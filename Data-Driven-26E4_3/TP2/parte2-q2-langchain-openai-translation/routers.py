"""Rotas HTTP da aplicacao (APIRouter)."""

import time

from fastapi import APIRouter, Depends

import config
from models import HealthResponse, TranslateRequest, TranslateResponse
from services import TranslationService, get_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> dict:
    return {
        "status": "ok",
        "model": config.OPENAI_MODEL,
        "api_key_configured": bool(config.OPENAI_API_KEY),
        "provider": config.LLM_PROVIDER,
        "base_url": config.OPENAI_BASE_URL or config.DEFAULT_BASE_URL,
    }


# Endpoint assincrono: a chamada de rede a OpenAI (I/O) e aguardada com
# "await" sem ocupar threads, permitindo muitas requisicoes concorrentes.
@router.post("/translate", response_model=TranslateResponse)
async def translate(
    request: TranslateRequest, service: TranslationService = Depends(get_service)
) -> dict:
    start = time.perf_counter()
    translated = await service.translate(request.text)
    latency_ms = (time.perf_counter() - start) * 1000
    return {
        "source_text": request.text,
        "translated_text": translated,
        "source_lang": config.SOURCE_LANG,
        "target_lang": config.TARGET_LANG,
        "model": service.model_name,
        "latency_ms": round(latency_ms, 1),
    }
