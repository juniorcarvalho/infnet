"""Agente ReAct: LLM + tools + memória (InMemorySaver)."""
from dataclasses import dataclass, field
from typing import Any

import openai
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from config import Settings, get_settings
from exceptions import ExternalServiceError
from tools import get_tools

SYSTEM_PROMPT = """Você é um assistente financeiro pessoal que responde em português do Brasil.
Regras:
- Nunca invente cotações, taxas ou resultados de cálculo: use sempre as ferramentas.
- Em perguntas de acompanhamento, reutilize no histórico os valores que o usuário omitiu (capital, taxa, prazo).
- Informe a data dos dados consultados (cotações, Selic, CDI), usando somente a data retornada pela ferramenta; nunca cite uma data que não veio de uma ferramenta.
- Se a taxa estiver em % ao ano (ex.: CDI, Selic), passe-a SEM converter, com tipo_taxa="anual" em calcular_juros_compostos; a conversão para mensal é feita pela ferramenta.
- Para converter um valor entre moedas use SEMPRE converter_moeda; nunca divida ou multiplique pela cotação você mesmo.
- Responda em texto simples, sem LaTeX nem fórmulas.
- Ao responder sobre rendimento, informe o montante final e os juros.
- Se uma ferramenta devolver "ERRO:", explique o problema ao usuário sem inventar valores.
- Para perguntas conceituais, responda diretamente, sem ferramentas.
- Lembre que suas respostas não são recomendação de investimento."""


@dataclass
class Passo:
    acao: str
    entrada: dict
    observacao: str = ""


@dataclass
class RespostaAgente:
    texto: str
    passos: list[Passo] = field(default_factory=list)


def build_llm(settings: Settings) -> ChatOpenAI:
    """Cria o cliente do LLM (Groq, via API compatível com OpenAI)."""
    return ChatOpenAI(
        model=settings.model_name,
        temperature=settings.temperature,
        api_key=settings.require_api_key(),
        base_url=settings.base_url,
    )


def build_agent(llm: Any = None, tools: list | None = None, checkpointer: Any = None):
    """Monta o agente ReAct (LLM + tools + memória). Os parâmetros permitem injetar fakes nos testes."""
    return create_agent(
        model=llm if llm is not None else build_llm(get_settings()),
        tools=tools if tools is not None else get_tools(),
        checkpointer=checkpointer if checkpointer is not None else InMemorySaver(),
        system_prompt=SYSTEM_PROMPT,
    )


def _extrair_passos(messages: list[Any]) -> list[Passo]:
    """Extrai o rastro ReAct (ação + observação) apenas do turno atual, pareando por tool_call_id."""
    ultimo = max((i for i, m in enumerate(messages) if isinstance(m, HumanMessage)), default=-1)
    passos: dict[str, Passo] = {}
    for m in messages[ultimo + 1:]:
        if isinstance(m, AIMessage):
            for tc in m.tool_calls:
                passos[tc["id"]] = Passo(acao=tc["name"], entrada=tc["args"])
        elif isinstance(m, ToolMessage) and m.tool_call_id in passos:
            passos[m.tool_call_id].observacao = str(m.content)
    return list(passos.values())


def perguntar(agent, mensagem: str, thread_id: str) -> RespostaAgente:
    """Envia a mensagem ao agente; o thread_id seleciona o histórico (memória) da conversa."""
    config = {"configurable": {"thread_id": thread_id}}
    try:
        resultado = agent.invoke({"messages": [{"role": "user", "content": mensagem}]}, config=config)
    except openai.AuthenticationError as e:
        raise ExternalServiceError("Chave da API inválida (GROQ_API_KEY).") from e
    except openai.RateLimitError as e:
        raise ExternalServiceError("Limite de requisições do provedor atingido. Tente novamente em instantes.") from e
    except openai.APIConnectionError as e:
        raise ExternalServiceError("Não foi possível conectar ao provedor do LLM.") from e
    except openai.APIError as e:
        raise ExternalServiceError(f"Erro do provedor do LLM: {e}") from e
    msgs = resultado["messages"]
    return RespostaAgente(texto=msgs[-1].text, passos=_extrair_passos(msgs))
