"""Configuracoes do chatbot com Fake LLM."""

import os

APP_TITLE = "TP2 - Parte 2 - Q1: Chatbot com Fake LLM (LangChain)"
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8011"))

MAX_MESSAGE_CHARS = 500
# Similaridade minima (0..1) para aceitar uma pergunta parecida com a cadastrada.
MATCH_CUTOFF = 0.6
