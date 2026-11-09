"""Testes do chatbot: Fake LLM customizado, troca do LLM e API."""

from fastapi.testclient import TestClient
from langchain_core.language_models.fake import FakeListLLM

from faq import FALLBACK_ANSWER, PREDEFINED_QA
from main import app
from services import ChatService, PredefinedFakeLLM, build_chain, find_answer, get_service, normalize

client = TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_normalize_removes_accents_and_punctuation():
    assert normalize("  O que é   LangChain?! ") == "o que e langchain"


def test_find_answer_exact_and_fuzzy():
    assert find_answer("Olá!") == (PREDEFINED_QA["ola"], True)
    # Erro de digitacao ainda e reconhecido.
    assert find_answer("o que e langchan")[1] is True
    assert find_answer("qual a capital da mongolia") == (FALLBACK_ANSWER, False)


def test_predefined_fake_llm_in_chain():
    chain = build_chain(PredefinedFakeLLM())
    assert chain.invoke({"question": "Qual seu nome?"}) == PREDEFINED_QA["qual seu nome"]


def test_chain_accepts_langchain_fake_list_llm():
    # O mesmo prompt/parser funciona com o FakeListLLM oficial do LangChain.
    chain = build_chain(FakeListLLM(responses=["resposta 1", "resposta 2"]))
    assert chain.invoke({"question": "qualquer"}) == "resposta 1"
    assert chain.invoke({"question": "qualquer"}) == "resposta 2"


def test_chat_endpoint_known_question():
    response = client.post("/chat", json={"message": "O que é FastAPI?"})
    assert response.status_code == 200
    body = response.json()
    assert body["matched"] is True
    assert body["response"] == PREDEFINED_QA["o que e fastapi"]
    assert body["llm"] == "fake"


def test_chat_endpoint_unknown_question():
    body = client.post("/chat", json={"message": "Quanto e 2+2?"}).json()
    assert body["matched"] is False
    assert body["response"] == FALLBACK_ANSWER


def test_chat_with_overridden_llm():
    service = ChatService(llm=FakeListLLM(responses=["simulado"]))
    app.dependency_overrides[get_service] = lambda: service
    body = client.post("/chat", json={"message": "O que é FastAPI?"}).json()
    assert body["response"] == "simulado"
    # A resposta nao veio do FAQ, entao matched nao se aplica.
    assert body["matched"] is None


def test_chat_empty_message_rejected():
    assert client.post("/chat", json={"message": "   "}).status_code == 422


def test_questions_endpoint():
    body = client.get("/questions").json()
    assert "o que e langchain" in body["questions"]
