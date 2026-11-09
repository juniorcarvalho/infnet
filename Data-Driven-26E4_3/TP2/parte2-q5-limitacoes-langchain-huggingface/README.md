# TP2 - Parte 2 - Questão 5: Limitações de usar LangChain para integrar o modelo HuggingFace

**Enunciado:** Com base na Questão 3 (Parte 2), explique as limitações de usar LangChain para integrar o modelo HuggingFace de tradução: desempenho e tempo de resposta; consumo de recursos computacionais; limitações no ajuste fino do modelo; comparação com o uso direto da API HuggingFace.

Aplicações analisadas: [Parte 2 - Questão 3 (FastAPI + LangChain + Helsinki-NLP/opus-mt-en-de)](../parte2-q3-langchain-hf-translation-en-de/), [Parte 1 - Questão 2 (FastAPI + Helsinki-NLP/opus-mt-en-fr)](../parte1-q2-translation-en-fr/).

## Medições de referência

Medições feitas em notebook com WSL2 (Ubuntu 24.04), 12 vCPUs, ~7 GB de RAM, **sem GPU**, Python 3.14, PyTorch 2.15 (CPU), transformers 4.57.6 e LangChain-core 1.7. As latências são medianas de 3 execuções do script [`docs/benchmark.py`](../docs/benchmark.py) contra as APIs rodando localmente (resultados brutos em [`docs/benchmark_results.json`](../docs/benchmark_results.json)).

| Aplicação | Entrada | Latência (mediana) | RAM do processo | Pesos do modelo |
|---|---|---|---|---|
| P2 Q3 LangChain + opus-mt-en-de | frase curta / texto longo | 0,21 s / 4,2 s | ~930 MB | 285 MB |
| P2 Q3 LangChain + opus-mt-en-de | 8 requisições curtas simultâneas | 3,7 s no total (2,2 req/s) | | |
| P1 Q2 opus-mt-en-fr | frase curta (2 frases) | 0,27 s | ~850 MB | 287 MB |
| P1 Q2 opus-mt-en-fr | texto longo (~3.300 caracteres, 40 frases) | 7,0 s | | |
| P1 Q2 opus-mt-en-fr | 8 requisições curtas simultâneas | 4,7 s no total (1,7 req/s) | | |

## Resposta

### 1. Desempenho e tempo de resposta

O LangChain quase não pesa. Em 15 repetições, traduzir duas frases chamando o `transformers.pipeline`
direto levou 225 ms (mediana). Pela chain (`PromptTemplate | HuggingFacePipeline | StrOutputParser`
com `batch`), levou 221 ms. A diferença fica dentro do ruído da medição.

O tempo vai quase todo para a inferência do Marian em CPU: 0,21 s para uma frase curta e 4,2 s para
~3.300 caracteres.

O problema da abstração é outro: ela esconde decisões de desempenho. O batching depende de como
alguém escreveu o wrapper.

O `HuggingFacePipeline` recebe todos os prompts de um `chain.batch` numa só chamada e os repassa ao
pipeline em lotes de `batch_size`. Os 21 chunks do texto longo viram uma chamada. Um `LLM` genérico do
LangChain chamaria `_call` uma vez por prompt.

- **Parâmetros fixos.** `num_beams` e `max_new_tokens` ficam fixos em `pipeline_kwargs` na criação. Não
  dá para mudar por requisição.
- **Sem paralelismo real.** Em CPU, a inferência é CPU-bound. O `batch` do LangChain usa threads, que
  não aceleram nada além do que o PyTorch já paraleliza por conta própria.
- **Cold start.** Carregar os pesos (~285 MB) leva alguns segundos por processo, e o LangChain não muda isso.

### 2. Consumo de recursos computacionais

Cada processo usa ~930 MB de RAM (PyTorch, pesos e tokenizer). A P1 Q2, com um modelo do mesmo
tamanho, usa ~850 MB. A diferença, algumas dezenas de MB, vem do LangChain e do
`langchain-huggingface`. Cada worker do Uvicorn carrega a própria cópia do modelo.

- **CPU.** Cada tradução ocupa vários núcleos por centenas de milissegundos. Um servidor atende
  poucas requisições por segundo, e as simultâneas entram na fila. Para escalar, só com GPU ou mais
  réplicas, e as duas opções têm custo fixo.
- **Disco e dependências.** PyTorch (centenas de MB), transformers e o cache de modelos deixam a
  imagem Docker maior e o deploy mais lento.

O LangChain acrescenta mais uma camada de dependências que mudam rápido. O `HuggingFacePipeline` não
funciona com o transformers 5, que removeu a task `translation`. Por isso a aplicação fixa
`transformers==4.57.6`.

### 3. Limitações no ajuste fino do modelo

O LangChain não treina modelo nenhum. Ele orquestra a inferência.

Para adaptar o opus-mt a um domínio jurídico ou médico, o fine-tuning acontece fora dele, com
`transformers.Seq2SeqTrainer`, PEFT/LoRA ou Marian-NMT. Isso exige dados paralelos de qualidade, GPU e
avaliação (BLEU/COMET). Depois é só recarregar o modelo ajustado no wrapper.

Prompt também não substitui o ajuste. O Marian **não segue instruções**, então os recursos típicos do
LangChain (system prompt, few-shot, templates com regras de estilo ou glossário) não funcionam.

Uma instrução escrita no prompt sairia traduzida junto com o texto. Na prática, o `PromptTemplate` só
repassa o texto.

- **A interface limita a geração.** A interface genérica de `LLM` recebe texto e devolve texto. Ela não
  expõe recursos de tradução como restrição de vocabulário ou glossário (`force_words_ids`), n-best
  com scores ou alinhamentos.
- **Esquecimento catastrófico.** Treinar num domínio estreito com poucos dados piora a tradução
  genérica (*catastrophic forgetting*). E cada par de idiomas precisa do próprio ajuste.

### 4. Comparação com o uso direto da API HuggingFace

| Critério        | LangChain + modelo local (P2 Q3)                            | Uso direto do transformers (P1 Q2) / HF Inference API                                        |
|-----------------|-------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| Código          | mais camadas (`HuggingFacePipeline`, chain, parser)         | `pipeline("translation")`: menos código e mais controle                                      |
| Desempenho      | overhead dentro do ruído; batching via `batch_size` do wrapper | controle total de batch, beams e quantização; a Inference API soma latência de rede       |
| Flexibilidade   | trocar o modelo por OpenAI/Fake sem mudar a chain; callbacks, tracing, cache | acesso a todos os recursos do modelo (scores, constraints)                  |
| Compatibilidade | depende de duas bibliotecas evoluírem juntas (exige transformers 4.x) | só depende do transformers (a P1 Q2 também usa a task `translation`, removida no 5.x) |
| Infraestrutura  | local: RAM, CPU/GPU e cold start por conta própria          | Inference API: sem infraestrutura, mas paga, com rate limit, cold start de modelos pouco usados e dados saindo da rede |

Para um modelo de tradução dedicado, o LangChain acrescenta pouco. Ele compensa quando a tradução é
**uma etapa** de um fluxo maior (RAG, agentes, roteamento entre provedores, fallback da OpenAI para o
modelo local) ou quando a equipe quer uma interface única para trocar de modelo.
