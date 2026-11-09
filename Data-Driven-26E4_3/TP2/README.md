# TP2: APIs com FastAPI e LangChain usando LLMs

Cinco aplicações práticas e cinco respostas teóricas, uma pasta autocontida por questão (cada uma
pode virar um repositório separado). As pastas das questões teóricas têm um único `README.md` com a
resposta, as tabelas e os diagramas.

[Relatório final (PDF)](relatorio-final.pdf)

## Aplicações

| Questão      | Pasta                                                                              | Porta | Endpoint principal | Descrição                                          |
|--------------|------------------------------------------------------------------------------------|-------|--------------------|----------------------------------------------------|
| Parte 1 - Q1 | [parte1-q1-gpt2-text-generation](parte1-q1-gpt2-text-generation/)                  | 8001  | `POST /generate`   | Geração de texto com GPT-2 (FastAPI + transformers) |
| Parte 1 - Q2 | [parte1-q2-translation-en-fr](parte1-q2-translation-en-fr/)                        | 8002  | `POST /translate`  | Tradução EN -> FR com Helsinki-NLP/opus-mt-en-fr   |
| Parte 2 - Q1 | [parte2-q1-fake-llm-chatbot](parte2-q1-fake-llm-chatbot/)                          | 8011  | `POST /chat`       | Chatbot com Fake LLM (LangChain)                   |
| Parte 2 - Q2 | [parte2-q2-langchain-openai-translation](parte2-q2-langchain-openai-translation/)  | 8012  | `POST /translate`  | Tradução EN -> FR com OpenAI via LangChain         |
| Parte 2 - Q3 | [parte2-q3-langchain-hf-translation-en-de](parte2-q3-langchain-hf-translation-en-de/) | 8013 | `POST /translate` | Tradução EN -> DE com LangChain + opus-mt-en-de    |

## Questões teóricas

| Questão      | Pasta                                                                                    | Conteúdo                                                        |
|--------------|------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| Parte 1 - Q3 | [parte1-q3-limitacoes-traducao-opus-mt](parte1-q3-limitacoes-traducao-opus-mt/)          | Limitações do opus-mt-en-fr (precisão, desempenho, custo, gírias) |
| Parte 1 - Q4 | [parte1-q4-limitacoes-gpt2](parte1-q4-limitacoes-gpt2/)                                  | Limitações do GPT-2 (coerência, falhas, latência, conteúdo)     |
| Parte 2 - Q4 | [parte2-q4-limitacoes-langchain-openai](parte2-q4-limitacoes-langchain-openai/)          | Limitações de LangChain + OpenAI (latência, limites, custo, qualidade) |
| Parte 2 - Q5 | [parte2-q5-limitacoes-langchain-huggingface](parte2-q5-limitacoes-langchain-huggingface/) | Limitações de LangChain + HuggingFace (desempenho, recursos, ajuste fino, API HF) |
| Parte 2 - Q6 | [parte2-q6-comparativo-fastapi-langchain](parte2-q6-comparativo-fastapi-langchain/)      | Tabela comparativa FastAPI puro x LangChain                     |

Os diagramas de arquitetura pedidos no enunciado (Parte 2, Q1 a Q3) estão no README de cada uma
dessas apps, com a fonte Mermaid em `docs/arquitetura.mmd` e a imagem em `docs/arquitetura.png`.

## Estrutura das aplicações

Cada pasta de aplicação tem `README.md` próprio, com instruções detalhadas, exemplos `curl` e testes.
Todas seguem o mesmo padrão:

```text
main.py        # cria o FastAPI (lifespan, handlers de erro) e roda o uvicorn
routers.py     # APIRouter: GET /health + endpoint POST (nome da "Estrutura Flat" da Etapa 2)
models.py      # schemas Pydantic de request/response (validação com strip/limites)
services.py    # carrega o modelo/chain uma única vez; injetado via Depends(get_service)
model_loader.py # (apps com modelo local) singleton + falha de carga memorizada
config.py      # constantes e variáveis de ambiente
tests/         # pytest + TestClient; o modelo é trocado por um fake (sem download/rede)
docs/          # (Parte 2, Q1 a Q3) diagrama de arquitetura: arquitetura.mmd + arquitetura.png
requirements.txt, pytest.ini, .gitignore
```

## Configuração do ambiente de desenvolvimento

Requisitos: Python 3.10 ou superior (testado com 3.14), ~3 GB de RAM livre para rodar as três apps
com modelos locais ao mesmo tempo, e ~1,5 GB de disco para os modelos. Não precisa de GPU.

### Opção A: um ambiente único para todas as apps (usado no desenvolvimento)

```bash
cd tp2
python -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt    # dependências de todas as apps (PyTorch CPU)
```

### Opção B: um ambiente por app

Entre na pasta da app e siga o README dela (`python -m venv .venv` e `pip install -r requirements.txt`).

Observações:

- `transformers==4.57.6` está fixado: no 5.x a task `translation` (usada pelo `pipeline` da P1Q2 e
  pelo `HuggingFacePipeline` da P2Q3) foi removida.
- Os `requirements.txt` usam `--extra-index-url https://download.pytorch.org/whl/cpu` e `torch==...+cpu`
  (wheel sem CUDA, bem menor). Em macOS, remova o sufixo `+cpu`.
- Na primeira execução, os modelos (GPT-2 ~523 MB, cada opus-mt ~285 MB) são baixados para
  `~/.cache/huggingface`.
- A app da OpenAI precisa de `parte2-q2-langchain-openai-translation/.env`, criado a partir do
  `.env.example`, com a `OPENAI_API_KEY`.

## Atalhos com make

O `Makefile` da raiz reúne os comandos mais usados. Rodar só `make` mostra a ajuda.

```bash
make install            # cria o .venv e instala as dependências
make p1q2               # sobe uma app (p1q1, p1q2, p2q1, p2q2, p2q3)
make p1q2 RELOAD=1      # mesma coisa, com uvicorn --reload
make run-all            # sobe as cinco apps juntas; Ctrl+C encerra todas
make test               # roda os testes de todas as apps
make benchmark          # roda o docs/benchmark.py (apps no ar)
make clean              # apaga __pycache__, *.pyc, .pytest_cache, logs e outros caches
```

O `make` usa o Python do `.venv` quando ele existe, sem precisar ativar o ambiente. O `clean` não
mexe no `.venv` nem nos arquivos `.env`.

## Como executar

Sem o `make`, com o ambiente ativado, cada app roda em sua própria porta:

```bash
cd parte1-q1-gpt2-text-generation && python main.py               # http://127.0.0.1:8001/docs
cd parte1-q2-translation-en-fr && python main.py                  # http://127.0.0.1:8002/docs
cd parte2-q1-fake-llm-chatbot && python main.py                   # http://127.0.0.1:8011/docs
cd parte2-q2-langchain-openai-translation && python main.py       # http://127.0.0.1:8012/docs
cd parte2-q3-langchain-hf-translation-en-de && python main.py     # http://127.0.0.1:8013/docs
```

Em desenvolvimento, também é possível usar o `uvicorn` com recarga automática (Etapa 1):

```bash
cd parte1-q1-gpt2-text-generation && uvicorn main:app --port 8001 --reload
```

Teste rápido:

```bash
curl -X POST http://127.0.0.1:8002/translate -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?"}'
```

## Testes

Os testes não baixam modelos nem chamam a OpenAI:

```bash
for d in parte*/; do [ -d "$d/tests" ] && (cd "$d" && python -m pytest -q); done
```

## Medições

As medições citadas nas respostas teóricas vêm de `docs/benchmark.py` (resultados em
`docs/benchmark_results.json`). Para coletá-las de novo, com as apps rodando:

```bash
python docs/benchmark.py            # todas as apps
python docs/benchmark.py p2q2       # só as indicadas, mesclando no JSON existente
```

Para regenerar a imagem de um diagrama após editar o `.mmd` (requer Node.js):

```bash
npx -y @mermaid-js/mermaid-cli -i docs/arquitetura.mmd -o docs/arquitetura.png -b white -s 2
```

## Uso de IA

Este trabalho usou IA generativa como apoio. Modelo: **Claude Opus 5.5** (Anthropic), via Claude Code.

- **Criados por IA:** os `README.md` das aplicações (documentação do código), os testes automatizados
  (`tests/`) e o script de benchmark (`docs/benchmark.py`).
- **Revisados por IA:** o código das aplicações e as respostas em `.md` das questões.

O conteúdo gerado foi integralmente revisado, verificado e validado pelo autor.
