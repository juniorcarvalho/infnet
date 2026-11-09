"""Testes da API: o HuggingFacePipeline e trocado por um FakeListLLM (sem baixar modelo)."""

from fastapi.testclient import TestClient
from langchain_core.language_models.fake import FakeListLLM

from main import app
from services import ModelError, TranslationService, build_chain, get_service


def word_count(text: str) -> int:
    return len(text.split())


def make_client(responses: list[str]) -> TestClient:
    service = TranslationService(build_chain(FakeListLLM(responses=responses)), word_count, "fake")
    app.dependency_overrides[get_service] = lambda: service
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
    body = response.json()
    assert body["model"] == "Helsinki-NLP/opus-mt-en-de"
    assert body["framework"] == "langchain+huggingface"
    assert body["model_loaded"] is True


def test_translate_single_sentence():
    client = make_client(["Hallo, wie geht es dir?"])
    body = client.post("/translate", json={"text": "Hello, how are you?"}).json()
    assert body["translated_text"] == "Hallo, wie geht es dir?"
    assert body["target_lang"] == "de"
    assert body["chunks"] == 1


def test_translate_multiple_sentences_and_paragraphs():
    client = make_client(["Eins.", "Zwei.", "Drei."])
    body = client.post("/translate", json={"text": "One. Two.\n\nThree."}).json()
    assert body["chunks"] == 3
    assert body["translated_text"] == "Eins. Zwei.\n\nDrei."


def test_translate_empty_rejected():
    assert make_client(["x"]).post("/translate", json={"text": ""}).status_code == 422


def test_model_error_returns_503():
    class Failing:
        model_name = "fake"

        def translate(self, text):
            raise ModelError("boom")

    app.dependency_overrides[get_service] = lambda: Failing()
    assert TestClient(app).post("/translate", json={"text": "Hi"}).status_code == 503
