"""Cliente HTTP da AwesomeAPI (cotações em BRL)."""
import re
from dataclasses import dataclass

import httpx

from config import get_settings
from exceptions import ExternalServiceError, InvalidInputError

URL = "https://economia.awesomeapi.com.br/json/last/{moeda}-BRL"


@dataclass(frozen=True)
class Cotacao:
    moeda: str
    nome: str
    valor_brl: float
    data_hora: str


def obter_cotacao(moeda: str) -> Cotacao:
    moeda = (moeda or "").strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", moeda):
        raise InvalidInputError(f"Código de moeda inválido: '{moeda}'. Use 3 letras (ex.: USD).")
    try:
        resp = httpx.get(URL.format(moeda=moeda), timeout=get_settings().http_timeout)
    except httpx.HTTPError as e:  # inclui timeouts
        raise ExternalServiceError(f"Falha ao consultar a cotação: {e}") from e
    if resp.status_code == 404:
        raise InvalidInputError(f"Moeda não suportada: {moeda}")
    if resp.status_code != 200:
        raise ExternalServiceError(f"AwesomeAPI retornou HTTP {resp.status_code}")
    try:
        dados = resp.json()
    except ValueError as e:
        raise ExternalServiceError("Resposta inesperada da AwesomeAPI") from e
    item = dados.get(f"{moeda}BRL") if isinstance(dados, dict) else None
    if item is None:
        raise InvalidInputError(f"Moeda não suportada: {moeda}")
    try:
        return Cotacao(moeda, item["name"], float(item["bid"]), item["create_date"])
    except (KeyError, TypeError, ValueError) as e:
        raise ExternalServiceError("Resposta inesperada da AwesomeAPI") from e
