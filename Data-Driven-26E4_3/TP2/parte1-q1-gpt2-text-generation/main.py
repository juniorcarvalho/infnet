"""Ponto de entrada da aplicacao FastAPI (Parte 1 - Questao 1)."""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

import config
from routers import router
from services import ModelError, get_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Carrega o modelo na inicializacao para a primeira requisicao nao pagar o custo.
    try:
        get_service()
    except ModelError:
        # Ja registrado pelo ModelLoader; /health indicara model_loaded=false.
        pass
    yield


app = FastAPI(title=config.APP_TITLE, version="1.0.0", lifespan=lifespan)


@app.exception_handler(ModelError)
async def model_error_handler(_, exc: ModelError):
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": str(exc)})


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host=config.HOST, port=config.PORT)
