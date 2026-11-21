"""Configurações carregadas do .env."""
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

from exceptions import ConfigError

load_dotenv()


@dataclass(frozen=True)
class Settings:
    groq_api_key: str = field(repr=False)
    model_name: str
    base_url: str
    temperature: float
    http_timeout: float

    def require_api_key(self) -> str:
        """Verificação preguiçosa: só ao construir o LLM."""
        if not self.groq_api_key:
            raise ConfigError(
                "GROQ_API_KEY não definida. Copie .env.example para .env e preencha a chave."
            )
        return self.groq_api_key


def get_settings() -> Settings:
    try:
        temperature = float(os.environ.get("LLM_TEMPERATURE", "0"))
        http_timeout = float(os.environ.get("HTTP_TIMEOUT", "10"))
    except ValueError as e:
        raise ConfigError(f"LLM_TEMPERATURE/HTTP_TIMEOUT devem ser numéricos: {e}") from e
    return Settings(
        groq_api_key=os.environ.get("GROQ_API_KEY", ""),
        model_name=os.environ.get("MODEL_NAME", "openai/gpt-oss-20b"),
        base_url=os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        temperature=temperature,
        http_timeout=http_timeout,
    )
