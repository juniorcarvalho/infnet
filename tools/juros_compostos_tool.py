from typing import Literal, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from exceptions import InvalidInputError
from services.calculos import juros_compostos
from tools.formatacao import brl, num


class JurosInput(BaseModel):
    capital: float = Field(description="Valor inicial investido em reais")
    taxa_percentual: float = Field(description="Taxa de juros em %, ex.: 1 para 1%")
    meses: int = Field(description="Prazo em meses (inteiro)")
    tipo_taxa: Literal["mensal", "anual"] = Field(description="Se a taxa é 'mensal' ou 'anual'")
    aporte_mensal: float = Field(default=0, description="Aporte mensal em reais (opcional)")


class JurosCompostosTool(BaseTool):
    name: str = "calcular_juros_compostos"
    description: str = (
        "Calcula o montante de um investimento com juros compostos, com aportes mensais opcionais. "
        "Para taxa anual (ex.: CDI, Selic) passe o valor original com tipo_taxa='anual', sem converter para mensal. Sempre use esta ferramenta para cálculos; não busca taxas (use consultar_taxa_juros para isso)."
    )
    args_schema: Type[BaseModel] = JurosInput

    def _run(self, capital: float, taxa_percentual: float, meses: int,
             tipo_taxa: str, aporte_mensal: float = 0) -> str:
        try:
            r = juros_compostos(capital, taxa_percentual, meses, tipo_taxa, aporte_mensal)
        except InvalidInputError as e:
            return f"ERRO: {e}"
        return (f"Montante final: {brl(r.montante)}; total investido: {brl(r.total_investido)}; "
                f"juros: {brl(r.juros)}; taxa mensal efetiva: {num(r.taxa_mensal_efetiva, 4)}%")
