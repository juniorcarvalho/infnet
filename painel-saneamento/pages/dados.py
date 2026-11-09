import streamlit as st

from src.api_client import APIError, enviar_dados
from src.data_processing import REGIAO_POR_UF
from src.ui_helpers import carregar_registros, csv_bytes, ler_upload

st.header("Consulta e importação")
st.subheader("Adicionar dados complementares")
st.write("Envie CSV UTF-8 separado por vírgulas, consolidado por UF e ano ou municipal SNIS. Os registros aceitos são persistidos como complementares.")
st.code("Ano,UF,Sigla,Regiao,Atendimento_Agua,Atendimento_Esgoto,Pop_Sem_Saneamento_Milhoes\n2021,Acre,AC,Norte,75,30,0.2", language="text")
uploaded = st.file_uploader("CSV complementar", type=["csv"])
if uploaded is not None:
    try:
        registros_upload = ler_upload(uploaded)
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.dataframe(registros_upload[:1000], width="stretch", hide_index=True)
        st.caption(f"{len(registros_upload)} registros prontos. Cada envio acrescenta um novo lote, inclusive se o CSV já tiver sido enviado.")
        if st.button("Enviar à API", type="primary"):
            try:
                resposta = enviar_dados(registros_upload)
            except APIError as exc:
                st.error(str(exc))
            else:
                st.success(f"{len(resposta['registros'])} registros complementares persistidos.")

st.subheader("Consultar e exportar")
ano_texto = st.text_input("Ano (vazio para todos)")
regiao = st.selectbox("Região", ["Todas"] + sorted(set(REGIAO_POR_UF.values())))
ano = None
if ano_texto.strip():
    try:
        ano = int(ano_texto)
        if not 1 <= ano <= 9999:
            raise ValueError
    except ValueError:
        st.error("Informe um ano inteiro entre 1 e 9999.")
        st.stop()
try:
    registros, fontes = carregar_registros(ano, None if regiao == "Todas" else regiao)
except APIError as exc:
    st.error(str(exc))
else:
    st.caption(f"{len(registros)} registros. A coluna Origem distingue dados oficiais e complementares.")
    if registros:
        st.dataframe(registros, width="stretch", hide_index=True)
        st.download_button("Baixar CSV da consulta", data=csv_bytes(registros), file_name="consulta_saneamento.csv", mime="text/csv")
    else:
        st.info("Nenhum registro atende aos filtros.")
