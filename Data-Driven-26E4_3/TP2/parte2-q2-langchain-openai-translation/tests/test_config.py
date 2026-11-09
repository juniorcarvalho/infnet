"""Testes dos presets de provedor (OpenAI, DeepSeek) e das sobrescritas por variavel."""

import importlib

import dotenv
import pytest

import config
import services

VARS = [
    "LLM_PROVIDER", "OPENAI_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_MODEL",
    "OPENAI_BASE_URL", "OPENAI_REASONING_EFFORT", "OPENAI_THINKING",
]


@pytest.fixture
def load_config(monkeypatch):
    """Recarrega o config so com as variaveis informadas (sem ler o .env local)."""
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
    for var in VARS:
        monkeypatch.delenv(var, raising=False)

    def _load(**env):
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        return importlib.reload(config)

    yield _load
    monkeypatch.undo()
    importlib.reload(config)


def test_default_is_openai(load_config):
    cfg = load_config(OPENAI_API_KEY="sk-x")
    assert cfg.LLM_PROVIDER == "openai"
    assert cfg.OPENAI_BASE_URL is None and cfg.OPENAI_MODEL == "gpt-4o-mini"
    assert cfg.OPENAI_THINKING is None


def test_deepseek_preset(load_config):
    cfg = load_config(LLM_PROVIDER="deepseek", DEEPSEEK_API_KEY="ds-key", OPENAI_API_KEY="outra")
    assert cfg.OPENAI_BASE_URL == "https://api.deepseek.com"
    assert cfg.OPENAI_MODEL == "deepseek-flash"
    assert cfg.OPENAI_API_KEY == "ds-key"  # chave especifica tem prioridade
    assert cfg.OPENAI_THINKING == "disabled"

    llm = services.build_llm()
    assert llm.openai_api_base == "https://api.deepseek.com"
    assert llm.extra_body == {"thinking": {"type": "disabled"}}
    assert llm.temperature == 0


def test_deepseek_falls_back_to_openai_api_key(load_config):
    assert load_config(LLM_PROVIDER="deepseek", OPENAI_API_KEY="sk-x").OPENAI_API_KEY == "sk-x"


def test_env_overrides_preset(load_config):
    cfg = load_config(
        LLM_PROVIDER="deepseek", DEEPSEEK_API_KEY="k", OPENAI_MODEL="deepseek-v4-pro", OPENAI_THINKING="enabled"
    )
    assert cfg.OPENAI_MODEL == "deepseek-v4-pro" and cfg.OPENAI_THINKING == "enabled"


def test_invalid_provider(load_config):
    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        load_config(LLM_PROVIDER="xpto")


def test_provider_detected_from_base_url(load_config):
    # Configuracao do usuario: so URL, modelo e OPENAI_API_KEY, sem LLM_PROVIDER.
    cfg = load_config(
        OPENAI_API_KEY="sk-ds", OPENAI_BASE_URL="https://api.deepseek.com", OPENAI_MODEL="deepseek-flash"
    )
    assert cfg.LLM_PROVIDER == "deepseek"
    assert cfg.OPENAI_THINKING == "disabled"
    assert cfg.OPENAI_API_KEY == "sk-ds"
    assert load_config(OPENAI_BASE_URL="https://api.deepseek.com/v1/").LLM_PROVIDER == "deepseek"
    assert load_config(OPENAI_BASE_URL="http://localhost:11434/v1").LLM_PROVIDER == "openai"
