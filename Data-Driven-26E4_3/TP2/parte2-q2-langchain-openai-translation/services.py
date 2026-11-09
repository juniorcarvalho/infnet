"""Chain LangChain (prompt | ChatOpenAI | parser) para traducao EN->FR."""

import logging
from functools import lru_cache
from typing import Any

import openai
from fastapi import status
from langchain_core.caches import InMemoryCache
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

import config

logger = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    """Erro ao chamar o provedor de LLM, com o status HTTP a devolver."""

    def __init__(self, message: str, status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(message)
        self.status_code = status_code


def build_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [("system", config.SYSTEM_PROMPT), ("human", "{text}")]
    )


def build_llm() -> Any:
    if not config.OPENAI_API_KEY:
        raise ProviderError(
            f"Chave de API não configurada para o provedor '{config.LLM_PROVIDER}' "
            "(OPENAI_API_KEY ou a chave específica, ex.: DEEPSEEK_API_KEY). "
            "Crie o arquivo .env a partir de .env.example.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    optional: dict[str, Any] = {}
    if config.OPENAI_REASONING_EFFORT:
        optional["reasoning_effort"] = config.OPENAI_REASONING_EFFORT
    if config.OPENAI_THINKING:
        # Parametro proprio do DeepSeek, fora do padrao OpenAI: vai no corpo da requisicao.
        optional["extra_body"] = {"thinking": {"type": config.OPENAI_THINKING}}
    return ChatOpenAI(
        model=config.OPENAI_MODEL,
        api_key=config.OPENAI_API_KEY,
        # None = api.openai.com; outra URL = provedor compativel (DeepSeek, OpenRouter, Ollama...).
        base_url=config.OPENAI_BASE_URL,
        temperature=0,  # traducao deterministica
        timeout=config.OPENAI_TIMEOUT,
        max_retries=config.OPENAI_MAX_RETRIES,
        # Cache em memoria (LRU limitado): textos repetidos retornam sem nova chamada a API.
        # False desliga o cache (ex.: para medir a latencia real do provedor).
        cache=InMemoryCache(maxsize=config.CACHE_MAXSIZE) if config.CACHE_MAXSIZE > 0 else False,
        **optional,
    )


def build_chain(llm: Any) -> Runnable:
    return build_prompt() | llm | StrOutputParser()


QUOTA_ERROR_CODES = {"insufficient_quota", "credit_balance_exhausted"}


def _is_quota_error(exc: Exception) -> bool:
    """True se o 429 e de conta sem creditos (e nao de rate limit temporario)."""
    body = getattr(exc, "body", None)
    if not isinstance(body, dict):
        return False
    return bool(QUOTA_ERROR_CODES & {body.get("code"), body.get("type")})


def map_openai_error(exc: Exception) -> ProviderError:
    """Converte excecoes do SDK da OpenAI em erros HTTP adequados."""
    if isinstance(exc, openai.RateLimitError) and _is_quota_error(exc):
        # A OpenAI tambem usa 429 para conta sem creditos; repetir nao resolve.
        return ProviderError(
            "Conta do provedor sem créditos (insufficient_quota). Adicione créditos à conta da API.",
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    if isinstance(exc, openai.RateLimitError):
        return ProviderError(
            "Limite de uso do provedor atingido (rate limit). Tente novamente.", status.HTTP_429_TOO_MANY_REQUESTS
        )
    if isinstance(exc, openai.AuthenticationError):
        return ProviderError(
            f"Falha de autenticação no provedor '{config.LLM_PROVIDER}'. Verifique a chave de API e a OPENAI_BASE_URL.", status.HTTP_503_SERVICE_UNAVAILABLE
        )
    if isinstance(exc, openai.APITimeoutError):
        return ProviderError("Timeout ao chamar o provedor.", status.HTTP_504_GATEWAY_TIMEOUT)
    if isinstance(exc, openai.APIConnectionError):
        return ProviderError("Não foi possível conectar ao provedor (verifique OPENAI_BASE_URL).", status.HTTP_502_BAD_GATEWAY)
    if isinstance(exc, openai.APIStatusError):
        return ProviderError(f"Erro do provedor (HTTP {exc.status_code}).", status.HTTP_502_BAD_GATEWAY)
    logger.exception("Erro inesperado ao traduzir")
    return ProviderError(f"Erro inesperado ao traduzir: {exc}", status.HTTP_500_INTERNAL_SERVER_ERROR)


class TranslationService:
    def __init__(self, chain: Runnable, model_name: str):
        self.chain = chain
        self.model_name = model_name

    async def translate(self, text: str) -> str:
        try:
            result = await self.chain.ainvoke({"text": text})
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise map_openai_error(exc) from exc
        translated = result.strip()
        if not translated:
            # Ex.: modelo de raciocinio que gastou todo o limite de saida "pensando"
            # (finish_reason=length) e nao devolveu texto.
            raise ProviderError(
                "O provedor devolveu uma tradução vazia. Em modelos de raciocínio, desligue ou reduza "
                "o raciocínio (OPENAI_THINKING=disabled ou OPENAI_REASONING_EFFORT=low).",
                status.HTTP_502_BAD_GATEWAY,
            )
        return translated


@lru_cache(maxsize=1)
def _default_service() -> TranslationService:
    # Singleton: cliente HTTP e conexoes reaproveitados entre requisicoes.
    return TranslationService(build_chain(build_llm()), config.OPENAI_MODEL)


def get_service() -> TranslationService:
    """Dependencia FastAPI."""
    return _default_service()
