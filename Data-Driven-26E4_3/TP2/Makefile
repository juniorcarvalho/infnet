# TP2: APIs com FastAPI e LangChain usando LLMs
#
# Uso: make            -> mostra a ajuda
#      make <alvo>     -> executa o alvo
#
# Variáveis:
#   RELOAD=1   roda com "uvicorn --reload" (recarga automática ao editar o código)
#   HOST=...   endereço de escuta (padrão: 127.0.0.1)
#   PYTHON=... interpretador (padrão: .venv/bin/python, se existir; senão python3)

.DEFAULT_GOAL := help
SHELL := /bin/bash

VENV    := .venv
PYTHON  ?= $(if $(wildcard $(VENV)/bin/python),$(abspath $(VENV)/bin/python),python3)
HOST    ?= 127.0.0.1
RELOAD  ?= 0

P1Q1 := parte1-q1-gpt2-text-generation
P1Q2 := parte1-q2-translation-en-fr
P2Q1 := parte2-q1-fake-llm-chatbot
P2Q2 := parte2-q2-langchain-openai-translation
P2Q3 := parte2-q3-langchain-hf-translation-en-de
APPS := $(P1Q1) $(P1Q2) $(P2Q1) $(P2Q2) $(P2Q3)

# run_app(pasta, porta): roda a app com "python main.py" ou, com RELOAD=1, "uvicorn --reload"
define run_app
	@echo ">> $(1) em http://$(HOST):$(2)/docs"
	@if [ "$(RELOAD)" = "1" ]; then \
		cd $(1) && HOST=$(HOST) PORT=$(2) $(PYTHON) -m uvicorn main:app --host $(HOST) --port $(2) --reload; \
	else \
		cd $(1) && HOST=$(HOST) PORT=$(2) $(PYTHON) main.py; \
	fi
endef

.PHONY: help install p1q1 p1q2 p2q1 p2q2 p2q3 run-all test benchmark clean check-env-p2q2

help: ## Mostra esta ajuda
	@echo "TP2: APIs com FastAPI e LangChain"
	@echo
	@echo "Uso: make <alvo> [RELOAD=1] [HOST=0.0.0.0]"
	@echo
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "Python usado: $(PYTHON)"

install: ## Cria o .venv e instala as dependências de todas as apps
	@[ -d $(VENV) ] || python3 -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install -r requirements.txt

p1q1: ## Parte 1 - Q1: geração de texto com GPT-2 (porta 8001)
	$(call run_app,$(P1Q1),8001)

p1q2: ## Parte 1 - Q2: tradução EN -> FR com opus-mt (porta 8002)
	$(call run_app,$(P1Q2),8002)

p2q1: ## Parte 2 - Q1: chatbot com Fake LLM (porta 8011)
	$(call run_app,$(P2Q1),8011)

p2q2: check-env-p2q2 ## Parte 2 - Q2: tradução EN -> FR com OpenAI via LangChain (porta 8012)
	$(call run_app,$(P2Q2),8012)

p2q3: ## Parte 2 - Q3: tradução EN -> DE com LangChain + opus-mt (porta 8013)
	$(call run_app,$(P2Q3),8013)

check-env-p2q2:
	@[ -f $(P2Q2)/.env ] || echo "Aviso: $(P2Q2)/.env não existe. Copie o .env.example e preencha a OPENAI_API_KEY."

run-all: ## Sobe as cinco apps juntas (Ctrl+C encerra todas)
	@echo ">> Subindo as apps (8001, 8002, 8011, 8012, 8013). Ctrl+C encerra todas."
	@trap 'kill 0' INT TERM; \
	(cd $(P1Q1) && HOST=$(HOST) PORT=8001 $(PYTHON) main.py) & \
	(cd $(P1Q2) && HOST=$(HOST) PORT=8002 $(PYTHON) main.py) & \
	(cd $(P2Q1) && HOST=$(HOST) PORT=8011 $(PYTHON) main.py) & \
	(cd $(P2Q2) && HOST=$(HOST) PORT=8012 $(PYTHON) main.py) & \
	(cd $(P2Q3) && HOST=$(HOST) PORT=8013 $(PYTHON) main.py) & \
	wait

test: ## Roda os testes de todas as apps (sem baixar modelos nem chamar a OpenAI)
	@status=0; \
	for d in $(APPS); do \
		echo ">> $$d"; \
		(cd $$d && $(PYTHON) -m pytest -q -p no:cacheprovider) || status=1; \
	done; \
	exit $$status

benchmark: ## Mede latência e memória das apps (precisam estar rodando)
	$(PYTHON) docs/benchmark.py

clean: ## Remove caches e arquivos gerados (__pycache__, .pytest_cache, *.pyc, logs...)
	@find . -path ./$(VENV) -prune -o \( \
		-name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o \
		-name .ruff_cache -o -name htmlcov -o -name '*.egg-info' \
		\) -type d -prune -print -exec rm -rf {} +
	@find . -path ./$(VENV) -prune -o \( \
		-name '*.py[cod]' -o -name '.coverage' -o -name '*.log' -o -name '.DS_Store' \
		\) -type f -print -exec rm -f {} +
	@echo ">> Limpo (o $(VENV) e os arquivos .env foram mantidos)."
