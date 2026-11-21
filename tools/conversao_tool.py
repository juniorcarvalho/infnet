from typing import Literal, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from exceptions import ExternalServiceError, InvalidInputError
from services.calculos import converter
from services.cotacao_client import obter_cotacao
from tools.formatacao import brl, num


class ConversaoInput(BaseModel):
    valor: float = Field(description="Valor a converter")
    moeda: str = Field(description="Código ISO da moeda estrangeira, ex.: USD, EUR")
    direcao: Literal["brl_para_moeda", "moeda_para_brl"] = Field(
        description="'brl_para_moeda' converte reais para a moeda; 'moeda_para_brl' o inverso")


class ConversaoTool(BaseTool):
    name: str = "converter_moeda"
    description: str = (
        "Converte um valor entre reais e outra moeda usando a cotação atual. "
        "Use SEMPRE esta ferramenta para converter valores; não divida nem multiplique você mesmo. "
        "Para apenas saber a cotação, use consultar_cotacao."
    )
    args_schema: Type[BaseModel] = ConversaoInput

    def _run(self, valor: float, moeda: str, direcao: str) -> str:
        try:
            c = obter_cotacao(moeda)
            res = converter(valor, c.valor_brl, direcao)
        except (InvalidInputError, ExternalServiceError) as e:
            return f"ERRO: {e}"
        if direcao == "brl_para_moeda":
            casas = 2 if res >= 1 else 8  # moedas caras (ex.: BTC) precisam de mais casas
            return f"{brl(valor)} = {num(res, casas)} {c.moeda} (cotação {num(c.valor_brl, 4)}, {c.data_hora})"
        return f"{num(valor)} {c.moeda} = {brl(res)} (cotação {num(c.valor_brl, 4)}, {c.data_hora})"
