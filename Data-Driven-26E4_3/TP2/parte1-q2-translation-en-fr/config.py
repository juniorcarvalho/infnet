"""Configuracoes da aplicacao de traducao EN->FR."""

import os

APP_TITLE = "TP2 - Parte 1 - Q2: Traducao EN->FR (Helsinki-NLP/opus-mt-en-fr)"
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8002"))

MODEL_NAME = os.getenv("MODEL_NAME", "Helsinki-NLP/opus-mt-en-fr")
SOURCE_LANG = "en"
TARGET_LANG = "fr"

MAX_INPUT_CHARS = 5000
# Limite de tokens por chunk (o modelo aceita ate 512).
MAX_CHUNK_TOKENS = 400
# False = uma frase por chunk (mais fiel: o Marian as vezes descarta frases
# quando recebe varias de uma vez). True = agrupa frases ate MAX_CHUNK_TOKENS.
GROUP_SENTENCES = False
MAX_NEW_TOKENS = 512
NUM_BEAMS = 4
BATCH_SIZE = 8

# Apos uma falha ao carregar o modelo, espera N segundos antes de tentar de novo.
LOAD_RETRY_SECONDS = float(os.getenv("LOAD_RETRY_SECONDS", "30"))
