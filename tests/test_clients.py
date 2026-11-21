import httpx
import pytest

from exceptions import ExternalServiceError, InvalidInputError
from services import bcb_client, cotacao_client


def _resp(status=200, json=None, text=None):
    req = httpx.Request("GET", "http://x")
    if text is not None:
        return httpx.Response(status, text=text, request=req)
    return httpx.Response(status, json=json, request=req)


def _patch(monkeypatch, module, resp=None, exc=None):
    def fake(*a, **k):
        if exc:
            raise exc
        return resp
    monkeypatch.setattr(module.httpx, "get", fake)


def test_cotacao_ok(monkeypatch):
    _patch(monkeypatch, cotacao_client, _resp(json={"USDBRL": {
        "bid": "5.9488", "name": "Dólar", "create_date": "2026-11-21 10:00:00"}}))
    c = cotacao_client.obter_cotacao("usd")
    assert c.moeda == "USD" and c.valor_brl == 5.9488


def test_cotacao_timeout(monkeypatch):
    _patch(monkeypatch, cotacao_client, exc=httpx.TimeoutException("t"))
    with pytest.raises(ExternalServiceError):
        cotacao_client.obter_cotacao("USD")


def test_cotacao_404(monkeypatch):
    _patch(monkeypatch, cotacao_client, _resp(404, json={}))
    with pytest.raises(InvalidInputError):
        cotacao_client.obter_cotacao("XYZ")


def test_cotacao_json_inesperado(monkeypatch):
    _patch(monkeypatch, cotacao_client, _resp(text="<html>"))
    with pytest.raises(ExternalServiceError):
        cotacao_client.obter_cotacao("USD")


def test_cotacao_codigo_invalido():
    with pytest.raises(InvalidInputError):
        cotacao_client.obter_cotacao("US1")


def test_taxa_ok(monkeypatch):
    _patch(monkeypatch, bcb_client, _resp(json=[{"data": "21/11/2026", "valor": "13.75"}]))
    t = bcb_client.obter_taxa("selic")
    assert t.percentual_ao_ano == 13.75 and t.data == "21/11/2026"


def test_taxa_erros(monkeypatch):
    with pytest.raises(InvalidInputError):
        bcb_client.obter_taxa("poupanca")
    _patch(monkeypatch, bcb_client, exc=httpx.ConnectError("x"))
    with pytest.raises(ExternalServiceError):
        bcb_client.obter_taxa("cdi")
    _patch(monkeypatch, bcb_client, _resp(500, json={}))
    with pytest.raises(ExternalServiceError):
        bcb_client.obter_taxa("cdi")
    _patch(monkeypatch, bcb_client, _resp(json=[]))
    with pytest.raises(ExternalServiceError):
        bcb_client.obter_taxa("cdi")


def test_taxa_ignora_data_futura(monkeypatch):
    _patch(monkeypatch, bcb_client, _resp(json=[
        {"data": "01/01/2020", "valor": "10.00"}, {"data": "09/12/2999", "valor": "99.0"}]))
    assert bcb_client.obter_taxa("selic").percentual_ao_ano == 10.0


def test_taxa_timeout(monkeypatch):
    _patch(monkeypatch, bcb_client, exc=httpx.TimeoutException("t"))
    with pytest.raises(ExternalServiceError):
        bcb_client.obter_taxa("selic")


def test_taxa_json_inesperado(monkeypatch):
    _patch(monkeypatch, bcb_client, _resp(text="<html>"))
    with pytest.raises(ExternalServiceError):
        bcb_client.obter_taxa("selic")


def test_taxa_somente_datas_futuras(monkeypatch):
    _patch(monkeypatch, bcb_client, _resp(json=[{"data": "09/12/2999", "valor": "99.0"}]))
    with pytest.raises(ExternalServiceError):
        bcb_client.obter_taxa("selic")


def test_cotacao_200_sem_chave(monkeypatch):
    _patch(monkeypatch, cotacao_client, _resp(json={"EURBRL": {}}))
    with pytest.raises(InvalidInputError):
        cotacao_client.obter_cotacao("USD")
