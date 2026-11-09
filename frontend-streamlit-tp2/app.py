"""Dashboard dos exercícios de visualização da COVID-19 em 2021."""

import csv
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import seaborn as sns
import streamlit as st
import altair as alt


PASTA_PROJETO = Path(__file__).parent
ARQUIVOS = [
    PASTA_PROJETO / "HIST_PAINEL_COVIDBR_2021_Parte1_05set2025.csv",
    PASTA_PROJETO / "HIST_PAINEL_COVIDBR_2021_Parte2_05set2025.csv",
]
LATITUDE_ZONA_MATA = -(21 + 7 / 60 + 12 / 3600)
LONGITUDE_ZONA_MATA = -(42 + 56 / 60 + 34 / 3600)
LATITUDE_VICOSA = -(20 + 45 / 60 + 14 / 3600)
LONGITUDE_VICOSA = -(42 + 52 / 60 + 54 / 3600)
COORDENADAS_ZONA_MATA = {
    "Juiz de Fora": (-21.7609533, -43.3501129),
    "Muriaé": (-21.1313485, -42.3628918),
    "Ubá": (-21.1200000, -42.9427770),
    "Viçosa": (-20.7538586, -42.8815888),
    "Cataguases": (-21.3874260, -42.6957219),
    "Leopoldina": (-21.5314282, -42.6403534),
    "Manhuaçu": (-20.2574434, -42.0340769),
    "Ponte Nova": (-20.4164353, -42.9087800),
    "Carangola": (-20.7336380, -42.0299412),
    "Além Paraíba": (-21.8760576, -42.6810473),
}
CAMPOS_NUMERICOS = (
    "coduf", "codmun", "codRegiaoSaude", "semanaEpi", "populacaoTCU2019",
    "casosAcumulado", "casosNovos", "obitosAcumulado", "obitosNovos",
    "Recuperadosnovos", "emAcompanhamentoNovos",
)


def numero(valor):
    """Converte um campo do CSV, deixando vazio como None."""
    if valor is None or valor.strip() == "":
        return None
    try:
        return int(float(valor))
    except ValueError:
        return None


@st.cache_data(show_spinner="Carregando os CSVs de 2021...")
def carregar_dados():
    """Lê e concatena as duas partes do arquivo"""
    registros = []
    for caminho in ARQUIVOS:
        with caminho.open("r", encoding="utf-8", newline="") as arquivo:
            leitor = csv.DictReader(arquivo, delimiter=";")
            for linha in leitor:
                registro = dict(linha)
                registro["data"] = datetime.strptime(linha["data"], "%Y-%m-%d").date()
                for campo in CAMPOS_NUMERICOS:
                    registro[campo] = numero(linha.get(campo, ""))
                registros.append(registro)
    return registros


def filtrar_dados(registros, ano=2021, estado=None, regiao=None, nivel=None):
    resultado = []
    for registro in registros:
        if registro["data"].year != ano:
            continue
        if estado is not None and registro["estado"] != estado:
            continue
        if regiao is not None and registro["regiao"] != regiao:
            continue
        municipio = registro["municipio"]
        eh_brasil = registro["regiao"] == "Brasil" and not registro["estado"] and not municipio
        eh_estado = bool(registro["estado"]) and not municipio and registro["codmun"] is None
        eh_municipio = bool(municipio)
        if nivel == "brasil" and not eh_brasil:
            continue
        if nivel == "estado" and not eh_estado:
            continue
        if nivel == "municipio" and not eh_municipio:
            continue
        if nivel == "regiao" and (registro["estado"] or municipio):
            continue
        resultado.append(registro)
    return resultado


def agrupar_por_semana(registros, chaves=(), somar=("casosNovos", "obitosNovos")):
    grupos = {}
    for registro in sorted(registros, key=lambda item: item["data"]):
        chave = tuple(registro[campo] for campo in chaves) + (registro["semanaEpi"],)
        if chave not in grupos:
            grupos[chave] = {campo: 0 for campo in somar}
            grupos[chave].update({campo: registro.get(campo) for campo in (
                "casosAcumulado", "obitosAcumulado", "populacaoTCU2019", "data"
            )})
            for campo in chaves:
                grupos[chave][campo] = registro[campo]
            grupos[chave]["semanaEpi"] = registro["semanaEpi"]
        for campo in somar:
            grupos[chave][campo] += registro.get(campo) or 0
        for campo in ("casosAcumulado", "obitosAcumulado", "populacaoTCU2019", "data"):
            if registro.get(campo) is not None:
                grupos[chave][campo] = registro[campo]
    return sorted(grupos.values(), key=lambda item: tuple(item.get(campo) or "" for campo in chaves) + (item["semanaEpi"] or 0,))


def agrupar_por_local(registros, campo_local="estado"):
    locais = {}
    for registro in sorted(registros, key=lambda item: item["data"]):
        local = registro.get(campo_local) or "Sem informação"
        locais[local] = registro
    return list(locais.values())


def quadro(registros):
    return pd.DataFrame(registros)


def mostrar_explicacao(texto):
    st.caption(texto)


st.set_page_config(page_title="COVID-19 Brasil 2021", layout="wide")
st.title("Dashboard de visualizações da COVID-19")
st.write("Dados do Ministério da Saúde, recorte de 01/01/2021 a 31/12/2021.")
st.write("Desenvolvimento Front-End com Python (com Streamlit) [26E3_1]")
st.write("TP2")
st.write("José Adolfo Fortes de Carvalho Júnior")

dados = carregar_dados()

# Exercício 1: Explique a importância da visualização de dados no contexto de uma pandemia.
st.header("1. Importância da visualização")
st.write("Visualizações tornam tendências de transmissão e mortalidade mais fáceis de acompanhar. Elas permitem comparar territórios, identificar aumentos e apoiar decisões de gestores de saúde e da população, como a distribuição de recursos e a adoção de medidas preventivas.")

# Exercício 2: Crie um gráfico de barras em Streamlit com casos novos por semana em um estado.
st.header("2. Casos novos por semana: Minas Gerais")
mg = filtrar_dados(dados, estado="MG", nivel="estado")
mg_semanal = quadro(agrupar_por_semana(mg))
if not mg_semanal.empty:
    st.bar_chart(mg_semanal.set_index("semanaEpi")["casosNovos"])
mostrar_explicacao("Minas Gerais foi escolhido porque é o estado de minha residência.")

# Exercício 3: Crie um gráfico de linha dos óbitos acumulados por semana para o Brasil.
st.header("3. Óbitos acumulados no Brasil")
brasil = quadro(agrupar_por_semana(filtrar_dados(dados, nivel="brasil"), somar=()))
if not brasil.empty:
    st.line_chart(brasil.set_index("semanaEpi")["obitosAcumulado"])
mostrar_explicacao("A inclinação mostra a velocidade de crescimento do total acumulado.")

# Exercício 4: Crie um gráfico de área comparando casos acumulados em três estados.
st.header("4. Casos acumulados em três estados")
estados = ["MG", "RJ", "SP"]
comparacao = quadro(agrupar_por_semana(filtrar_dados(dados, nivel="estado", estado=None), chaves=("estado",), somar=()))
comparacao = comparacao[comparacao["estado"].isin(estados)] if not comparacao.empty else comparacao
if not comparacao.empty:
    st.area_chart(comparacao.pivot(index="semanaEpi", columns="estado", values="casosAcumulado"))
mostrar_explicacao("Minas Gerais é comparado com Rio de Janeiro e São Paulo.")

# Exercício 5: Crie um mapa com st.map dos casos acumulados por município de um estado.
st.header("5. Distribuição municipal em Minas Gerais")
municipios = quadro(filtrar_dados(dados, estado="MG", nivel="municipio"))
municipios = municipios[municipios["municipio"].isin(COORDENADAS_ZONA_MATA)]
if municipios.empty:
    st.info("Os municípios selecionados não foram encontrados no recorte de 2021.")
else:
    municipios = municipios.sort_values("data").drop_duplicates("codmun", keep="last")
    municipios[["latitude", "longitude"]] = municipios["municipio"].map(COORDENADAS_ZONA_MATA).apply(pd.Series)
    st.map(municipios[["latitude", "longitude", "casosAcumulado"]].dropna(), latitude="latitude", longitude="longitude", size="casosAcumulado")    
mostrar_explicacao("Um mapa municipal ajuda a localizar concentrações territoriais e orientar a análise de desigualdades entre municípios.")

# Exercício 6: Use Matplotlib para comparar casos novos e óbitos novos por estado na semana mais recente.
st.header("6. Casos e óbitos novos na semana mais recente")
estaduais = filtrar_dados(dados, nivel="estado")
semana_final = max(r["semanaEpi"] for r in estaduais if r["semanaEpi"] is not None)
semana = quadro([r for r in estaduais if r["semanaEpi"] == semana_final])
if not semana.empty:
    figura, eixo = plt.subplots(figsize=(12, 5))
    posicoes = range(len(semana))
    eixo.bar([p - 0.2 for p in posicoes], semana["casosNovos"], width=0.4, label="Casos novos")
    eixo.bar([p + 0.2 for p in posicoes], semana["obitosNovos"], width=0.4, label="Óbitos novos")
    eixo.set_xticks(list(posicoes), semana["estado"], rotation=45)
    eixo.set_ylabel("Quantidade")
    eixo.set_title(f"Semana epidemiológica {semana_final}")
    eixo.legend()
    st.pyplot(figura)
    plt.close(figura)


# Exercício 7: Use Seaborn para comparar a distribuição de casos novos por semana entre três regiões.
st.header("7. Distribuição regional de casos novos")
regioes_box = quadro([r for r in estaduais if r["regiao"] in ["Norte", "Nordeste", "Sudeste"]])
if not regioes_box.empty:
    figura, eixo = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=regioes_box, x="regiao", y="casosNovos", ax=eixo)
    eixo.set_xlabel("Região")
    eixo.set_ylabel("Casos novos por estado")
    st.pyplot(figura)
    plt.close(figura)
mostrar_explicacao("A linha dentro da caixa representa a mediana, a caixa mostra a dispersão central ")

# Exercício 8: Crie um gráfico de área em Altair para os casos novos de uma região.
st.header("8. Área em Altair: região Sudeste")
sudeste = quadro(agrupar_por_semana([r for r in estaduais if r["regiao"] == "Sudeste"], somar=("casosNovos",)))
chart = alt.Chart(sudeste).mark_area(opacity=0.7).encode(x="semanaEpi:Q", y="casosNovos:Q", tooltip=["semanaEpi", "casosNovos"])
st.altair_chart(chart, use_container_width=True)
mostrar_explicacao("O Sudeste foi escolhido por estar disponível nos dados e por reunir grande volume populacional")

# Exercício 9: Desenvolva um heatmap em Altair com as correlações disponíveis em Minas Gerais.
st.header("9. Correlação em Minas Gerais")
mg_correlacao = quadro(agrupar_por_semana(mg, somar=("casosNovos", "obitosNovos")))
colunas_correlacao = [c for c in ["casosNovos", "obitosNovos", "leitos hospitalares ocupados"] if c in mg_correlacao]
matriz = mg_correlacao[colunas_correlacao].corr()
pares = [{"linha": linha, "coluna": coluna, "valor": matriz.loc[linha, coluna]} for linha in matriz.index for coluna in matriz.columns]
chart = alt.Chart(pd.DataFrame(pares)).mark_rect().encode(x="coluna:N", y="linha:N", color="valor:Q", tooltip=["linha", "coluna", "valor"])
st.altair_chart(chart, use_container_width=True)

# Exercício 10: Crie um gráfico de pizza com a distribuição percentual por região.
st.header("10. Distribuição regional dos casos acumulados")
ultima_data = max(r["data"] for r in dados)
ultimos_estados = quadro([r for r in estaduais if r["data"] == ultima_data])
regiao_pizza = ultimos_estados.groupby("regiao", as_index=False)["casosAcumulado"].sum() if not ultimos_estados.empty else pd.DataFrame()
if not regiao_pizza.empty:
    grafico = px.pie(regiao_pizza, names="regiao", values="casosAcumulado", title="Casos acumulados por região")
    grafico.update_traces(textinfo="label+value+percent")
    st.plotly_chart(grafico, use_container_width=True)
mostrar_explicacao("Cada estado entra uma vez na soma mais recente")

# Exercício 11: Crie subplots em Plotly comparando casos e óbitos novos em duas regiões.
st.header("11. Subplots por região")
regioes_subplot = ["Sudeste", "Nordeste"]
dados_subplot = quadro(agrupar_por_semana([r for r in estaduais if r["regiao"] in regioes_subplot], chaves=("regiao",)))
if not dados_subplot.empty:
    figura = go.Figure()
    for indice, regiao in enumerate(regioes_subplot, start=1):
        parte = dados_subplot[dados_subplot["regiao"] == regiao]
        figura.add_trace(go.Bar(x=parte["semanaEpi"], y=parte["casosNovos"], name=f"Casos - {regiao}", legendgroup=regiao, xaxis=f"x{indice}", yaxis=f"y{indice}"))
        figura.add_trace(go.Bar(x=parte["semanaEpi"], y=parte["obitosNovos"], name=f"Óbitos - {regiao}", legendgroup=regiao, xaxis=f"x{indice}", yaxis=f"y{indice}"))
    figura.update_layout(barmode="group", grid={"rows": 1, "columns": 2, "pattern": "independent"}, title="Casos e óbitos novos por semana")
    st.plotly_chart(figura, use_container_width=True)
mostrar_explicacao("As regiões podem diferir em volume e no momento dos picos")

# Exercício 12: Utilize PyDeck para mapear casos acumulados ajustados pela população por município.
st.header("12. Mapa PyDeck do Sudeste")
municipios_sudeste = quadro(filtrar_dados(dados, regiao="Sudeste", nivel="municipio"))
municipios_sudeste = municipios_sudeste.sort_values("data").drop_duplicates("codmun", keep="last")
municipios_sudeste = municipios_sudeste[municipios_sudeste["municipio"].isin(COORDENADAS_ZONA_MATA)]
if not municipios_sudeste.empty:
    municipios_sudeste["casosPorHabitante"] = municipios_sudeste["casosAcumulado"] / municipios_sudeste["populacaoTCU2019"].replace(0, pd.NA)
    municipios_sudeste[["latitude", "longitude"]] = municipios_sudeste["municipio"].map(COORDENADAS_ZONA_MATA).apply(pd.Series)
    municipios_sudeste = municipios_sudeste.dropna(subset=["casosPorHabitante", "latitude", "longitude"])
    camada = pdk.Layer("ScatterplotLayer", data=municipios_sudeste, get_position="[longitude, latitude]", get_radius="casosPorHabitante * 100000", get_fill_color="[200, 30, 30, 180]", pickable=True)
    st.pydeck_chart(pdk.Deck(layers=[camada], initial_view_state=pdk.ViewState(latitude=-21, longitude=-42.6, zoom=7), tooltip={"text": "{municipio}\nCasos ajustados: {casosPorHabitante}"}))
st.info("O mapa mostra os 10 municípios selecionados da Zona da Mata Mineira. O tamanho representa casos acumulados ajustados pela população.")
st.caption("Coordenadas consultadas no OpenStreetMap/Nominatim")
mostrar_explicacao("Casos ajustados pela população ajudam a comparar municípios de tamanhos diferentes")
