# Amostra da referência municipal

`municipios_brasil_wikipedia_amostra.csv` é um recorte do CSV local gerado
pelo scraper `coletar_municipios_wikipedia`, a partir da
[Lista de municípios do Brasil na Wikipédia](https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Brasil).

- Formato: CSV UTF-8, separado por vírgulas, com `municipio`, `uf` e `estado`.
- Conteúdo: os primeiros dois registros disponíveis de cada UF na ordem do
  arquivo coletado, ordenado por UF e município. São 52 registros dos 26
  estados. O Distrito Federal não aparece na coleta local utilizada.
- Finalidade: permitir consultar a referência territorial após clonar o
  projeto, sem rede nem execução prévia do scraper.
- Limitações: recorte demonstrativo, sem representatividade estatística,
  código IBGE ou indicadores de saneamento. Não participa do score.

O carregamento prefere `data/processed/municipios_brasil_wikipedia.csv` quando
esse arquivo existe; na ausência dele, utiliza automaticamente a amostra e
a interface identifica o recorte.
Reinicie o Streamlit depois de gerar a coleta para renovar o cache municipal.

Para atualizar a referência completa, a partir da raiz e com o ambiente ativo:

```bash
SCRAPE_MUNICIPIOS=1 python src/data_access.py
```

A execução não substitui esta amostra. Caso o recorte seja atualizado
futuramente, revise os registros, a proveniência e a data documentada.
