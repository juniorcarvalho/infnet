# TP2 - Parte 2 - Questão 6: Tabela comparativa FastAPI puro x LangChain

**Enunciado:** Com base nas Questões 1-2 (Parte 1) e 2-3 (Parte 2), tabela comparativa entre FastAPI puro e LangChain: facilidade de uso/configuração; latência e desempenho; flexibilidade para diferentes modelos; custo e escalabilidade; adequação para protótipos versus produção.

Aplicações analisadas: [Parte 1 - Questão 1 (FastAPI + GPT-2)](../parte1-q1-gpt2-text-generation/), [Parte 1 - Questão 2 (FastAPI + Helsinki-NLP/opus-mt-en-fr)](../parte1-q2-translation-en-fr/), [Parte 2 - Questão 2 (FastAPI + LangChain + OpenAI)](../parte2-q2-langchain-openai-translation/), [Parte 2 - Questão 3 (FastAPI + LangChain + Helsinki-NLP/opus-mt-en-de)](../parte2-q3-langchain-hf-translation-en-de/).

## Medições de referência

Medições feitas em notebook com WSL2 (Ubuntu 24.04), 12 vCPUs, ~7 GB de RAM, **sem GPU**, Python 3.14, PyTorch 2.15 (CPU), transformers 4.57.6 e LangChain-core 1.7. As latências são medianas de 3 execuções do script [`docs/benchmark.py`](../docs/benchmark.py) contra as APIs rodando localmente (resultados brutos em [`docs/benchmark_results.json`](../docs/benchmark_results.json)).

| Aplicação | Entrada | Latência (mediana) | RAM do processo | Pesos do modelo |
|---|---|---|---|---|
| P1 Q1 GPT-2 | 20 / 100 / 200 tokens gerados | 0,81 / 3,3 / 7,4 s | ~1.040 MB | 523 MB |
| P1 Q1 GPT-2 | 8 requisições simultâneas de 50 tokens | 25,3 s no total (0,32 req/s) | | |
| P1 Q2 opus-mt-en-fr | frase curta (2 frases) | 0,27 s | ~850 MB | 287 MB |
| P1 Q2 opus-mt-en-fr | texto longo (~3.300 caracteres, 40 frases) | 7,0 s | | |
| P1 Q2 opus-mt-en-fr | 8 requisições curtas simultâneas | 4,7 s no total (1,7 req/s) | | |
| P2 Q2 LangChain + API compatível com OpenAI (DeepSeek `deepseek-flash`) | frase curta / texto longo | 0,99 s / 3,1 s (cache: 15 ms) | ~115 MB | - (remoto) |
| P2 Q2 LangChain + API compatível com OpenAI | 8 requisições curtas simultâneas | 1,4 s no total (5,6 req/s), sem 429 | | |
| P2 Q3 LangChain + opus-mt-en-de | frase curta / texto longo | 0,21 s / 4,2 s | ~930 MB | 285 MB |
| P2 Q3 LangChain + opus-mt-en-de | 8 requisições curtas simultâneas | 3,7 s no total (2,2 req/s) | | |

## Resposta

| Abordagem | Facilidade de uso / configuração | Latência e desempenho | Flexibilidade para diferentes modelos | Custo e escalabilidade | Adequação: protótipo x produção |
|---|---|---|---|---|---|
| **FastAPI puro + transformers** (P1 Q1 GPT-2, P1 Q2 opus-mt-en-fr) | Média: poucas dependências conceituais, mas exige conhecer o transformers (tokenizer, `generate`, padding, limites de tokens, chunking) e instalar PyTorch (~centenas de MB). Modelo baixado na 1a execução. | Sem overhead de framework; controle fino de batch, beams e `inference_mode`. Em CPU: 0,27 s por frase curta e 7,0 s por texto longo (tradução); ~35 ms por token (GPT-2). CPU-bound, concorrência limitada. | Baixa: o código é acoplado à API de cada modelo; trocar de GPT-2 para um modelo de tradução ou para a OpenAI exige reescrever o serviço. | Sem custo por requisição; custo fixo de infraestrutura (~0,8 a 1 GB de RAM por processo, GPU para escala). Escala horizontal com cold start. Dados ficam na própria infraestrutura. | Bom para produção quando o modelo é fixo e o desempenho e a privacidade importam; exige engenharia de MLOps (quantização, GPU, batching). |
| **LangChain + OpenAI** (P2 Q2) | Alta: poucas linhas (prompt, `ChatOpenAI` e parser numa chain), sem baixar modelos nem gerenciar hardware; só precisa de uma API key. | Dominada pela rede e pela fila do provedor (medido no DeepSeek: 0,99 s para frase curta e 3,1 s para texto longo); overhead do LangChain desprezível; `async`, cache (~15 ms) e retries ajudam. | Alta: trocar de modelo/provedor é mudar configuração (`OPENAI_BASE_URL` e `OPENAI_MODEL`, sem mudar o código); prompts ajustam tom e tarefa sem re-treino. | Pago por token, sem custo fixo; escala elástica limitada por rate limits (RPM/TPM) e pelo orçamento. Servidor leve (~115 MB). | Excelente para protótipos; viável em produção com controle de custos, limites, fallback e cuidados com privacidade (LGPD). |
| **LangChain + HuggingFace local** (P2 Q3) | Média/baixa: soma a complexidade do transformers e a do LangChain; incompatibilidades entre versões (o `HuggingFacePipeline` não suporta tradução no transformers 5) exigem fixar `transformers==4.57.6`. | Igual ao modelo local (0,21 s por frase curta, 4,2 s por texto longo); overhead da chain dentro do ruído de medição; batching via `batch_size` do `HuggingFacePipeline`. | Média/alta: a interface LangChain permite trocar Marian, OpenAI ou Fake na mesma chain; mas modelos de tradução não seguem prompts, então parte da flexibilidade não se aplica. | Igual ao FastAPI puro + transformers (infraestrutura fixa, ~930 MB por processo), mais dependências para manter. | Bom para protótipos que já usam LangChain ou que precisam alternar entre provedores; em produção, só se justifica se a tradução fizer parte de um fluxo LangChain maior. |

### Resumo: FastAPI puro x LangChain

| | Facilidade de uso / configuração | Latência e desempenho | Flexibilidade para diferentes modelos | Custo e escalabilidade | Protótipos x produção |
|---|---|---|---|---|---|
| **FastAPI puro** | Mais código específico do modelo, porém menos camadas e dependências | Máximo controle; nenhum overhead extra | Baixa: trocar de modelo significa reescrever o serviço | Definido pelo modelo escolhido (local = fixo; API = por uso) | Produção com modelo fixo e requisitos rígidos de desempenho |
| **LangChain** | Componentes prontos (prompts, parsers, cache, retries); curva de aprendizado e versões instáveis | Overhead desprezível (dentro do ruído medido); abstração pode esconder ineficiências (ex.: batch) | Alta: interface única para OpenAI, HuggingFace e outros | Igual ao modelo subjacente, mais dependências | Excelente para protótipos e fluxos com vários passos ou modelos; em produção, exige fixar versões e observabilidade |

### Custo e escalabilidade: análise objetiva

Números medidos neste ambiente (CPU, 12 vCPUs) e estimativas declaradas como tais:

| Métrica | FastAPI/LangChain + modelo local (P1 Q2, P2 Q3) | LangChain + API compatível com OpenAI (P2 Q2, medido no DeepSeek `deepseek-flash`) |
|---|---|---|
| RAM por processo (medida) | ~850 a 930 MB (tradução); ~1.040 MB (GPT-2) | ~115 MB |
| Throughput por máquina (medido, 8 requisições curtas simultâneas) | 1,7 a 2,2 req/s, ou seja, ~6.000 a 8.000 traduções curtas por hora | limitado pela cota do provedor, não pela máquina: 5,6 req/s nessa rajada, sem 429 |
| Cold start | download de ~285 MB na 1a execução + alguns segundos de carga por réplica | nenhum (só abrir a conexão HTTPS) |
| Custo fixo | a máquina ligada 24h, com ou sem uso | zero |
| Custo variável (tokens medidos) | zero | frase curta: 53 tokens de entrada (com o system prompt) + 20 de saída, ~US$ 0,00004; texto de ~3.300 caracteres: 538 + 880 tokens, ~US$ 0,0012 |
| Custo por 1 milhão de traduções curtas | o custo da máquina pelas ~125 a 165 horas necessárias para processá-las | ~US$ 40 (pico) ou ~US$ 20 (fora do pico) |

Premissas: tokens medidos no DeepSeek; preços oficiais do `deepseek-flash` no horário de pico
(US$ 0,30 por 1M de tokens de entrada sem cache e US$ 1,20 por 1M de saída; fora do pico, metade),
sem considerar o desconto de cache de entrada. Como referência, o `gpt-4o-mini` custa US$ 0,15 e
US$ 0,60 (a conferir na tabela vigente), ou seja, a mesma ordem de grandeza.

O que os números mostram:

Uma máquina saturada faz ~6.000 traduções curtas por hora. O mesmo volume no DeepSeek custaria
~US$ 0,24/hora no pico (~US$ 0,12 fora dele).

O modelo local só sai mais barato se a máquina custar menos que isso por hora e ficar ocupada o tempo
todo. Com tráfego baixo ou irregular, a máquina parada pesa, e a API paga por uso ganha. Com volume
alto e constante, ou com GPU bem aproveitada, o modelo local tende a vencer.

Na escala, a abordagem local cresce comprando máquinas, com ~1 GB de RAM por processo e cold start
em cada réplica. A API cresce sem infraestrutura, mas esbarra nos limites do provedor (RPM/TPM ou
concorrência) e no saldo de créditos (`insufficient_quota`).

O LangChain não muda essa conta. Ele soma dezenas de MB e um overhead dentro do ruído. Quem define
custo e escala são o modelo e o provedor, não o framework.

Nos dois casos, o FastAPI segue como a camada HTTP. Muda só o jeito de chamar o modelo: direto ou
pelo LangChain.
