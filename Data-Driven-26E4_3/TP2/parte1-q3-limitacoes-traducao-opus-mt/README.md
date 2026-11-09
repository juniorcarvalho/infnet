# TP2 - Parte 1 - Questão 3: Limitações do modelo de tradução Helsinki-NLP/opus-mt-en-fr

**Enunciado:** Com base na API da Questão 2 (Parte 1), explique as principais limitações do modelo de tradução utilizado: precisão da tradução; tempo de resposta e desempenho em grande escala; custo e escalabilidade; gírias, expressões idiomáticas e linguagem de contexto.

Aplicação analisada: [Parte 1 - Questão 2 (FastAPI + Helsinki-NLP/opus-mt-en-fr)](../parte1-q2-translation-en-fr/).

## Medições de referência

Medições feitas em notebook com WSL2 (Ubuntu 24.04), 12 vCPUs, ~7 GB de RAM, **sem GPU**, Python 3.14, PyTorch 2.15 (CPU), transformers 4.57.6 e LangChain-core 1.7. As latências são medianas de 3 execuções do script [`docs/benchmark.py`](../docs/benchmark.py) contra as APIs rodando localmente (resultados brutos em [`docs/benchmark_results.json`](../docs/benchmark_results.json)).

| Aplicação | Entrada | Latência (mediana) | RAM do processo | Pesos do modelo |
|---|---|---|---|---|
| P1 Q2 opus-mt-en-fr | frase curta (2 frases) | 0,27 s | ~850 MB | 287 MB |
| P1 Q2 opus-mt-en-fr | texto longo (~3.300 caracteres, 40 frases) | 7,0 s | | |
| P1 Q2 opus-mt-en-fr | 8 requisições curtas simultâneas | 4,7 s no total (1,7 req/s) | | |

## Resposta

O `opus-mt-en-fr` é um modelo MarianMT (Transformer encoder-decoder, ~75M parâmetros) treinado com o
corpus paralelo OPUS. É pequeno, gratuito e roda em CPU.

### 1. Precisão da tradução

O modelo aprendeu com pares de frases isoladas e não enxerga o documento. Pronomes, gênero e termos
que dependem de frases anteriores perdem a referência, e textos longos ficam inconsistentes.

O problema mais grave aparece quando ele recebe várias frases de uma vez: pode descartar parte delas.
A entrada `"Hello, how are you? It is raining cats and dogs."` enviada inteira volta só como
`"Il pleut des chats et des chiens."`.

Num texto de 60 frases agrupadas em 3 blocos, a saída teve 2.822 caracteres. Frase a frase, foram
6.899. **O modelo jogou fora mais da metade do conteúdo.**

E a falha não avisa. A resposta parece fluente, só que está incompleta. Por isso a API traduz frase a
frase, em batch.

Outros pontos fracos:

- **Ambiguidade.** Em `"The bank was closed, so we sat on the bank of the river."`, o modelo
  devolveu `"La rive était fermée, alors nous nous sommes assis sur la rive de la rivière."` e usou
  "rive" (margem) para os dois sentidos de "bank".
  O modelo alemão (P2 Q3) acertou a mesma frase (`"Die Bank war geschlossen ... am Ufer des Flusses"`).
  A qualidade muda conforme o par de idiomas.
- **Frases longas.** Acima de 512 tokens o texto seria cortado, e a qualidade cai antes disso. A API
  resolve com chunking.
- **Domínio.** O OPUS vai bem em textos genéricos (legendas, documentos da UE, software) e mal em
  termos médicos, jurídicos ou técnicos muito específicos.
- **Formalidade.** Não dá para escolher entre tu e vous. O modelo decide sozinho.
- A API não tem como saber quando a tradução está errada, porque o modelo não informa confiança.

### 2. Tempo de resposta e desempenho em grande escala

A latência cresce linearmente com o tamanho do texto: 0,27 s para duas frases e 7,0 s para ~3.300
caracteres em CPU. A decodificação gera um token por vez, e o beam search (`num_beams=4`) multiplica o custo.

Com várias requisições ao mesmo tempo, piora. Oito requisições curtas simultâneas levaram 4,7 s no
total (1,7 req/s), e cada cliente esperou ~4,5 s. Sozinha, a mesma requisição leva 0,27 s.

Em sequência, as oito terminariam em ~2,2 s. A concorrência atrapalha porque o PyTorch já usa todos
os núcleos em cada inferência, e as threads do FastAPI passam a disputar os mesmos núcleos.
O threadpool impede que o servidor trave, mas não cria capacidade de processamento.

- **Cold start.** O primeiro uso baixa ~300 MB do HuggingFace Hub, e carregar o modelo leva alguns
  segundos. Em autoscaling, cada réplica nova paga esse custo.
- **Memória.** ~850 MB de RAM por processo. Cada worker do Uvicorn carrega outra cópia do modelo.
- **O que ajuda:** GPU, quantização (int8) ou conversão para ONNX/CTranslate2, micro-batching de
  requisições concorrentes, `num_beams` menor (perde qualidade, ganha velocidade) e cache de
  traduções repetidas.

### 3. Custo e escalabilidade

Não há custo por requisição: o modelo é aberto (licença CC-BY 4.0). O custo está na
**infraestrutura fixa**. Os servidores ficam ligados mesmo sem uso, e GPU custa caro.

Escalar na horizontal pesa. Cada réplica precisa de ~1 GB de RAM e de alguns segundos para aquecer,
então a equipe tem que dimensionar para o pico. Numa API paga por uso, isso não acontece.

- **Um modelo por par de idiomas.** Atender N idiomas significa carregar e manter vários modelos
  (en-fr, en-de, fr-en...), e a memória e a operação crescem junto. Um LLM multilíngue faz tudo com um só.
- **Operação.** Monitoramento, atualização de dependências e cache de modelos ficam com a equipe.

### 4. Gírias, expressões idiomáticas e linguagem de contexto

O modelo traduz palavra por palavra. Saídas reais da API:

| Inglês                             | Saída do opus-mt-en-fr                        | Tradução idiomática esperada           |
|------------------------------------|-----------------------------------------------|----------------------------------------|
| It's raining cats and dogs.        | Il pleut des chats et des chiens.             | Il pleut des cordes.                   |
| Break a leg tonight!               | Brisez une jambe ce soir !                    | Merde pour ce soir !                   |
| That exam was a piece of cake.     | Cet examen était un morceau de gâteau.        | Cet examen était du gâteau.            |
| He kicked the bucket last year.    | Il a donné un coup de pied l'an dernier.      | Il a cassé sa pipe l'an dernier.       |
| Let's call it a day.               | C'est un jour.                                | On s'arrête là pour aujourd'hui.       |
| I'm feeling under the weather.     | Je me sens sous la météo.                     | Je ne me sens pas très bien.           |
| That's lit, bro, no cap.           | C'est allumé, frérot, pas de casquette.       | C'est génial, frérot, sans mentir.     |

Gírias recentes ("lit", "no cap") não existem no corpus de treino. Expressões idiomáticas viram
traduções literais sem sentido, ou com o sentido trocado: "kicked the bucket" virou um chute.

Ironia, sarcasmo, referências culturais e tudo o que depende da conversa também se perdem. O modelo
vê uma frase por vez.
