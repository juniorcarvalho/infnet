from langchain_core.messages import AIMessage

from agent import build_agent, perguntar
from tests.fakes import FakeToolChatModel
from tools import cotacao_tool, get_tools
from services.cotacao_client import Cotacao


def _agent(msgs, monkeypatch):
    monkeypatch.setattr(cotacao_tool, "obter_cotacao",
                        lambda m: Cotacao("USD", "Dólar", 5.0, "2026-11-21 10:00:00"))
    return build_agent(llm=FakeToolChatModel(messages=iter(msgs)), tools=get_tools())


def test_react(monkeypatch):
    agent = _agent([
        AIMessage(content="", tool_calls=[{"name": "consultar_cotacao", "args": {"moeda": "USD"}, "id": "c1"}]),
        AIMessage(content="O dólar está R$ 5,00."),
    ], monkeypatch)
    r = perguntar(agent, "Quanto está o dólar?", "t1")
    assert r.texto == "O dólar está R$ 5,00."
    assert len(r.passos) == 1
    assert r.passos[0].acao == "consultar_cotacao"
    assert r.passos[0].entrada == {"moeda": "USD"}
    assert "R$ 5,0000" in r.passos[0].observacao


def test_memoria(monkeypatch):
    agent = _agent([AIMessage(content="Oi!"), AIMessage(content="Lembro de você.")], monkeypatch)
    perguntar(agent, "Tenho R$ 2.000.", "A")
    perguntar(agent, "E agora?", "A")
    cfg = lambda t: {"configurable": {"thread_id": t}}
    assert len(agent.get_state(cfg("A")).values["messages"]) == 4
    assert not agent.get_state(cfg("B")).values
