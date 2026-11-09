"""Fake LLM customizado + chain LCEL do chatbot."""

import difflib
import re
import string
import unicodedata
from functools import lru_cache
from typing import Any

from langchain_core.language_models.llms import LLM
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable

import config
from faq import FALLBACK_ANSWER, PREDEFINED_QA

PROMPT_TEMPLATE = (
    "Voce e um assistente prestativo que responde perguntas frequentes em portugues.\n"
    "Pergunta: {question}\n"
    "Resposta:"
)
QUESTION_RE = re.compile(r"Pergunta:\s*(.*?)\s*(?:\nResposta:|$)", re.DOTALL)


def normalize(text: str) -> str:
    """Minusculas, sem acentos, sem pontuacao e espacos colapsados."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.translate(str.maketrans("", "", string.punctuation + "?!"))
    return " ".join(text.split())


def find_answer(question: str, cutoff: float = config.MATCH_CUTOFF) -> tuple[str, bool]:
    """Retorna (resposta, encontrou?) para a pergunta do usuario."""
    norm = normalize(question)
    if norm in PREDEFINED_QA:
        return PREDEFINED_QA[norm], True
    close = difflib.get_close_matches(norm, PREDEFINED_QA.keys(), n=1, cutoff=cutoff)
    if close:
        return PREDEFINED_QA[close[0]], True
    return FALLBACK_ANSWER, False


class PredefinedFakeLLM(LLM):
    """LLM simulado: responde perguntas pre-definidas, sem rede e sem custo."""

    @property
    def _llm_type(self) -> str:
        return "predefined-fake"

    def _call(self, prompt: str, stop: list[str] | None = None, run_manager: Any = None, **kwargs: Any) -> str:
        match = QUESTION_RE.search(prompt)
        question = match.group(1) if match else prompt
        answer, _ = find_answer(question)
        return answer


def build_chain(llm: Any | None = None) -> Runnable:
    """PromptTemplate | LLM | StrOutputParser. O LLM pode ser trocado (ex.: nos testes)."""
    prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
    return prompt | (llm or PredefinedFakeLLM()) | StrOutputParser()


class ChatService:
    def __init__(self, llm: Any | None = None):
        self.llm = llm or PredefinedFakeLLM()
        self.chain = build_chain(self.llm)

    def ask(self, message: str) -> tuple[str, bool | None]:
        """Retorna (resposta, matched).

        ``matched`` so tem significado com o PredefinedFakeLLM (a resposta veio
        do FAQ?). Com outro LLM (FakeListLLM, OpenAI...) o FAQ nao e consultado,
        entao ``matched`` e None.
        """
        response = self.chain.invoke({"question": message})
        if isinstance(self.llm, PredefinedFakeLLM):
            return response, response != FALLBACK_ANSWER
        return response, None

    @staticmethod
    def questions() -> list[str]:
        return list(PREDEFINED_QA.keys())


@lru_cache(maxsize=1)
def get_service() -> ChatService:
    return ChatService()
