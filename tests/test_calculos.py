import pytest

from exceptions import InvalidInputError
from services.calculos import converter, juros_compostos, taxa_anual_para_mensal


def test_juros_conhecido():
    r = juros_compostos(5000, 1, 24)
    assert r.montante == 6348.67
    assert r.total_investido == 5000
    assert r.juros == 1348.67


def test_taxa_zero():
    r = juros_compostos(1000, 0, 12, aporte_mensal=100)
    assert r.montante == 2200


def test_aporte_mensal():
    r = juros_compostos(0, 1, 12, aporte_mensal=100)
    assert r.montante == pytest.approx(1268.25, abs=0.01)
    assert r.total_investido == 1200


def test_anual_para_mensal():
    assert taxa_anual_para_mensal(12) == pytest.approx(0.9489, abs=1e-4)
    assert juros_compostos(1000, 12, 12, "anual").montante == 1120


@pytest.mark.parametrize("args", [(-1, 1, 12), (100, 1, 0), (100, 1, 1.5), (100, -100, 12)])
def test_invalidos(args):
    with pytest.raises(InvalidInputError):
        juros_compostos(*args)


def test_converter():
    assert converter(100, 5, "brl_para_moeda") == 20
    assert converter(100, 5, "moeda_para_brl") == 500
    with pytest.raises(InvalidInputError):
        converter(1, 5, "x")
