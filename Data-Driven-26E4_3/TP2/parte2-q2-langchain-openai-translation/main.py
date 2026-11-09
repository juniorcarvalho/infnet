"""Ponto de entrada da aplicacao FastAPI (Parte 2 - Questao 2)."""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

import config
from routers import router
from services import ProviderError, get_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        get_service()
        logger.info("Chain de traducao pronta (modelo %s).", config.OPENAI_MODEL)
    except ProviderError as exc:
        logger.error("%s As chamadas a /translate responderao 503.", exc)
    yield


app = FastAPI(title=config.APP_TITLE, version="1.0.0", lifespan=lifespan)


@app.exception_handler(ProviderError)
async def provider_error_handler(_, exc: ProviderError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host=config.HOST, port=config.PORT)
