"""Camada de servico: carrega o pipeline de traducao uma unica vez e traduz textos.

Usa ``transformers.pipeline("translation_en_to_fr")``, como na Etapa 3 da
disciplina. Textos longos sao divididos em frases (``text_chunking``) e
traduzidos em batch.
"""

import torch
from transformers import pipeline

import config
from model_loader import ModelError, ModelLoader
from text_chunking import chunk_text, reassemble

__all__ = ["ModelError", "Translator", "get_service", "is_model_loaded"]


class Translator:
    def __init__(self, model_name: str = config.MODEL_NAME):
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name
        self.pipe = pipeline(f"translation_{config.SOURCE_LANG}_to_{config.TARGET_LANG}", model=model_name, device=device)

    def count_tokens(self, text: str) -> int:
        return len(self.pipe.tokenizer.encode(text, add_special_tokens=False))

    def _translate_batch(self, texts: list[str]) -> list[str]:
        # O pipeline ja aplica torch.inference_mode e divide em lotes de batch_size.
        outputs = self.pipe(
            texts,
            batch_size=config.BATCH_SIZE,
            num_beams=config.NUM_BEAMS,
            max_new_tokens=config.MAX_NEW_TOKENS,
            truncation=True,
        )
        return [out["translation_text"] for out in outputs]

    def translate(self, text: str) -> tuple[str, int]:
        """Traduz o texto e retorna (traducao, numero_de_chunks)."""
        chunks = chunk_text(text, self.count_tokens, config.MAX_CHUNK_TOKENS, config.GROUP_SENTENCES)
        try:
            translations = self._translate_batch([c.text for c in chunks])
        except (RuntimeError, ValueError) as exc:
            raise ModelError(f"Falha na tradução: {exc}") from exc
        return reassemble(chunks, translations), len(chunks)


_loader: ModelLoader[Translator] = ModelLoader(Translator, config.LOAD_RETRY_SECONDS)


def get_service() -> Translator:
    """Dependencia FastAPI: retorna o tradutor (singleton)."""
    return _loader.get()


def is_model_loaded() -> bool:
    return _loader.loaded
