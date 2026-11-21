from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from exceptions import ExternalServiceError, InvalidInputError
from services.cotacao_client import obter_cotacao
from tools.formatacao import num


class CotacaoInput(BaseModel):
    moeda: str = Field(description="Código ISO da moeda com 3 letras, ex.: USD, EUR, BTC")


class CotacaoTool(BaseTool):
    name: str = "consultar_cotacao"
    description: str = (
        "Consulta a cotação atual de uma moeda em reais (BRL). Use para saber quanto vale "
        "dólar, euro, bitcoin etc. Não use para Selic/CDI. "
        "Não use para converter valores; para isso use converter_moeda."
    )
    args_schema: Type[BaseModel] = CotacaoInput

    def _run(self, moeda: str) -> str:
        try:
            c = obter_cotacao(moeda)
        except (InvalidInputError, ExternalServiceError) as e:
            return f"ERRO: {e}"
        return f"1 {c.moeda} ({c.nome}) = R$ {num(c.valor_brl, 4)} em {c.data_hora}"
