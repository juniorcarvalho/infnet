"""Rotas HTTP da aplicacao (APIRouter)."""

import time

from fastapi import APIRouter, Depends, Response, status

import config
from models import GenerateRequest, GenerateResponse, HealthResponse
from services import TextGenerator, get_service, is_model_loaded

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(response: Response) -> dict:
    loaded = is_model_loaded()
    if not loaded:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if loaded else "unavailable", "model": config.MODEL_NAME, "model_loaded": loaded}


# Endpoint sincrono (def): o FastAPI executa em threadpool, sem bloquear o event loop.
@router.post("/generate", response_model=GenerateResponse)
def generate(
    request: GenerateRequest, service: TextGenerator = Depends(get_service)
) -> dict:
    start = time.perf_counter()
    generations = service.generate(
        prompt=request.prompt,
        max_new_tokens=request.max_new_tokens,
        temperature=request.temperature,
        top_k=request.top_k,
        num_return_sequences=request.num_return_sequences,
        seed=request.seed,
    )
    latency_ms = (time.perf_counter() - start) * 1000
    return {
        "prompt": request.prompt,
        "generations": generations,
        "model": config.MODEL_NAME,
        "latency_ms": round(latency_ms, 1),
    }
