"""Ponto de entrada da aplicacao FastAPI (Parte 2 - Questao 1)."""

import uvicorn
from fastapi import FastAPI

import config
from routers import router

app = FastAPI(title=config.APP_TITLE, version="1.0.0")
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host=config.HOST, port=config.PORT)
