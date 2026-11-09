"""API local de consulta e importação de indicadores consolidados."""

import logging
from typing import Annotated, Literal

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.api_data_access import adicionar_dados_complementares, carregar_dados_complementares
from src.data_access import carregar_dados_processados
from src.data_processing import calcular_prioridade, normalizar_registros

logger = logging.getLogger(__name__)
Regiao = Literal["Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"]


class RegistroEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)

    Ano: int = Field(ge=1, le=9999, strict=True)
    UF: str = Field(min_length=1)
    Sigla: str = Field(min_length=2, max_length=2)
    Regiao: Regiao
    Atendimento_Agua: float = Field(ge=0, le=100, strict=True)
    Atendimento_Esgoto: float = Field(ge=0, le=100, strict=True)
    Pop_Sem_Saneamento_Milhoes: float = Field(ge=0, strict=True)

    @model_validator(mode="after")
    def validar_registro(self):
        normalizado = normalizar_registros([self.model_dump()])[0]
        self.Sigla = normalizado["Sigla"]
        return self


class RegistroSaida(RegistroEntrada):
    Deficit_Agua: float
    Deficit_Esgoto: float
    Score_Prioridade: float
    Origem: Literal["oficial", "complementar"]
    Importado_Em: str | None = None


class DadosResposta(BaseModel):
    fontes: list[str]
    registros: list[RegistroSaida]


app = FastAPI(title="Saneamento em Foco", version="3.0.0", description="Consulta de indicadores urbanos e importação complementar, com proveniência explícita.")


@app.exception_handler(RequestValidationError)
async def entrada_invalida(request, exc):
    # Não ecoar valores como NaN/Infinity, que não podem ser serializados em JSON.
    detalhes = [
        {campo: erro[campo] for campo in ("loc", "msg", "type")}
        for erro in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": detalhes})


@app.get("/dados", response_model=DadosResposta, responses={503: {"description": "Cache oficial ausente"}, 500: {"description": "Falha de leitura ou formato inválido"}})
def consultar_dados(
    ano: Annotated[int | None, Query(ge=1, le=9999)] = None,
    regiao: Regiao | None = None,
):
    """Consulta dados oficiais e complementares sem executar coleta externa."""
    try:
        payload = carregar_dados_processados()
        fontes = payload.get("fontes", [])
        if not isinstance(fontes, list) or any(not isinstance(fonte, str) for fonte in fontes):
            raise ValueError("Fontes inválidas no cache oficial.")
        oficiais = calcular_prioridade(payload["registros"])
        for item in oficiais:
            item["Origem"] = "oficial"
            item.pop("Importado_Em", None)
        complementares = carregar_dados_complementares()
        registros = calcular_prioridade(oficiais + complementares)
        resposta = DadosResposta(fontes=fontes, registros=registros)
    except FileNotFoundError as exc:
        raise HTTPException(503, "Cache oficial ausente. Execute a preparação dos dados.") from exc
    except (OSError, ValueError) as exc:
        logger.exception("Falha ao ler dados de saneamento")
        raise HTTPException(500, "Não foi possível ler os arquivos de dados; verifique formato e permissões.") from exc
    resposta.registros = [item for item in resposta.registros if (ano is None or item.Ano == ano) and (regiao is None or item.Regiao == regiao)]
    return resposta


@app.post("/dados", status_code=201, response_model=DadosResposta, responses={500: {"description": "Falha de leitura ou gravação complementar"}})
def importar_dados(registros: Annotated[list[RegistroEntrada], Body(min_length=1)]):
    """Acrescenta um lote complementar; repetições geram novos registros."""
    try:
        novos = adicionar_dados_complementares([item.model_dump() for item in registros])
    except (OSError, ValueError) as exc:
        logger.exception("Falha ao persistir dados complementares")
        raise HTTPException(500, "Não foi possível persistir o lote complementar; verifique formato e permissões.") from exc
    return {"fontes": ["Importação complementar via API"], "registros": novos}
