import streamlit as st

from src.api_client import APIError
from src.ui_helpers import carregar_registros, csv_bytes

st.header("Exploração e ranking")
try:
    registros, fontes = carregar_registros()
except APIError as exc:
    st.error(str(exc))
    st.stop()
if not registros:
    st.info("Nenhum registro disponível para exploração.")
    st.stop()

origem = st.sidebar.selectbox("Origem", ["oficial", "complementar", "Todas"])
disponiveis = [item for item in registros if origem == "Todas" or item["Origem"] == origem]
if not disponiveis:
    st.info("Nenhum registro disponível para a origem selecionada.")
    st.stop()
ano = st.sidebar.selectbox("Ano", sorted({item["Ano"] for item in disponiveis}, reverse=True))
regiao = st.sidebar.selectbox("Região geográfica", ["Todas"] + sorted({item["Regiao"] for item in disponiveis if item["Ano"] == ano}))
st.caption("A visão inicial usa os dados oficiais. Você pode selecionar os dados complementares pelo filtro de origem.")
criterio = st.sidebar.radio("Ordenar por", ["Prioridade", "Menor cobertura de água", "Menor cobertura de esgoto", "Maior população sem saneamento", "Alfabética (UF)"])
filtrados = [item for item in registros if item["Ano"] == ano and (regiao == "Todas" or item["Regiao"] == regiao) and (origem == "Todas" or item["Origem"] == origem)]
if not filtrados:
    st.info("Nenhum dado atende aos filtros selecionados.")
    st.stop()

top = ", ".join(item["UF"] for item in filtrados[:3])
st.info(f"O ranking combina 40% do déficit de água e 60% do déficit de esgoto. Maiores prioridades em {ano}: **{top}**.")
if criterio == "Menor cobertura de água":
    filtrados.sort(key=lambda item: item["Atendimento_Agua"])
elif criterio == "Menor cobertura de esgoto":
    filtrados.sort(key=lambda item: item["Atendimento_Esgoto"])
elif criterio == "Maior população sem saneamento":
    filtrados.sort(key=lambda item: -item["Pop_Sem_Saneamento_Milhoes"])
elif criterio == "Alfabética (UF)":
    filtrados.sort(key=lambda item: item["UF"])

col1, col2, col3 = st.columns(3)
col1.metric("Média de atendimento de água", f"{sum(item['Atendimento_Agua'] for item in filtrados) / len(filtrados):.1f}%")
col2.metric("Média de atendimento de esgoto", f"{sum(item['Atendimento_Esgoto'] for item in filtrados) / len(filtrados):.1f}%")
col3.metric("População sem saneamento", f"{sum(item['Pop_Sem_Saneamento_Milhoes'] for item in filtrados):.2f} M")
st.caption("Médias simples dos registros exibidos. Lotes complementares podem repetir uma UF e ano; nesses casos, o total populacional pode contar a mesma população mais de uma vez.")
st.subheader("Cobertura por UF")
st.bar_chart([
    {"Registro": f"{index + 1} · {item['Sigla']} ({item['Origem']})", "Água (%)": item["Atendimento_Agua"], "Esgoto (%)": item["Atendimento_Esgoto"]}
    for index, item in enumerate(filtrados)
], x="Registro", y=["Água (%)", "Esgoto (%)"])
st.dataframe(filtrados, width="stretch", hide_index=True)
st.download_button("Baixar CSV filtrado", data=csv_bytes(filtrados), file_name="saneamento_filtrado.csv", mime="text/csv")
st.caption(f"Fontes oficiais declaradas: {', '.join(fontes) or 'não informadas'}. Complementares: importação via API.")
