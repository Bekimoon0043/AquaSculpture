import json

import pytest
from fastapi.testclient import TestClient

from ai import interpreter
from main import app

client = TestClient(app)

VALID_BRIEF = {
    "project": {"name": "Test", "site": "garden", "budget_usd": 100000},
    "sculpture": {
        "family": "open_ring", "height_m": 3.0,
        "material": "stainless_316l", "finish": "mirror_polish_8",
        "parameters": {"diameter_m": 3.0, "opening_deg": 90},
        "style_notes": "minimal",
    },
    "water": {
        "features": [{"type": "still_basin"}],
        "basin": {"shape": "circular", "diameter_m": 5, "depth_m": 0.4,
                  "material": "black_granite", "overflow": "perimeter_weir"},
    },
    "lighting": {"sculpture_uplights": 2},
    "constraints": {"wind_zone": "moderate", "indoor": False, "public_access": True},
}


@pytest.fixture(autouse=True)
def keys(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")


def _mock_response(payload: dict):
    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    return Resp()


def _anthropic_payload(text: str):
    return {"content": [{"text": text}]}


def _chat_payload(text: str):
    # OpenAI-compatible shape (DeepSeek uses the same)
    return {"choices": [{"message": {"content": text}}]}


def test_deepseek_success(monkeypatch):
    monkeypatch.setattr(interpreter.httpx, "post",
                        lambda url, **k: _mock_response(
                            _chat_payload("```json\n" + json.dumps(VALID_BRIEF) + "\n```")))
    brief, provider = interpreter.interpret("a steel ring")
    assert provider == "deepseek"
    assert brief["sculpture"]["family"] == "open_ring"


def test_anthropic_used_when_deepseek_down(monkeypatch):
    def fake_post(url, **k):
        if "deepseek" in url:
            raise interpreter.httpx.ConnectError("down")
        return _mock_response(_anthropic_payload(json.dumps(VALID_BRIEF)))

    monkeypatch.setattr(interpreter.httpx, "post", fake_post)
    brief, provider = interpreter.interpret("a steel ring")
    assert provider == "anthropic"


def test_retry_on_invalid_json_then_success(monkeypatch):
    calls = {"n": 0}

    def fake_post(url, **k):
        calls["n"] += 1
        text = "not json at all" if calls["n"] == 1 else json.dumps(VALID_BRIEF)
        return _mock_response(_chat_payload(text))

    monkeypatch.setattr(interpreter.httpx, "post", fake_post)
    brief, provider = interpreter.interpret("a steel ring")
    assert provider == "deepseek"
    assert calls["n"] == 2


def test_fallback_to_openai_when_others_down(monkeypatch):
    def fake_post(url, **k):
        if "openai.com" not in url:
            raise interpreter.httpx.ConnectError("down")
        return _mock_response(_chat_payload(json.dumps(VALID_BRIEF)))

    monkeypatch.setattr(interpreter.httpx, "post", fake_post)
    brief, provider = interpreter.interpret("a steel ring")
    assert provider == "openai"


def test_unimplemented_family_rejected(monkeypatch):
    bad = json.loads(json.dumps(VALID_BRIEF))
    bad["sculpture"]["family"] = "voronoi_shell"  # in schema, not implemented
    monkeypatch.setattr(interpreter.httpx, "post",
                        lambda url, **k: _mock_response(
                            _chat_payload(json.dumps(bad))))
    with pytest.raises(interpreter.AIFailure):
        interpreter.interpret("a voronoi thing")


def test_no_keys_raises_unavailable(monkeypatch):
    for k in ("DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(interpreter.AIUnavailable):
        interpreter.interpret("anything")


def test_api_interpret_happy_path(monkeypatch):
    monkeypatch.setattr(interpreter.httpx, "post",
                        lambda url, **k: _mock_response(
                            _chat_payload(json.dumps(VALID_BRIEF))))
    resp = client.post("/api/ai/interpret", json={"prompt": "a steel ring"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "deepseek"
    assert body["brief"]["sculpture"]["family"] == "open_ring"


def test_api_interpret_empty_prompt():
    resp = client.post("/api/ai/interpret", json={"prompt": "   "})
    assert resp.status_code == 422


# ── Refinement / echo / diff (conversation, not one-shot) ─────────────

def test_refine_applies_instruction_and_reports_changes(monkeypatch):
    updated = json.loads(json.dumps(VALID_BRIEF))
    updated["sculpture"]["material"] = "bronze"
    updated["sculpture"]["finish"] = "patina"
    seen = {}

    def fake_post(url, **k):
        seen["messages"] = k["json"]["messages"]
        return _mock_response(_chat_payload(json.dumps(updated)))

    monkeypatch.setattr(interpreter.httpx, "post", fake_post)
    brief, provider = interpreter.refine(VALID_BRIEF, "make it bronze with a patina")
    assert provider == "deepseek"
    assert brief["sculpture"]["material"] == "bronze"
    # The model saw refinement mode + the current brief + the instruction.
    assert "REFINEMENT MODE" in seen["messages"][0]["content"]
    assert "make it bronze" in seen["messages"][1]["content"]
    assert '"open_ring"' in seen["messages"][1]["content"]
    changes = interpreter.diff_briefs(VALID_BRIEF, brief)
    assert {c["path"]: (c["before"], c["after"]) for c in changes} == {
        "sculpture.material": ("stainless_316l", "bronze"),
        "sculpture.finish": ("mirror_polish_8", "patina"),
    }


def test_refine_retries_on_invalid_output(monkeypatch):
    calls = {"n": 0}

    def fake_post(url, **k):
        calls["n"] += 1
        text = "{not valid" if calls["n"] == 1 else json.dumps(VALID_BRIEF)
        return _mock_response(_chat_payload(text))

    monkeypatch.setattr(interpreter.httpx, "post", fake_post)
    brief, _ = interpreter.refine(VALID_BRIEF, "no change")
    assert calls["n"] == 2 and brief["sculpture"]["family"] == "open_ring"


def test_describe_brief_reads_like_the_design():
    text = interpreter.describe_brief(VALID_BRIEF)
    assert "3 m open_ring in stainless_316l (mirror_polish_8)" in text
    assert "5 m circular black_granite basin" in text
    assert "still water" in text
    assert "2 uplights" in text
    assert "outdoor, moderate wind, public access" in text
    assert "budget $100,000" in text


def test_describe_brief_dry_piece_without_ai():
    dry = {"sculpture": {"family": "ribbon_knot", "height_m": 5, "material": "bronze"},
           "water": {"features": []}, "lighting": {}, "constraints": {"indoor": True}}
    text = interpreter.describe_brief(dry)
    assert "5 m ribbon_knot in bronze" in text
    assert "dry (no basin)" in text and "unlit" in text and "indoor" in text


def test_diff_briefs_handles_nested_lists_and_additions():
    a = {"water": {"features": [{"type": "still_basin"}]}, "lighting": {}}
    b = {"water": {"features": [{"type": "bubbler_field", "count": 12},
                                {"type": "rain_curtain"}]},
         "lighting": {"submersible_rgb": 12}}
    paths = {c["path"]: c for c in interpreter.diff_briefs(a, b)}
    assert paths["water.features.0.type"]["after"] == "bubbler_field"
    assert paths["water.features.0.count"]["before"] is None
    assert paths["water.features.1"]["after"] == {"type": "rain_curtain"}
    assert paths["lighting.submersible_rgb"] == {
        "path": "lighting.submersible_rgb", "before": None, "after": 12}
    assert interpreter.diff_briefs(a, a) == []


def test_api_refine_and_interpret_return_summary(monkeypatch):
    updated = json.loads(json.dumps(VALID_BRIEF))
    updated["sculpture"]["height_m"] = 3.6
    monkeypatch.setattr(interpreter.httpx, "post",
                        lambda url, **k: _mock_response(
                            _chat_payload(json.dumps(updated))))
    resp = client.post("/api/ai/refine",
                       json={"brief": VALID_BRIEF, "instruction": "20% taller"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["brief"]["sculpture"]["height_m"] == 3.6
    assert body["changes"] == [{"path": "sculpture.height_m", "before": 3.0, "after": 3.6}]
    assert body["summary"].startswith("3.6 m open_ring")
    assert client.post("/api/ai/interpret", json={"prompt": "ring"}).json()["summary"]
    assert client.post("/api/ai/refine",
                       json={"brief": VALID_BRIEF, "instruction": " "}).status_code == 422
