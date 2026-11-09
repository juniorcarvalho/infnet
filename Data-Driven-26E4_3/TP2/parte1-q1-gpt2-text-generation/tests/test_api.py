"""Testes da API usando um gerador fake (nao baixa o GPT-2)."""

from fastapi.testclient import TestClient

from main import app
from services import ModelError, get_service


class FakeGenerator:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.calls = []

    def generate(self, prompt, max_new_tokens, temperature, top_k, num_return_sequences, seed):
        self.calls.append((prompt, max_new_tokens, temperature, top_k, num_return_sequences, seed))
        if self.fail:
            raise ModelError("boom")
        return [
            {"generated_text": f"{prompt} continuacao {i}", "continuation": f"continuacao {i}"}
            for i in range(num_return_sequences)
        ]


def make_client(fake: FakeGenerator) -> TestClient:
    app.dependency_overrides[get_service] = lambda: fake
    # Sem "with": o lifespan nao roda, entao o modelo real nao e carregado.
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_health_model_not_loaded_returns_503():
    # Sem lifespan o modelo nao e carregado: o health deve refletir isso.
    response = TestClient(app).get("/health")
    assert response.status_code == 503
    assert response.json()["model_loaded"] is False


def test_health_model_loaded(monkeypatch):
    monkeypatch.setattr("routers.is_model_loaded", lambda: True)
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model": "gpt2", "model_loaded": True}


def test_generate_ok():
    fake = FakeGenerator()
    client = make_client(fake)
    response = client.post("/generate", json={"prompt": "  Hello world  ", "num_return_sequences": 2})
    assert response.status_code == 200
    body = response.json()
    assert body["prompt"] == "Hello world"
    assert len(body["generations"]) == 2
    assert body["generations"][0]["continuation"] == "continuacao 0"
    assert body["model"] == "gpt2"
    assert fake.calls[0][0] == "Hello world"
    assert fake.calls[0][3] == 50  # top_k padrao


def test_generate_custom_top_k():
    fake = FakeGenerator()
    client = make_client(fake)
    assert client.post("/generate", json={"prompt": "Hi", "top_k": 10}).status_code == 200
    assert fake.calls[0][3] == 10
    assert client.post("/generate", json={"prompt": "Hi", "top_k": 0}).status_code == 422


def test_generate_empty_prompt_rejected():
    client = make_client(FakeGenerator())
    response = client.post("/generate", json={"prompt": "   "})
    assert response.status_code == 422


def test_generate_invalid_params_rejected():
    client = make_client(FakeGenerator())
    response = client.post("/generate", json={"prompt": "Hi", "max_new_tokens": 1000})
    assert response.status_code == 422


def test_model_error_returns_503():
    client = make_client(FakeGenerator(fail=True))
    response = client.post("/generate", json={"prompt": "Hi"})
    assert response.status_code == 503
    assert "boom" in response.json()["detail"]
