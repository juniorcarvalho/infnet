# TP2 - Parte 1 - Questão 4: Limitações do GPT-2 na geração de texto

**Enunciado:** Com base no modelo GPT-2 da Questão 1 (Parte 1), explique as principais limitações do modelo na geração de texto: coerência do texto gerado; falhas ou incoerências geradas por LLMs; desempenho e latência; geração de conteúdo apropriado.

Aplicação analisada: [Parte 1 - Questão 1 (FastAPI + GPT-2)](../parte1-q1-gpt2-text-generation/).

## Medições de referência

Medições feitas em notebook com WSL2 (Ubuntu 24.04), 12 vCPUs, ~7 GB de RAM, **sem GPU**, Python 3.14, PyTorch 2.15 (CPU), transformers 4.57.6 e LangChain-core 1.7. As latências são medianas de 3 execuções do script [`docs/benchmark.py`](../docs/benchmark.py) contra as APIs rodando localmente (resultados brutos em [`docs/benchmark_results.json`](../docs/benchmark_results.json)).

| Aplicação | Entrada | Latência (mediana) | RAM do processo | Pesos do modelo |
|---|---|---|---|---|
| P1 Q1 GPT-2 | 20 / 100 / 200 tokens gerados | 0,81 / 3,3 / 7,4 s | ~1.040 MB | 523 MB |
| P1 Q1 GPT-2 | 8 requisições simultâneas de 50 tokens | 25,3 s no total (0,32 req/s) | | |

## Resposta

O GPT-2 (versão base, 124M parâmetros, 2019) é um modelo autoregressivo **treinado só para prever o
próximo token** (WebText, em inglês). Não passou por ajuste de instruções nem por RLHF. Ele completa
texto, mas não responde perguntas nem segue comandos.

### 1. Coerência do texto gerado

As frases saem gramaticais, mas o texto perde o fio depois de poucas sentenças. Um exemplo real, com
o prompt "Once upon a time in a small village,":

> *"a young boy was brought here in his early twenties by his parents. The boy was a boy who wanted to
> get his father to join him in life."*

Um "boy" de vinte e poucos anos e uma frase que anda em círculo.

- **Contexto curto.** A janela é de 1.024 tokens, mas na prática o modelo "esquece" o tema bem antes.
- **Repetição ou deriva.** Sem `no_repeat_ngram_size` e sem amostragem (`top_p`, `temperature`), o
  modelo entra em loop ("The boy was a boy..."). Com temperatura alta, foge para assuntos sem relação.
  Os parâmetros da API (`temperature=0.9`, `top_k=50`, `top_p=0.95`, `no_repeat_ngram_size=3`)
  buscam um meio-termo entre os dois problemas.
- **Cada chamada dá um texto diferente.** É o efeito da amostragem. Para reproduzir um resultado, a
  API aceita `seed`.

### 2. Falhas e incoerências típicas de LLMs

O GPT-2 inventa fatos. Para o prompt *"The capital of Brazil is"*, ele gerou:

> *"known for its military, which in turn includes the military wing of the Brazilian military and the
> elite military organization known as the 'Tibetan Democratic Guard'"*

Não disse "Brasília" e ainda criou uma organização que não existe. O modelo busca o texto mais
plausível, não o verdadeiro.

- **Frases vazias.** *"it is still hard to see how we can make an AI that is completely compatible
  with artificial intelligence"* parece um argumento, mas é tautológico.
- **Instruções ignoradas.** Pedir "Translate to French: ..." ou "Answer the question: ..." não
  funciona de forma confiável. O modelo só continua o texto.
- **Conhecimento parado em 2019 e só em inglês.** Prompts em português geram texto ruim.
- **Contas e lógica.** Erra contas simples e cadeias de raciocínio.

### 3. Desempenho e latência

A latência acompanha o número de tokens gerados. Em CPU: 0,81 s para 20 tokens, 3,3 s para 100 e
7,4 s para 200, ou ~35 ms por token.

Cada token depende dos anteriores, então a geração é sequencial e não paraleliza dentro de uma
requisição. O processo ocupa ~1.040 MB de RAM, com 523 MB de pesos, e o cold start inclui download e
carregamento.

Com concorrência, a conta piora. Oito requisições simultâneas de 50 tokens levaram 25,3 s
(0,32 req/s). Cada usuário esperou ~25 s por um texto que, sozinho, sairia em ~1,8 s.

Em produção, isso pede GPU, batching dinâmico (vLLM, TGI) e streaming de tokens para o usuário ver o
texto chegando. Também pede limite de `max_new_tokens`, que a API já aplica (máx. 200).

### 4. Geração de conteúdo apropriado

O WebText vem de links do Reddit, e o modelo herdou o viés e a toxicidade desses dados. A própria
OpenAI documenta vieses de gênero, raça e religião no GPT-2. Um prompt inocente pode gerar conteúdo
ofensivo, estereotipado ou sexual.

- **Sem alinhamento nem filtros.** Não há RLHF nem moderação embutida. Para uso público, é preciso
  colocar camadas por fora: filtros de entrada e saída, classificadores de toxicidade, listas de
  bloqueio e moderação humana.
- **Desinformação.** Gera com facilidade textos fluentes e falsos (notícias, citações, dados). Foi por
  isso que a OpenAI lançou o modelo em etapas em 2019.
- **Sem fontes.** Pode reproduzir trechos memorizados sem dizer de onde vieram.
