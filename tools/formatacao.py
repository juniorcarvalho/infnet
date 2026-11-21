"""Formatação pt-BR."""


def brl(valor: float) -> str:
    return f"R$ {num(valor)}"


def num(valor: float, casas: int = 2) -> str:
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
