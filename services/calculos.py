"""Funções financeiras puras (sem I/O)."""
from dataclasses import dataclass

from exceptions import InvalidInputError


@dataclass(frozen=True)
class ResultadoJuros:
    montante: float
    total_investido: float
    juros: float
    taxa_mensal_efetiva: float


def taxa_anual_para_mensal(taxa_aa_pct: float) -> float:
    """Taxa equivalente composta: (1 + a)^(1/12) - 1, em %."""
    return ((1 + taxa_aa_pct / 100) ** (1 / 12) - 1) * 100


def juros_compostos(capital: float, taxa_pct: float, meses: int,
                    tipo_taxa: str = "mensal", aporte_mensal: float = 0.0) -> ResultadoJuros:
    """Montante = C*(1+i)^n + PMT*((1+i)^n - 1)/i; com i == 0 os aportes apenas se somam."""
    if capital < 0:
        raise InvalidInputError("O capital não pode ser negativo.")
    if aporte_mensal < 0:
        raise InvalidInputError("O aporte mensal não pode ser negativo.")
    if int(meses) != meses or meses <= 0:
        raise InvalidInputError("O prazo deve ser um número inteiro de meses maior que zero.")
    if taxa_pct <= -100:
        raise InvalidInputError("A taxa deve ser maior que -100%.")
    if tipo_taxa not in ("mensal", "anual"):
        raise InvalidInputError("tipo_taxa deve ser 'mensal' ou 'anual'.")
    meses = int(meses)
    taxa_mensal = taxa_anual_para_mensal(taxa_pct) if tipo_taxa == "anual" else taxa_pct
    i = taxa_mensal / 100
    fator = (1 + i) ** meses
    montante = capital * fator
    montante += aporte_mensal * meses if i == 0 else aporte_mensal * (fator - 1) / i
    total = capital + aporte_mensal * meses
    return ResultadoJuros(round(montante, 2), round(total, 2),
                          round(montante - total, 2), round(taxa_mensal, 4))


def converter(valor: float, taxa_cambio: float, direcao: str) -> float:
    """Converte entre BRL e moeda estrangeira; taxa_cambio = valor em BRL de 1 unidade da moeda."""
    if valor < 0:
        raise InvalidInputError("O valor não pode ser negativo.")
    if taxa_cambio <= 0:
        raise InvalidInputError("Taxa de câmbio inválida.")
    if direcao == "brl_para_moeda":
        return valor / taxa_cambio
    if direcao == "moeda_para_brl":
        return valor * taxa_cambio
    raise InvalidInputError("direcao deve ser 'brl_para_moeda' ou 'moeda_para_brl'.")
