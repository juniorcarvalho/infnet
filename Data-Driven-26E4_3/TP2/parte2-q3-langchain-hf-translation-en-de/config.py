"""Configuracoes da aplicacao de traducao EN->DE (LangChain + HuggingFace)."""

import os

APP_TITLE = "TP2 - Parte 2 - Q3: Traducao EN->DE com LangChain + HuggingFace"
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8013"))

MODEL_NAME = os.getenv("MODEL_NAME", "Helsinki-NLP/opus-mt-en-de")
SOURCE_LANG = "en"
TARGET_LANG = "de"
FRAMEWORK = "langchain+huggingface"

MAX_INPUT_CHARS = 5000
MAX_CHUNK_TOKENS = 400
# False = uma frase por chunk (mais fiel: o Marian as vezes descarta frases
# quando recebe varias de uma vez).
GROUP_SENTENCES = False
MAX_NEW_TOKENS = 512
NUM_BEAMS = 4
BATCH_SIZE = 8

# Apos uma falha ao carregar o modelo, espera N segundos antes de tentar de novo.
LOAD_RETRY_SECONDS = float(os.getenv("LOAD_RETRY_SECONDS", "30"))
