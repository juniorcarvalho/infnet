"""Chain LangChain (PromptTemplate | HuggingFacePipeline | StrOutputParser).

O ``HuggingFacePipeline`` (pacote ``langchain-huggingface``) encapsula um
``transformers.pipeline("translation")`` com o modelo Helsinki-NLP/opus-mt-en-de.
Requer transformers 4.x: no 5.x a task "translation" foi removida.
"""

from collections.abc import Callable
from typing import Any

import torch
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from langchain_huggingface import HuggingFacePipeline

import config
from model_loader import ModelError, ModelLoader
from text_chunking import chunk_text, reassemble

__all__ = ["ModelError", "TranslationService", "build_chain", "get_service", "is_model_loaded"]


def build_chain(llm: Any) -> Runnable:
    # O prompt e apenas o texto puro: o Marian nao segue instrucoes, e qualquer
    # instrucao extra ("Translate to German: ...") seria traduzida junto.
    return PromptTemplate.from_template("{text}") | llm | StrOutputParser()


def build_llm() -> Any:
    return HuggingFacePipeline.from_model_id(
        model_id=config.MODEL_NAME,
        task="translation",
        device=0 if torch.cuda.is_available() else -1,  # -1 = CPU
        batch_size=config.BATCH_SIZE,
        pipeline_kwargs={"max_new_tokens": config.MAX_NEW_TOKENS, "num_beams": config.NUM_BEAMS},
    )


class TranslationService:
    def __init__(self, chain: Runnable, count_tokens: Callable[[str], int], model_name: str):
        self.chain = chain
        self.count_tokens = count_tokens
        self.model_name = model_name

    def translate(self, text: str) -> tuple[str, int]:
        chunks = chunk_text(text, self.count_tokens, config.MAX_CHUNK_TOKENS, config.GROUP_SENTENCES)
        try:
            # chain.batch entrega todos os chunks ao HuggingFacePipeline numa unica
            # chamada, que os traduz em lotes de batch_size.
            outputs = self.chain.batch([{"text": c.text} for c in chunks])
        except (RuntimeError, ValueError) as exc:
            raise ModelError(f"Falha na tradução: {exc}") from exc
        return reassemble(chunks, outputs), len(chunks)


def _create_service() -> TranslationService:
    llm = build_llm()
    tokenizer = llm.pipeline.tokenizer

    def count_tokens(text: str) -> int:
        return len(tokenizer.encode(text, add_special_tokens=False))

    return TranslationService(build_chain(llm), count_tokens, config.MODEL_NAME)


_loader: ModelLoader[TranslationService] = ModelLoader(_create_service, config.LOAD_RETRY_SECONDS)


def get_service() -> TranslationService:
    """Dependencia FastAPI: carrega o modelo uma unica vez (singleton)."""
    return _loader.get()


def is_model_loaded() -> bool:
    return _loader.loaded
