"""Base de perguntas e respostas pre-definidas do chatbot.

As chaves ja estao normalizadas (minusculas, sem acentos e sem pontuacao),
no mesmo formato produzido por ``services.normalize``.
"""

PREDEFINED_QA: dict[str, str] = {
    "ola": "Olá! Sou o assistente virtual do TP2. Como posso ajudar?",
    "qual seu nome": "Eu sou o FakeBot, um chatbot de demonstração construído com LangChain e um Fake LLM.",
    "o que e langchain": (
        "LangChain é um framework para construir aplicações com LLMs, compondo prompts, "
        "modelos, parsers, memória e ferramentas em cadeias (chains)."
    ),
    "o que e fastapi": (
        "FastAPI é um framework web Python de alta performance para criar APIs, "
        "com validação via Pydantic e documentação OpenAPI automática."
    ),
    "o que e fake llm": (
        "Um Fake LLM é um modelo simulado que devolve respostas pré-definidas. Ele permite "
        "testar prompts, chains e APIs de forma rápida, determinística e sem custo."
    ),
    "qual o horario de atendimento": "Nosso atendimento funciona de segunda a sexta, das 9h às 18h.",
    "como entro em contato": "Você pode enviar um e-mail para suporte@exemplo.com.",
    "tchau": "Até logo! Foi um prazer ajudar.",
}

FALLBACK_ANSWER = (
    "Desculpe, não sei responder a essa pergunta. "
    "Consulte GET /questions para ver as perguntas que eu conheço."
)
