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
