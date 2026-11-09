# TP2 - Parte 1 - Questão 2: Tradução EN -> FR com Helsinki-NLP/opus-mt-en-fr (FastAPI)

API FastAPI que recebe um texto em inglês e devolve a tradução para o francês usando o modelo
[Helsinki-NLP/opus-mt-en-fr](https://huggingface.co/Helsinki-NLP/opus-mt-en-fr) (MarianMT, ~75M
parâmetros). Funciona tanto com frases curtas quanto com textos longos (até 5000 caracteres).

## Estrutura do projeto

```text
parte1-q2-translation-en-fr/
├── main.py              # FastAPI, lifespan (pré-carrega o modelo), handler de erro, uvicorn
├── routers.py           # APIRouter: GET /health e POST /translate
├── models.py            # schemas Pydantic (TranslateRequest / TranslateResponse)
├── services.py          # Translator: pipeline("translation_en_to_fr"), tradução em batch
├── model_loader.py      # carrega o modelo 1x; memoriza falhas de carga (503 + nova tentativa)
├── text_chunking.py     # divisão de textos longos em parágrafos/frases e remontagem
├── config.py            # modelo, porta, limites, beam search, batch size
├── requirements.txt
├── pytest.ini
└── tests/
    ├── test_api.py           # API com tradutor fake (não baixa o modelo)
    ├── test_text_chunking.py # testes unitários do chunking (inclui abreviações)
    └── test_model_loader.py
```

## Requisitos

- Python 3.10 ou superior (testado com 3.14)
- ~1 GB de RAM livre e ~300 MB de disco para o modelo (baixado na primeira execução)
- Não precisa de GPU (PyTorch somente CPU)

## Configuração do ambiente de desenvolvimento

```bash
cd parte1-q2-translation-en-fr
python -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`sentencepiece` (tokenizador do Marian) e `sacremoses` (normalização) já estão no `requirements.txt`.
Em macOS, remova o sufixo `+cpu` da linha do `torch`.

## Execução

```bash
python main.py
# ou, em desenvolvimento, com recarga automatica ao salvar (como na Etapa 1):
uvicorn main:app --port 8002 --reload
```

A API sobe em `http://127.0.0.1:8002` e a documentação Swagger fica em `http://127.0.0.1:8002/docs`.
Na primeira execução o modelo é baixado para `~/.cache/huggingface`.

`GET /health` responde `200` com `"model_loaded": true` quando o modelo está pronto, e `503` com
`"model_loaded": false` se o carregamento falhou. Após uma falha, as requisições recebem `503`
imediatamente e uma nova tentativa de carga só ocorre depois de `LOAD_RETRY_SECONDS` (padrão 30 s).

## Endpoints

| Método | Rota         | Descrição                          |
|--------|--------------|------------------------------------|
| GET    | `/health`    | status, modelo e `model_loaded`    |
| POST   | `/translate` | traduz `text` de inglês para francês |

## Exemplos de uso

Frase curta:

```bash
curl -X POST http://127.0.0.1:8002/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you? I hope you are having a great day."}'
```

Resposta (real, CPU):

```json
{
  "source_text": "Hello, how are you? I hope you are having a great day.",
  "translated_text": "Bonjour, comment allez-vous ? J'espère que vous passez une bonne journée.",
  "source_lang": "en",
  "target_lang": "fr",
  "model": "Helsinki-NLP/opus-mt-en-fr",
  "chunks": 2,
  "latency_ms": 335.5
}
```

Texto longo com parágrafos (a estrutura de parágrafos é preservada):

```bash
curl -X POST http://127.0.0.1:8002/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Artificial intelligence is transforming software. Models can translate documents.\n\nHowever, they have limitations. Engineers must evaluate trade-offs."}'
```

Texto vazio ou acima de 5000 caracteres retorna `422`. Falha no modelo retorna `503`.

## Como textos longos são tratados

Modelos Marian aceitam no máximo 512 tokens por entrada e foram treinados com pares de **frases**.
Nos testes, ao receber várias frases de uma vez, o modelo às vezes **descartava conteúdo**
(`"Hello, how are you? It is raining cats and dogs."` virava só `"Il pleut des chats et des chiens."`).
Por isso, em `text_chunking.py`:

1. O texto é separado em parágrafos (linha em branco) e cada parágrafo em frases (regex `(?<=[.!?])\s+`).
   Abreviações não quebram a frase: `Dr.`, `Mr.`, `e.g.`, iniciais (`J. K.`) e qualquer ponto seguido de
   minúscula ou dígito (`the U.S. in 2020`) são tratados como continuação.
2. Cada frase vira um chunk (`GROUP_SENTENCES = False` em `config.py`; com `True`, as frases são
   agrupadas até `MAX_CHUNK_TOKENS=400` tokens).
3. Uma frase que sozinha passa do limite é quebrada por palavras: nada é truncado.
4. Os chunks são traduzidos em batch pelo pipeline (`batch_size=8`, `num_beams=4`).
5. As traduções são remontadas: frases unidas por espaço e parágrafos por `\n\n`. O campo `chunks`
   da resposta informa quantos blocos foram traduzidos.

## Testes

```bash
pytest
```

## Decisões de implementação

- Endpoint `def` (threadpool), já que a inferência em CPU é bloqueante.
- Modelo singleton (`ModelLoader`, thread-safe), injetado via `Depends(get_service)` e pré-carregado no `lifespan`.
- `transformers.pipeline("translation_en_to_fr")`, como na Etapa 3, com `device` = GPU se disponível.
- `transformers==4.57.6` fixado no `requirements.txt`: a task `translation` foi removida no transformers 5.x.
