"""Camada de servico: carrega o GPT-2 uma unica vez e gera texto.

Segue o padrao da Etapa 3 da disciplina: ``pipeline("text-generation")``,
selecao de ``device`` (GPU se disponivel), ``GenerationConfig`` com os
parametros de amostragem e ``return_full_text=False``.
"""

import torch
from transformers import GenerationConfig, pipeline, set_seed

import config
from model_loader import ModelError, ModelLoader

__all__ = ["ModelError", "TextGenerator", "get_service", "is_model_loaded"]


class TextGenerator:
    def __init__(self, model_name: str = config.MODEL_NAME):
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name
        self._pipe = pipeline("text-generation", model=model_name, device=device)
        # Evita o aviso/conflito entre max_length (padrao do modelo) e max_new_tokens.
        self._pipe.model.generation_config.max_length = None

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = config.DEFAULT_MAX_NEW_TOKENS,
        temperature: float = config.DEFAULT_TEMPERATURE,
        top_k: int = config.DEFAULT_TOP_K,
        num_return_sequences: int = 1,
        seed: int | None = None,
    ) -> list[dict[str, str]]:
        # Observacao: set_seed altera o RNG global do torch. Com requisicoes
        # concorrentes, a reprodutibilidade so e garantida sem concorrencia.
        if seed is not None:
            set_seed(seed)
        generation_config = GenerationConfig(
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            top_k=top_k,
            top_p=config.TOP_P,
            no_repeat_ngram_size=config.NO_REPEAT_NGRAM_SIZE,
            # GPT-2 nao possui pad token; usa-se o EOS no lugar.
            pad_token_id=self._pipe.tokenizer.eos_token_id,
        )
        try:
            outputs = self._pipe(
                prompt,
                max_length=None,
                generation_config=generation_config,
                num_return_sequences=num_return_sequences,
                return_full_text=False,  # devolve so a continuacao
            )
        except (RuntimeError, ValueError) as exc:
            raise ModelError(f"Falha na geração de texto: {exc}") from exc

        # A continuacao ja traz o espaco inicial (" texto..."), entao a
        # concatenacao direta reproduz o texto completo sem espacos duplicados.
        return [
            {"generated_text": prompt + out["generated_text"], "continuation": out["generated_text"].strip()}
            for out in outputs
        ]


_loader: ModelLoader[TextGenerator] = ModelLoader(TextGenerator, config.LOAD_RETRY_SECONDS)


def get_service() -> TextGenerator:
    """Dependencia FastAPI: retorna o gerador (singleton)."""
    return _loader.get()


def is_model_loaded() -> bool:
    return _loader.loaded
