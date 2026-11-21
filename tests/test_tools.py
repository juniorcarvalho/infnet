from exceptions import ExternalServiceError
from services.bcb_client import Taxa
from services.cotacao_client import Cotacao
from tools import conversao_tool, cotacao_tool, get_tools, taxa_juros_tool
from tools.juros_compostos_tool import JurosCompostosTool

COT = Cotacao("USD", "Dólar", 5.0, "2026-11-21 10:00:00")


def test_get_tools():
    assert [t.name for t in get_tools()] == [
        "consultar_cotacao", "consultar_taxa_juros", "calcular_juros_compostos", "converter_moeda"]


def test_cotacao(monkeypatch):
    monkeypatch.setattr(cotacao_tool, "obter_cotacao", lambda m: COT)
    assert "R$ 5,0000" in cotacao_tool.CotacaoTool().invoke({"moeda": "USD"})


def test_taxa(monkeypatch):
    monkeypatch.setattr(taxa_juros_tool, "obter_taxa", lambda i: Taxa("selic", 13.75, "21/11/2026"))
    assert "13,75%" in taxa_juros_tool.TaxaJurosTool().invoke({"indicador": "selic"})


def test_juros():
    out = JurosCompostosTool().invoke(
        {"capital": 5000, "taxa_percentual": 1, "meses": 24, "tipo_taxa": "mensal"})
    assert "R$ 6.348,67" in out


def test_juros_invalido():
    out = JurosCompostosTool().invoke(
        {"capital": -5, "taxa_percentual": 1, "meses": 24, "tipo_taxa": "mensal"})
    assert out.startswith("ERRO:")


def test_conversao(monkeypatch):
    monkeypatch.setattr(conversao_tool, "obter_cotacao", lambda m: COT)
    out = conversao_tool.ConversaoTool().invoke(
        {"valor": 100, "moeda": "USD", "direcao": "brl_para_moeda"})
    assert "20,00 USD" in out


def test_erro_servico(monkeypatch):
    def boom(m):
        raise ExternalServiceError("fora do ar")
    monkeypatch.setattr(cotacao_tool, "obter_cotacao", boom)
    assert cotacao_tool.CotacaoTool().invoke({"moeda": "USD"}) == "ERRO: fora do ar"


def test_conversao_btc_casas_adicionais(monkeypatch):
    monkeypatch.setattr(conversao_tool, "obter_cotacao",
                        lambda m: Cotacao("BTC", "Bitcoin", 500000.0, "2026-11-21 10:00:00"))
    out = conversao_tool.ConversaoTool().invoke(
        {"valor": 1000, "moeda": "BTC", "direcao": "brl_para_moeda"})
    assert "0,00200000 BTC" in out
