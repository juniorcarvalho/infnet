from typing import Literal, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from exceptions import ExternalServiceError, InvalidInputError
from services.bcb_client import obter_taxa
from tools.formatacao import num


class TaxaInput(BaseModel):
    indicador: Literal["selic", "cdi"] = Field(description="Indicador: 'selic' ou 'cdi'")


class TaxaJurosTool(BaseTool):
    name: str = "consultar_taxa_juros"
    description: str = (
        "Consulta a taxa Selic (meta) ou CDI atual, em % ao ano, no Banco Central. "
        "Não use para cotação de moedas nem para calcular rendimento."
    )
    args_schema: Type[BaseModel] = TaxaInput

    def _run(self, indicador: str) -> str:
        try:
            t = obter_taxa(indicador)
        except (InvalidInputError, ExternalServiceError) as e:
            return f"ERRO: {e}"
        return f"{t.indicador.upper()}: {num(t.percentual_ao_ano)}% ao ano (data: {t.data})"
