"""Configuracoes da aplicacao de traducao EN->FR via OpenAI + LangChain.

Funciona com qualquer API compativel com a da OpenAI. Ha presets para OpenAI e
DeepSeek (LLM_PROVIDER); outros provedores (OpenRouter, Ollama, vLLM...) usam
OPENAI_BASE_URL, OPENAI_API_KEY e OPENAI_MODEL.
"""

import os

from dotenv import load_dotenv

load_dotenv()

APP_TITLE = "TP2 - Parte 2 - Q2: Traducao EN->FR com OpenAI via LangChain"
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8012"))

# Presets de provedores com API compativel com a da OpenAI. Cada valor pode ser
# sobrescrito pelas variaveis OPENAI_* correspondentes.
PROVIDERS: dict[str, dict[str, str | None]] = {
    "openai": {
        "base_url": None,  # SDK usa https://api.openai.com/v1
        "model": "gpt-4o-mini",
        "key_env": "OPENAI_API_KEY",
        "reasoning_effort": None,
        "thinking": None,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-flash",
        "key_env": "DEEPSEEK_API_KEY",
        "reasoning_effort": None,
        # No DeepSeek o modo de raciocinio vem ligado (esforco high) e ignora temperature;
        # para traducao ele so acrescenta latencia e custo.
        "thinking": "disabled",
    },
}


def _env(name: str) -> str | None:
    return os.getenv(name, "").strip() or None


def _detect_provider(base_url: str | None) -> str:
    """Sem LLM_PROVIDER, deduz o preset pela OPENAI_BASE_URL (ex.: api.deepseek.com -> deepseek)."""
    if base_url:
        for name, preset in PROVIDERS.items():
            if preset["base_url"] and base_url.rstrip("/").startswith(str(preset["base_url"]).rstrip("/").removesuffix("/v1")):
                return name
    return "openai"


LLM_PROVIDER = (_env("LLM_PROVIDER") or _detect_provider(_env("OPENAI_BASE_URL"))).lower()
if LLM_PROVIDER not in PROVIDERS:
    raise ValueError(f"LLM_PROVIDER invalido: {LLM_PROVIDER!r}. Opcoes: {', '.join(PROVIDERS)}")
_preset = PROVIDERS[LLM_PROVIDER]

# Chave: primeiro a especifica do provedor (ex.: DEEPSEEK_API_KEY), depois OPENAI_API_KEY.
OPENAI_API_KEY = _env(str(_preset["key_env"])) or _env("OPENAI_API_KEY") or ""
OPENAI_MODEL = _env("OPENAI_MODEL") or str(_preset["model"])
# None = API oficial da OpenAI.
OPENAI_BASE_URL = _env("OPENAI_BASE_URL") or _preset["base_url"]
DEFAULT_BASE_URL = "https://api.openai.com/v1"
# Modelos de raciocinio da OpenAI (serie o): low | medium | high.
OPENAI_REASONING_EFFORT = _env("OPENAI_REASONING_EFFORT") or _preset["reasoning_effort"]
# DeepSeek: "enabled" | "disabled" (enviado como {"thinking": {"type": ...}}).
OPENAI_THINKING = _env("OPENAI_THINKING") or _preset["thinking"]
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "30"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "2"))
# Limite de entradas do cache em memoria (evita crescimento ilimitado da RAM). 0 = sem cache.
CACHE_MAXSIZE = int(os.getenv("CACHE_MAXSIZE", "1000"))

SOURCE_LANG = "en"
TARGET_LANG = "fr"
MAX_INPUT_CHARS = 5000

SYSTEM_PROMPT = (
    "You are a professional translator. Translate the user's English text to French. "
    "Return only the translation, preserving the original formatting and line breaks. "
    "Do not add explanations."
)
