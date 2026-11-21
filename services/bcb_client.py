"""Cliente HTTP do BCB SGS (Selic e CDI)."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import httpx

from config import get_settings
from exceptions import ExternalServiceError, InvalidInputError

SERIES = {"selic": 432, "cdi": 4389}
URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"


@dataclass(frozen=True)
class Taxa:
    indicador: str
    percentual_ao_ano: float
    data: str


def obter_taxa(indicador: str) -> Taxa:
    chave = (indicador or "").strip().lower()
    if chave not in SERIES:
        raise InvalidInputError(f"Indicador desconhecido: '{indicador}'. Use: {', '.join(SERIES)}.")
    hoje = date.today()
    params = {
        "formato": "json",
        "dataInicial": (hoje - timedelta(days=45)).strftime("%d/%m/%Y"),
        "dataFinal": hoje.strftime("%d/%m/%Y"),
    }
    try:
        resp = httpx.get(URL.format(codigo=SERIES[chave]), params=params, timeout=get_settings().http_timeout)
    except httpx.HTTPError as e:
        raise ExternalServiceError(f"Falha ao consultar o BCB: {e}") from e
    if resp.status_code != 200:
        raise ExternalServiceError(f"BCB retornou HTTP {resp.status_code}")
    try:
        itens = resp.json()
        # A série 432 contém datas futuras: a consulta limita a janela a hoje e filtra por segurança
        validos = [i for i in itens if datetime.strptime(i["data"], "%d/%m/%Y").date() <= hoje]
        if not validos:
            raise ExternalServiceError("BCB sem dados recentes")
        item = validos[-1]
        return Taxa(chave, float(item["valor"]), item["data"])
    except (ValueError, KeyError, IndexError, TypeError) as e:
        raise ExternalServiceError("Resposta inesperada do BCB") from e
