# TP2 - Parte 1 - Questão 1: Geração de texto com GPT-2 (FastAPI + transformers)

API FastAPI que recebe uma frase em JSON e devolve uma continuação gerada pelo modelo
[GPT-2](https://huggingface.co/gpt2) (124M parâmetros) da HuggingFace, usando a biblioteca `transformers`.

## Estrutura do projeto

```text
parte1-q1-gpt2-text-generation/
├── main.py           # cria o FastAPI, lifespan (pré-carrega o modelo), handler de erro, uvicorn
├── routers.py        # APIRouter: GET /health e POST /generate
├── models.py         # schemas Pydantic (GenerateRequest / GenerateResponse)
├── services.py       # TextGenerator: pipeline("text-generation") + GenerationConfig
├── model_loader.py   # carrega o modelo 1x; memoriza falhas de carga (503 + nova tentativa)
├── config.py         # nome do modelo, porta, parâmetros de geração e limites
├── requirements.txt
├── pytest.ini
└── tests/
    ├── test_api.py          # testes com gerador fake (não baixam o modelo)
    └── test_model_loader.py # singleton, falha memorizada e nova tentativa
```

## Requisitos

- Python 3.10 ou superior (testado com 3.14)
- ~1 GB de RAM livre e ~550 MB de disco para o modelo (baixado na primeira execução)
- Não precisa de GPU: o `requirements.txt` instala o PyTorch somente CPU

## Configuração do ambiente de desenvolvimento

```bash
cd parte1-q1-gpt2-text-generation
python -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

O `requirements.txt` aponta para o índice do PyTorch CPU (`--extra-index-url https://download.pytorch.org/whl/cpu`)
e fixa `torch==...+cpu`. Em macOS, remova o sufixo `+cpu` da linha do `torch`.

## Execução

```bash
python main.py
# ou, em desenvolvimento, com recarga automatica ao salvar (como na Etapa 1):
uvicorn main:app --port 8001 --reload
```

A API sobe em `http://127.0.0.1:8001`. Na primeira execução o GPT-2 é baixado para
`~/.cache/huggingface` (alguns segundos a minutos, conforme a rede). O modelo é carregado uma única
vez na inicialização (`lifespan`), então as requisições seguintes não pagam esse custo.

Variáveis de ambiente opcionais: `HOST`, `PORT`, `MODEL_NAME` (ex.: `distilgpt2`), `LOAD_RETRY_SECONDS`.

`GET /health` responde `200` com `"model_loaded": true` quando o modelo está pronto, e `503` com
`"model_loaded": false` se o carregamento falhou. Após uma falha, as requisições recebem `503`
imediatamente e uma nova tentativa de carga só ocorre depois de `LOAD_RETRY_SECONDS` (padrão 30 s).

Documentação interativa (Swagger): `http://127.0.0.1:8001/docs`

## Endpoints

| Método | Rota        | Descrição                                   |
|--------|-------------|---------------------------------------------|
| GET    | `/health`   | status, nome do modelo e `model_loaded`     |
| POST   | `/generate` | gera a continuação do texto de entrada      |

### Corpo da requisição `POST /generate`

| Campo                  | Tipo   | Padrão | Limites    | Descrição                                       |
|------------------------|--------|--------|------------|-------------------------------------------------|
| `prompt`               | string | -      | 1..1000    | frase de entrada (obrigatória, não pode ser vazia) |
| `max_new_tokens`       | int    | 50     | 1..200     | quantidade máxima de tokens gerados             |
| `temperature`          | float  | 0.9    | 0.1..2.0   | criatividade da amostragem                      |
| `top_k`                | int    | 50     | 1..1000    | amostra só entre os k tokens mais prováveis     |
| `num_return_sequences` | int    | 1      | 1..3       | quantas continuações diferentes gerar           |
| `seed`                 | int    | null   | -          | semente para resultado reproduzível             |

Os parâmetros vão num `GenerationConfig` (como no exemplo da Etapa 3), junto com os fixos:
`do_sample=True`, `top_p=0.95`, `no_repeat_ngram_size=3` (reduz repetições) e
`pad_token_id=eos_token_id` (o GPT-2 não tem token de padding).

## Exemplos de uso

```bash
curl -X POST http://127.0.0.1:8001/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Artificial intelligence will", "max_new_tokens": 30, "seed": 42}'
```

Resposta (real, CPU):

```json
{
  "prompt": "Artificial intelligence will",
  "generations": [
    {
      "generated_text": "Artificial intelligence will continue to evolve to create new types of AI, but it is still hard to see how we can make an AI that is completely compatible with artificial intelligence",
      "continuation": "continue to evolve to create new types of AI, but it is still hard to see how we can make an AI that is completely compatible with artificial intelligence"
    }
  ],
  "model": "gpt2",
  "latency_ms": 1259.2
}
```

Várias continuações:

```bash
curl -X POST http://127.0.0.1:8001/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Once upon a time", "num_return_sequences": 3, "temperature": 1.2}'
```

Entrada inválida (prompt vazio) retorna `422`:

```bash
curl -X POST http://127.0.0.1:8001/generate -H "Content-Type: application/json" -d '{"prompt": "   "}'
```

Se o modelo não puder ser carregado ou falhar na geração, a API responde `503` com `{"detail": "..."}`.

## Testes

```bash
pytest
```

Os testes usam `app.dependency_overrides` para trocar o `TextGenerator` por um fake, então rodam em
milissegundos e não baixam o modelo.

## Decisões de implementação

- O endpoint é `def` (não `async def`): a inferência é CPU-bound e bloqueante; o FastAPI a executa
  num threadpool e o event loop continua livre.
- O modelo é um singleton (`ModelLoader`, thread-safe) injetado via `Depends(get_service)` e pré-carregado
  no `lifespan`.
- Segue o padrão da Etapa 3: `device` escolhido com `torch.cuda.is_available()`,
  `generation_config.max_length = None` (evita conflito com `max_new_tokens`), `GenerationConfig` e
  `return_full_text=False`. A resposta traz só a parte nova (`continuation`) e o texto completo
  (`generated_text` = prompt + continuação).
- Diferença consciente em relação ao exemplo da aula (TinyLlama): não há `apply_chat_template` nem
  mensagens `system`/`user`, porque o GPT-2 não é um modelo de chat e não tem chat template; ele só
  continua o texto recebido.
- `seed` usa `transformers.set_seed`, que altera o RNG global do torch: a reprodutibilidade só é
  garantida sem requisições concorrentes.
- Os textos são gerados em inglês: o GPT-2 foi treinado majoritariamente com textos em inglês.
