"""Cliente HTTP do Streamlit com configuração e tratamento de falhas centralizados."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class APIError(RuntimeError):
    """Falha de conexão, contrato ou validação na API."""


def _requisicao(method: str, registros=None, filtros=None):
    base = os.getenv("SANEAMENTO_API_URL", "http://127.0.0.1:8000").rstrip("/")
    url = f"{base}/dados"
    if filtros:
        url += "?" + urlencode({key: value for key, value in filtros.items() if value is not None})
    body = None if registros is None else json.dumps(registros, allow_nan=False).encode("utf-8")
    try:
        request = Request(url, data=body, method=method, headers={"Accept": "application/json", "Content-Type": "application/json"})
        with urlopen(request, timeout=15) as response:
            payload = json.load(response)
        if not isinstance(payload, dict) or not isinstance(payload.get("registros"), list) or not isinstance(payload.get("fontes"), list):
            raise ValueError("Resposta fora do contrato esperado.")
        return payload
    except HTTPError as exc:
        try:
            erro = json.loads(exc.read())
            detalhe = erro.get("detail", "Erro sem detalhes.") if isinstance(erro, dict) else "Erro sem detalhes."
        except (ValueError, UnicodeError):
            detalhe = "Erro sem detalhes."
        raise APIError(f"API retornou HTTP {exc.code}: {detalhe}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise APIError("API indisponível. Verifique se o serviço FastAPI está em execução.") from exc
    except (ValueError, UnicodeError) as exc:
        raise APIError("A API retornou uma resposta inválida.") from exc


def consultar_dados(ano=None, regiao=None):
    return _requisicao("GET", filtros={"ano": ano, "regiao": regiao})


def enviar_dados(registros):
    return _requisicao("POST", registros=registros)
