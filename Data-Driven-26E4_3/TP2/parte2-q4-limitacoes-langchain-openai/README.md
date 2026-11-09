# TP2 - Parte 2 - Questão 4: Limitações de usar LangChain para integrar a API da OpenAI

**Enunciado:** Com base na Questão 2 (Parte 2), explique as principais limitações de utilizar LangChain para integrar a API da OpenAI: latência de resposta; limites de uso da API; escalabilidade e custo; qualidade das traduções em comparação com outros modelos.

Aplicações analisadas: [Parte 2 - Questão 2 (FastAPI + LangChain + OpenAI)](../parte2-q2-langchain-openai-translation/), [Parte 1 - Questão 2 (FastAPI + Helsinki-NLP/opus-mt-en-fr)](../parte1-q2-translation-en-fr/).

## Medições de referência

Medições feitas em notebook com WSL2 (Ubuntu 24.04), 12 vCPUs, ~7 GB de RAM, **sem GPU**, Python 3.14, PyTorch 2.15 (CPU), transformers 4.57.6 e LangChain-core 1.7. As latências são medianas de 3 execuções do script [`docs/benchmark.py`](../docs/benchmark.py) contra as APIs rodando localmente (resultados brutos em [`docs/benchmark_results.json`](../docs/benchmark_results.json)).

| Aplicação | Entrada | Latência (mediana) | RAM do processo | Pesos do modelo |
|---|---|---|---|---|
| P2 Q2 LangChain + API compatível com OpenAI (DeepSeek `deepseek-flash`) | frase curta / texto longo | 0,99 s / 3,1 s (cache: 15 ms) | ~115 MB | - (remoto) |
| P2 Q2 LangChain + API compatível com OpenAI | 8 requisições curtas simultâneas | 1,4 s no total (5,6 req/s), sem 429 | | |
| P1 Q2 opus-mt-en-fr | frase curta (2 frases) | 0,27 s | ~850 MB | 287 MB |
| P1 Q2 opus-mt-en-fr | texto longo (~3.300 caracteres, 40 frases) | 7,0 s | | |
| P1 Q2 opus-mt-en-fr | 8 requisições curtas simultâneas | 4,7 s no total (1,7 req/s) | | |

## Resposta

### 1. Latência de resposta

Quem manda na latência é a rede. Cada tradução faz um round-trip HTTPS até o provedor, espera na fila
dele e só então o modelo gera a resposta.

Com a aplicação apontada para a API compatível do DeepSeek (`deepseek-flash`), uma frase curta levou
0,99 s (1,4 s na primeira chamada). O texto de ~3.300 caracteres levou 3,1 s.

No opus-mt local em CPU, o mesmo texto longo leva 7,0 s, mas uma frase curta sai em 0,27 s. Em textos
curtos, a rede custa mais que a inferência. E a latência depende do provedor e da fila dele, não da aplicação.

O LangChain em si pesa pouco. Montar o prompt, rodar os callbacks e fazer o parsing custa poucos
milissegundos, nada perto da rede. O custo aparece nas camadas de abstração:

- **Retries.** O backoff exponencial pode multiplicar a latência de uma requisição que falhou. Com
  `max_retries=2`, um erro permanente gera 3 tentativas, e o cliente só recebe o erro depois do
  backoff (~2,3 s no total).
- **Visibilidade.** Sem tracing (LangSmith), a abstração esconde detalhes como o tempo até o primeiro token.

O que a aplicação já faz para reduzir a latência: `async`/`ainvoke`, cliente singleton (keep-alive),
`gpt-4o-mini`, `temperature=0` e `InMemoryCache`. Com o cache, um texto repetido volta sem chamada
externa (no DeepSeek, ~1,3 s na primeira chamada e ~15 ms nas seguintes).

Dá para ir além com streaming (`astream`), que mostra a tradução enquanto o modelo gera, e com um
cache persistente (Redis) compartilhado entre réplicas. O `InMemoryCache` vale só para um processo e
some no restart.

### 2. Limites de uso da API da OpenAI

A OpenAI limita o uso por organização e por modelo: RPM (requisições por minuto), TPM (tokens por
minuto) e limites diários. Os valores dependem do *tier* da conta, que sobe com o histórico de gasto.

Quem passa do limite recebe **429**. A aplicação devolve HTTP 429 ao cliente, e o SDK tenta de novo
com `max_retries=2` e backoff, respeitando o `Retry-After`.

Em rajadas grandes, os retries só adiam o problema e aumentam a espera do usuário. Quem define a
capacidade é a cota da conta, não o servidor.

- **Créditos pré-pagos.** Sem saldo, a API também responde **429**, com o código
  `insufficient_quota`. Como o status é o mesmo do rate limit, o SDK repete a chamada à toa. A
  aplicação lê o código do erro e responde 503 ("conta sem créditos").
- **Tamanho da entrada.** Textos muito longos precisam ser divididos. A API aceita até 5.000 caracteres.
- **Dependência de terceiros.** Quedas, modelos descontinuados, mudanças de preço e de política de uso
  fogem do controle da aplicação. A política de conteúdo pode recusar textos sensíveis.
- **Chave de API.** Precisa ficar protegida (`.env` fora do Git) e ser trocada de tempos em tempos.
  Sem ela, a API responde 503.
- **Privacidade.** O texto do usuário sai da infraestrutura própria. Com dados sensíveis, isso pode
  violar a LGPD ou cláusulas de contrato.

### 3. Escalabilidade e custo

Escalar a aplicação é fácil. O servidor só faz I/O, ocupa ~115 MB de RAM, e um único processo `async`
atende muitas requisições ao mesmo tempo. **O gargalo passa a ser a cota do provedor**, não a infraestrutura.

O custo é por token, somando entrada e saída. Na tabela pública do `gpt-4o-mini`, são cerca de
US$ 0,15 por 1M de tokens de entrada e US$ 0,60 por 1M de saída (confira a tabela vigente).

Uma frase curta consumiu ~53 tokens de entrada (com o system prompt) e ~20 de saída. Dá frações de
centavo, mas o custo cresce linearmente com o volume e é difícil de prever. Modelos maiores
(`gpt-4o`) custam ~15 vezes mais.

- **Tokens que não aparecem.** O system prompt vai em toda chamada, e o retry de uma requisição que
  falhou também gasta cota. Cache, prompts curtos e modelos menores baixam o custo. Para volumes que
  não precisam de resposta imediata, a Batch API é assíncrona e mais barata.
- **Controles em produção.** Limite de gasto, cota por usuário e rate limiting na própria API, para
  que um cliente abusivo não esgote a cota de todos.

### 4. Qualidade das traduções em comparação com outros modelos

O LLM traduz **pelo sentido e com o contexto do texto inteiro**. Costuma acertar expressões
idiomáticas e gírias ("it's raining cats and dogs" tende a virar "il pleut des cordes"), resolve
ambiguidades como "bank" e mantém os termos consistentes.

Tom e formalidade se ajustam pelo prompt. Nas avaliações publicadas, LLMs grandes superam modelos de
tradução dedicados e pequenos como o opus-mt, sobretudo em textos longos e informais.

Os riscos:

- **Não-determinismo residual**, mesmo com `temperature=0`.
- **Alucinações.** O modelo pode acrescentar explicações, "corrigir" o original ou pular trechos.
- **Desobediência ao prompt.** Se o texto contém uma pergunta, o modelo pode respondê-la em vez de
  traduzir. É um tipo de *prompt injection*.
- **Validação difícil.** É mais difícil conferir a saída de forma automática.

**Saídas reais** (as mesmas frases da P1 Q3, pela aplicação da P2 Q2 apontada para o DeepSeek):

| Inglês | opus-mt-en-fr (P1 Q2) | deepseek-flash (P2 Q2) |
|---|---|---|
| It's raining cats and dogs. | Il pleut des chats et des chiens. | Il pleut des cordes. |
| Break a leg tonight! | Brisez une jambe ce soir ! | Merde pour ce soir ! |
| That exam was a piece of cake. | Cet examen était un morceau de gâteau. | Cet examen était un jeu d'enfant. |
| He kicked the bucket last year. | Il a donné un coup de pied l'an dernier. | Il a cassé sa pipe l'année dernière. |
| Let's call it a day. | C'est un jour. | Appelons-le un jour. |
| I'm feeling under the weather. | Je me sens sous la météo. | Je ne me sens pas dans mon assiette. |
| That's lit, bro, no cap. | C'est allumé, frérot, pas de casquette. | C'est de la bombe, frère, sans mentir. |
| The bank was closed, so we sat on the bank of the river. | La rive était fermée, alors nous nous sommes assis sur la rive de la rivière. | La banque était fermée, alors nous nous sommes assis sur la rive de la rivière. |

O DeepSeek traduziu 7 das 8 frases pelo sentido. Usou expressões francesas equivalentes ("Merde pour
ce soir", "Il a cassé sa pipe", "pas dans mon assiette") e transformou "lit, no cap" em "de la bombe,
sans mentir".

Também acertou os dois sentidos de "bank" ("banque" e "rive"). Só errou "Let's call it a day", que
saiu ao pé da letra. O opus-mt errou todas as expressões idiomáticas.

No texto longo, de 40 frases, o DeepSeek devolveu as 40, sem cortar nem acrescentar nada. Mesmo
assim, um LLM pode acrescentar ou repetir trechos e responder com status 200 e texto fluente. Só uma
validação, como comparar o número de frases, pegaria isso.

**Comparação resumida:**

| Aspecto                       | opus-mt-en-fr (P1 Q2)             | LLM via API (P2 Q2)                     |
|-------------------------------|-----------------------------------|-----------------------------------------|
| Expressões idiomáticas / gírias | traduz literalmente (ver [P1 Q3](../parte1-q3-limitacoes-traducao-opus-mt/)) | costuma traduzir pelo sentido          |
| Contexto entre frases         | nenhum (frase a frase)            | documento inteiro                       |
| Fidelidade estrita ao texto   | alta (quando não descarta frases) | alta, com risco de acréscimos           |
| Determinismo                  | total (beam search)               | quase total (`temperature=0`)           |
| Controle de tom/formalidade   | não                               | sim, via prompt                         |
| Latência (medida)             | 0,27 s (2 frases) / 7,0 s (texto longo), CPU local | DeepSeek 0,99 s / 3,1 s, variável (fila) |
| Custo                         | infraestrutura fixa               | por token                               |
