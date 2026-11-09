"""Leitura da API e conversão de CSV compartilhadas pelas páginas."""

import csv
import io

import streamlit as st

from src.api_client import consultar_dados
from src.data_access import carregar_municipios_web
from src.data_processing import REQUIRED_FIELDS, URBAN_CSV_FIELDS, consolidar_dados_urbanos, normalizar_registros

CONTRACT_FIELDS = ("Ano", "UF", "Sigla", "Regiao", "Atendimento_Agua", "Atendimento_Esgoto", "Pop_Sem_Saneamento_Milhoes")


def carregar_registros(ano=None, regiao=None):
    payload = consultar_dados(ano, regiao)
    return payload["registros"], payload["fontes"]


@st.cache_data
def carregar_referencia_municipios():
    return carregar_municipios_web()


def ler_upload(uploaded_file):
    if uploaded_file is None:
        return []
    try:
        reader = csv.DictReader(io.StringIO(uploaded_file.getvalue().decode("utf-8-sig")))
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("Cabeçalho CSV ausente ou com colunas duplicadas.")
        registros = list(reader)
    except UnicodeDecodeError as exc:
        raise ValueError("O CSV deve estar codificado em UTF-8.") from exc
    except csv.Error as exc:
        raise ValueError("Não foi possível interpretar o CSV.") from exc
    if not registros:
        raise ValueError("O CSV enviado não contém registros.")
    if any(None in item or any(value is None for value in item.values()) for item in registros):
        raise ValueError("CSV com linhas que não correspondem ao cabeçalho.")
    campos = set(registros[0])
    if (REQUIRED_FIELDS | {"Ano"}).issubset(campos):
        registros = normalizar_registros(registros)
    elif set(URBAN_CSV_FIELDS).issubset(campos):
        registros = normalizar_registros(consolidar_dados_urbanos(registros))
    else:
        raise ValueError("Envie as sete colunas consolidadas (incluindo Ano, Sigla e Pop_Sem_Saneamento_Milhoes) ou as seis colunas urbanas municipais SNIS.")
    if not registros:
        raise ValueError("O CSV não produziu registros urbanos válidos.")
    return [{field: item[field] for field in CONTRACT_FIELDS} for item in registros]


def csv_bytes(registros):
    if not registros:
        return b""
    buffer = io.StringIO()
    campos = list(dict.fromkeys(field for item in registros for field in item))
    writer = csv.DictWriter(buffer, fieldnames=campos)
    writer.writeheader()
    writer.writerows(registros)
    return buffer.getvalue().encode("utf-8-sig")
