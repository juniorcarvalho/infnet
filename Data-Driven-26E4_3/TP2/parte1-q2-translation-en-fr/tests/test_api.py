"""Testes da API usando um tradutor fake (nao baixa o modelo)."""

from fastapi.testclient import TestClient

from main import app
from services import ModelError, get_service


class FakeTranslator:
    def __init__(self, fail: bool = False):
        self.fail = fail

    def translate(self, text: str) -> tuple[str, int]:
        if self.fail:
            raise ModelError("boom")
        return f"[fr] {text}", 1


def make_client(fake) -> TestClient:
    app.dependency_overrides[get_service] = lambda: fake
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_health_model_not_loaded_returns_503():
    response = TestClient(app).get("/health")
    assert response.status_code == 503
    assert response.json()["model_loaded"] is False


def test_health_model_loaded(monkeypatch):
    monkeypatch.setattr("routers.is_model_loaded", lambda: True)
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model": "Helsinki-NLP/opus-mt-en-fr", "model_loaded": True}


def test_translate_ok():
    client = make_client(FakeTranslator())
    response = client.post("/translate", json={"text": " Hello "})
    assert response.status_code == 200
    body = response.json()
    assert body["source_text"] == "Hello"
    assert body["translated_text"] == "[fr] Hello"
    assert body["source_lang"] == "en"
    assert body["target_lang"] == "fr"
    assert body["chunks"] == 1


def test_translate_empty_rejected():
    client = make_client(FakeTranslator())
    assert client.post("/translate", json={"text": "  "}).status_code == 422
    assert client.post("/translate", json={}).status_code == 422


def test_translate_too_long_rejected():
    client = make_client(FakeTranslator())
    assert client.post("/translate", json={"text": "a" * 5001}).status_code == 422


def test_model_error_returns_503():
    client = make_client(FakeTranslator(fail=True))
    response = client.post("/translate", json={"text": "Hi"})
    assert response.status_code == 503
