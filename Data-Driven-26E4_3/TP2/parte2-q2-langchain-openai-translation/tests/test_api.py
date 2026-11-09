"""Testes sem chamadas reais a OpenAI: o ChatOpenAI e trocado por um FakeListChatModel."""

import httpx
import openai
import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from main import app
import config
from services import TranslationService, build_chain, build_llm, build_prompt, get_service, map_openai_error


def make_client(responses: list[str]) -> TestClient:
    service = TranslationService(build_chain(FakeListChatModel(responses=responses)), "fake-chat")
    app.dependency_overrides[get_service] = lambda: service
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_prompt_contains_system_and_user_text():
    messages = build_prompt().format_messages(text="Hello")
    assert messages[0].type == "system" and "French" in messages[0].content
    assert messages[1].type == "human" and messages[1].content == "Hello"


def test_translate_ok():
    client = make_client(["  Bonjour, comment allez-vous ?  "])
    response = client.post("/translate", json={"text": "Hello, how are you?"})
    assert response.status_code == 200
    body = response.json()
    assert body["translated_text"] == "Bonjour, comment allez-vous ?"
    assert body["target_lang"] == "fr"
    assert body["model"] == "fake-chat"
    assert body["latency_ms"] >= 0


def test_translate_empty_rejected():
    client = make_client(["x"])
    assert client.post("/translate", json={"text": " "}).status_code == 422


def test_health():
    body = TestClient(app).get("/health").json()
    assert body["status"] == "ok"
    assert "api_key_configured" in body
    assert body["base_url"].startswith("http")


def _request() -> httpx.Request:
    return httpx.Request("POST", "https://api.openai.com/v1/chat/completions")


@pytest.mark.parametrize(
    ("exc", "status"),
    [
        (openai.RateLimitError("rl", response=httpx.Response(429, request=_request()), body=None), 429),
        (
            openai.RateLimitError(
                "quota",
                response=httpx.Response(429, request=_request()),
                body={"code": "credit_balance_exhausted", "type": "insufficient_quota"},
            ),
            503,
        ),
        (openai.AuthenticationError("auth", response=httpx.Response(401, request=_request()), body=None), 503),
        (openai.APITimeoutError(request=_request()), 504),
        (openai.APIConnectionError(request=_request()), 502),
        (RuntimeError("x"), 500),
    ],
)
def test_map_openai_error(exc, status):
    assert map_openai_error(exc).status_code == status


def test_provider_error_returned_as_json():
    class FailingService:
        model_name = "fake"

        async def translate(self, text):
            raise map_openai_error(
                openai.RateLimitError("rl", response=httpx.Response(429, request=_request()), body=None)
            )

    app.dependency_overrides[get_service] = lambda: FailingService()
    response = TestClient(app).post("/translate", json={"text": "Hi"})
    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"]


def test_llm_cache_is_bounded(monkeypatch):
    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-test")
    llm = build_llm()  # nao faz chamada de rede ao construir
    assert llm.cache._maxsize == config.CACHE_MAXSIZE


def test_llm_uses_configured_base_url(monkeypatch):
    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(config, "OPENAI_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setattr(config, "OPENAI_MODEL", "deepseek-flash")
    monkeypatch.setattr(config, "OPENAI_REASONING_EFFORT", "low")
    llm = build_llm()
    assert llm.openai_api_base == "https://api.deepseek.com"
    assert llm.model_name == "deepseek-flash"
    assert llm.reasoning_effort == "low"


def test_health_shows_base_url(monkeypatch):
    monkeypatch.setattr(config, "OPENAI_BASE_URL", "https://api.deepseek.com")
    assert TestClient(app).get("/health").json()["base_url"] == "https://api.deepseek.com"


def test_empty_translation_returns_502():
    client = make_client(["   "])
    response = client.post("/translate", json={"text": "Hello"})
    assert response.status_code == 502
    assert "vazia" in response.json()["detail"]


def test_cache_can_be_disabled(monkeypatch):
    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(config, "CACHE_MAXSIZE", 0)
    assert build_llm().cache is False
