# TP3: Assistente financeiro (ReAct + tools + memória)
.DEFAULT_GOAL := help
SHELL := /bin/bash
VENV := .venv
PYTHON ?= $(if $(wildcard $(VENV)/bin/python),$(abspath $(VENV)/bin/python),python3)

.PHONY: help venv install run test casos
help: ## mostra a ajuda
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/ -/'
venv: ## cria o ambiente virtual
	python3 -m venv $(VENV)
install: venv ## instala as dependências
	$(VENV)/bin/pip install -r requirements.txt
run: ## inicia a CLI
	$(PYTHON) main.py
test: ## roda os testes (sem custo, com Fake LLM)
	$(PYTHON) -m pytest
casos: ## roda os casos de uso com LLM real e gera o relatório
	$(PYTHON) scripts/rodar_casos_de_uso.py
