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
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek")
    monkeypatch.delenv("AI_PROVIDER", raising=False)   # full chain by default
    # Never let a test reach the network through the OpenAI-compatible path.
    monkeypatch.setattr(interpreter.httpx, "post",
                        lambda url, **k: (_ for _ in ()).throw(
                            interpreter.httpx.ConnectError("no network in tests")))


# ── Claude SDK double ────────────────────────────────────────────────

class _Block:
    def __init__(self, text, type="text"):
        self.type, self.text = type, text


class _Response:
    def __init__(self, text, stop_reason="end_turn"):
        self.content = [_Block("", "thinking"), _Block(text)]
        self.stop_reason = stop_reason
        self.stop_details = None


def mock_claude(monkeypatch, reply):
    """`reply` is a text, or a callable(kwargs) -> text / raising."""
    seen = []

    class _Messages:
        def create(self, **kwargs):
            seen.append(kwargs)
            out = reply(kwargs) if callable(reply) else reply
            return out if isinstance(out, _Response) else _Response(out)

    class _Beta:
        messages = _Messages()

    class FakeAnthropic:
        def __init__(self, *a, **k):
            self.beta = _Beta()

    monkeypatch.setattr(interpreter.anthropic, "Anthropic", FakeAnthropic)
    return seen


def _mock_response(payload: dict):
    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    return Resp()


def _chat_payload(text: str):
    # OpenAI-compatible shape (DeepSeek uses the same)
    return {"choices": [{"message": {"content": text}}]}


# ── Provider chain ───────────────────────────────────────────────────

def test_claude_is_primary_and_uses_sdk_with_fallbacks(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-5-5")
    seen = mock_claude(monkeypatch, "```json\n" + json.dumps(VALID_BRIEF) + "\n```")
    brief, provider = interpreter.interpret("a steel ring")
    assert provider == "anthropic"
    assert brief["sculpture"]["family"] == "open_ring"
    call = seen[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["system"].startswith("You are the design interpreter")
    assert call["messages"] == [{"role": "user", "content": "a steel ring"}]
    assert call["fallbacks"] == "default"
    assert call["betas"] == ["server-side-fallback-2026-07-01"]


def test_ai_provider_env_pins_chain_to_claude(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    mock_claude(monkeypatch, lambda k: (_ for _ in ()).throw(
        interpreter.anthropic.APIConnectionError(request=None)))
    with pytest.raises(interpreter.AIFailure) as e:
        interpreter.interpret("a steel ring")
    assert "openai" not in str(e.value) and "deepseek" not in str(e.value)


def test_openai_used_when_claude_down(monkeypatch):
    mock_claude(monkeypatch, lambda k: (_ for _ in ()).throw(
        interpreter.anthropic.APIConnectionError(request=None)))

    def fake_post(url, **k):
        if "openai.com" not in url:
            raise interpreter.httpx.ConnectError("down")
        return _mock_response(_chat_payload(json.dumps(VALID_BRIEF)))

    monkeypatch.setattr(interpreter.httpx, "post", fake_post)
    brief, provider = interpreter.interpret("a steel ring")
    assert provider == "openai"


def test_deepseek_is_last_resort(monkeypatch):
    mock_claude(monkeypatch, lambda k: (_ for _ in ()).throw(
        interpreter.anthropic.APIConnectionError(request=None)))

    def fake_post(url, **k):
        if "deepseek" not in url:
            raise interpreter.httpx.ConnectError("down")
        return _mock_response(_chat_payload(json.dumps(VALID_BRIEF)))

    monkeypatch.setattr(interpreter.httpx, "post", fake_post)
    brief, provider = interpreter.interpret("a steel ring")
    assert provider == "deepseek"


def test_retry_on_invalid_json_then_success(monkeypatch):
    calls = {"n": 0}

    def reply(kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return "not json at all"
        assert "previous answer was invalid" in kwargs["messages"][0]["content"]
        return json.dumps(VALID_BRIEF)

    mock_claude(monkeypatch, reply)
    brief, provider = interpreter.interpret("a steel ring")
    assert provider == "anthropic"
    assert calls["n"] == 2


def test_claude_refusal_is_reported_not_retried(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    seen = mock_claude(monkeypatch, lambda k: _Response("", stop_reason="refusal"))
    with pytest.raises(interpreter.AIFailure) as e:
        interpreter.interpret("something")
    assert "refused" in str(e.value)
    assert len(seen) == 1


def test_unimplemented_family_rejected(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    bad = json.loads(json.dumps(VALID_BRIEF))
    bad["sculpture"]["family"] = "voronoi_shell"  # in schema, not implemented
    mock_claude(monkeypatch, json.dumps(bad))
    with pytest.raises(interpreter.AIFailure):
        interpreter.interpret("a voronoi thing")


def test_no_keys_raises_unavailable(monkeypatch):
    for k in ("DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(interpreter.AIUnavailable):
        interpreter.interpret("anything")


def test_unknown_provider_name_is_an_error(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    with pytest.raises(interpreter.AIFailure):
        interpreter.interpret("anything")


def test_api_interpret_happy_path(monkeypatch):
    mock_claude(monkeypatch, json.dumps(VALID_BRIEF))
    resp = client.post("/api/ai/interpret", json={"prompt": "a steel ring"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "anthropic"
    assert body["brief"]["sculpture"]["family"] == "open_ring"


def test_api_interpret_empty_prompt():
    resp = client.post("/api/ai/interpret", json={"prompt": "   "})
    assert resp.status_code == 422


# ── Refinement / echo / diff (conversation, not one-shot) ─────────────

def test_refine_applies_instruction_and_reports_changes(monkeypatch):
    updated = json.loads(json.dumps(VALID_BRIEF))
    updated["sculpture"]["material"] = "bronze"
    updated["sculpture"]["finish"] = "patina"
    seen = mock_claude(monkeypatch, json.dumps(updated))
    brief, provider = interpreter.refine(VALID_BRIEF, "make it bronze with a patina")
    assert provider == "anthropic"
    assert brief["sculpture"]["material"] == "bronze"
    # The model saw refinement mode + the current brief + the instruction.
    assert "REFINEMENT MODE" in seen[0]["system"]
    user = seen[0]["messages"][0]["content"]
    assert "make it bronze" in user and '"open_ring"' in user
    changes = interpreter.diff_briefs(VALID_BRIEF, brief)
    assert {c["path"]: (c["before"], c["after"]) for c in changes} == {
        "sculpture.material": ("stainless_316l", "bronze"),
        "sculpture.finish": ("mirror_polish_8", "patina"),
    }


def test_refine_retries_on_invalid_output(monkeypatch):
    calls = {"n": 0}

    def reply(kwargs):
        calls["n"] += 1
        return "{not valid" if calls["n"] == 1 else json.dumps(VALID_BRIEF)

    mock_claude(monkeypatch, reply)
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
    mock_claude(monkeypatch, json.dumps(updated))
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
