"""Configuracoes da aplicacao de geracao de texto com GPT-2."""

import os

APP_TITLE = "TP2 - Parte 1 - Q1: Geracao de texto com GPT-2"
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8001"))

MODEL_NAME = os.getenv("MODEL_NAME", "gpt2")

# Limites de entrada/saida
MAX_PROMPT_CHARS = 1000
MAX_NEW_TOKENS_LIMIT = 200
MAX_RETURN_SEQUENCES = 3

# Parametros de geracao padrao
DEFAULT_MAX_NEW_TOKENS = 50
DEFAULT_TEMPERATURE = 0.9
DEFAULT_TOP_K = 50
MAX_TOP_K = 1000
TOP_P = 0.95
NO_REPEAT_NGRAM_SIZE = 3

# Apos uma falha ao carregar o modelo, espera N segundos antes de tentar de novo.
LOAD_RETRY_SECONDS = float(os.getenv("LOAD_RETRY_SECONDS", "30"))
