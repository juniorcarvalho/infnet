"""Rotas HTTP da aplicacao (APIRouter)."""

import time

from fastapi import APIRouter, Depends, Response, status

import config
from models import HealthResponse, TranslateRequest, TranslateResponse
from services import Translator, get_service, is_model_loaded

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(response: Response) -> dict:
    loaded = is_model_loaded()
    if not loaded:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if loaded else "unavailable", "model": config.MODEL_NAME, "model_loaded": loaded}


# Endpoint sincrono (def): a inferencia roda em threadpool, sem bloquear o event loop.
@router.post("/translate", response_model=TranslateResponse)
def translate(
    request: TranslateRequest, service: Translator = Depends(get_service)
) -> dict:
    start = time.perf_counter()
    translated, n_chunks = service.translate(request.text)
    latency_ms = (time.perf_counter() - start) * 1000
    return {
        "source_text": request.text,
        "translated_text": translated,
        "source_lang": config.SOURCE_LANG,
        "target_lang": config.TARGET_LANG,
        "model": config.MODEL_NAME,
        "chunks": n_chunks,
        "latency_ms": round(latency_ms, 1),
    }
