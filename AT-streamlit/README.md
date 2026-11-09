# Dashboard de Futebol com Streamlit

Dashboard didático de Sports Analytics com dados abertos da StatsBomb. A pergunta analítica é: como os eventos, passes e finalizações ajudam a explicar o desempenho das equipes em uma partida?

A aplicação permite selecionar campeonato, temporada e partida. Os dados são buscados na StatsBombPy, normalizados e mantidos em cache para evitar consultas repetidas.

## Análise da partida

Na barra lateral, o formulário reúne filtros de jogador, intervalo de minutos, tipo de evento, busca textual, equipe dos mapas, limite de eventos visíveis e coordenadas na tabela. Os filtros são aplicados ao clicar em `Aplicar filtros` e permanecem durante os reruns da aplicação.

Os cards mostram gols, finalizações, passes completos e conversão. A aba de gráficos inclui distribuição e ritmo de eventos com gráficos nativos do Streamlit, mapas de passes e finalizações com mplsoccer e gráficos de relação entre estatísticas com Matplotlib e Seaborn. Os indicadores e gráficos usam todo o recorte filtrado; a tabela e o download CSV respeitam apenas o limite de eventos exibidos.

A segunda página oferece uma comparação opcional de até dois jogadores, com passes, acerto de passe, finalizações e gols no mesmo recorte analítico.


# Url streamlit cloud

https://at-stream-lit-jr.streamlit.app/

## Tecnologias

- Streamlit para interface e filtros;
- StatsBombPy para dados abertos de futebol;
- Pandas para tratamento dos eventos;
- mplsoccer, Matplotlib e Seaborn para visualizações.

## Execução local

```bash
git clone https://github.com/juniorcarvalho/AT-streamlit.git
cd AT-streamlit
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Organização

- `app.py`: configuração global e roteamento nativo;
- `pages/`: entradas das páginas de análise e comparação;
- `views/`: filtros, estado compartilhado e apresentação reutilizável;
- `data_loader.py`: consulta e normalização dos eventos;
- `charts.py`: mapas e gráficos;
- `utils.py`: formatação e download CSV;
- `.streamlit/config.toml`: tema visual;
- `requirements.txt`: dependências do projeto.
