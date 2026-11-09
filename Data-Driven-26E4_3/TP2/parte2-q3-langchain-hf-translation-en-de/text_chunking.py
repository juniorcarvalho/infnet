"""Divisao de textos longos em blocos (chunks) que cabem no limite do modelo.

Os modelos Marian (opus-mt) aceitam no maximo 512 tokens e a qualidade cai
bastante antes disso. Alem disso, foram treinados com pares de *frases*: ao
receber varias frases de uma vez, as vezes descartam parte do conteudo
(ex.: "Hello, how are you? It is raining cats and dogs." vira apenas
"Il pleut des chats et des chiens."). Por isso o padrao e uma frase por chunk,
traduzidas em batch.

Algoritmo:

1. Separa o texto em paragrafos (linhas em branco) para preservar a estrutura.
2. Separa cada paragrafo em frases (pontuacao final seguida de espaco), sem
   quebrar em abreviacoes: "Dr. Smith", "the U.S. in 2020", "e.g. the food"
   (ver ``_is_false_boundary``).
3. Se ``group_sentences=True``, agrupa frases consecutivas ate ``max_tokens``;
   caso contrario, cada frase vira um chunk.
4. Uma frase que sozinha excede ``max_tokens`` e quebrada por palavras em
   pedacos menores (nada e truncado/perdido).
5. Depois da traducao, ``reassemble`` junta os chunks por espaco dentro do
   paragrafo e os paragrafos por linha em branco.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")
# Abreviacoes que quase nunca terminam uma frase (sempre seguidas de mais texto).
NON_TERMINAL_ABBREVIATIONS = {
    "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.", "st.", "vs.", "e.g.", "i.e.", "approx.", "no.", "fig.",
}
# Uma letra maiuscula com ponto: iniciais ("J. K. Rowling").
INITIAL_RE = re.compile(r"(?:^|\s)[A-Z]\.$")


@dataclass(frozen=True)
class Chunk:
    paragraph: int
    text: str


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in PARAGRAPH_SPLIT_RE.split(text) if p.strip()]


def _is_false_boundary(previous: str, following: str) -> bool:
    """True se o ponto no fim de ``previous`` nao encerra a frase."""
    last_word = previous.rsplit(" ", 1)[-1].lower()
    if last_word in NON_TERMINAL_ABBREVIATIONS or INITIAL_RE.search(previous):
        return True
    # Frase nova comeca com maiuscula; minuscula/digito indica continuacao
    # ("moved to the U.S. in 2020", "etc. and more").
    return previous.endswith(".") and (following[0].islower() or following[0].isdigit())


def split_sentences(paragraph: str) -> list[str]:
    # Quebras de linha simples dentro do paragrafo viram espaco.
    normalized = " ".join(paragraph.split())
    sentences: list[str] = []
    for fragment in SENTENCE_SPLIT_RE.split(normalized):
        if not fragment:
            continue
        if sentences and _is_false_boundary(sentences[-1], fragment):
            sentences[-1] = f"{sentences[-1]} {fragment}"
        else:
            sentences.append(fragment)
    return sentences


def split_oversized(sentence: str, count_tokens: Callable[[str], int], max_tokens: int) -> list[str]:
    """Quebra uma frase grande demais em pedacos de ate ``max_tokens`` (por palavras)."""
    pieces: list[str] = []
    current: list[str] = []
    for word in sentence.split():
        candidate = " ".join([*current, word])
        if current and count_tokens(candidate) > max_tokens:
            pieces.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        pieces.append(" ".join(current))
    return pieces


def chunk_text(
    text: str,
    count_tokens: Callable[[str], int],
    max_tokens: int = 400,
    group_sentences: bool = True,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for p_idx, paragraph in enumerate(split_paragraphs(text)):
        current: list[str] = []
        current_tokens = 0

        def flush() -> None:
            nonlocal current, current_tokens
            if current:
                chunks.append(Chunk(p_idx, " ".join(current)))
            current, current_tokens = [], 0

        for sentence in split_sentences(paragraph):
            n_tokens = count_tokens(sentence)
            if n_tokens > max_tokens:
                flush()
                chunks.extend(Chunk(p_idx, piece) for piece in split_oversized(sentence, count_tokens, max_tokens))
                continue
            if not group_sentences or (current and current_tokens + n_tokens > max_tokens):
                flush()
            current.append(sentence)
            current_tokens += n_tokens
        flush()
    return chunks


def reassemble(chunks: list[Chunk], translations: list[str]) -> str:
    if len(chunks) != len(translations):
        raise ValueError("chunks e translations devem ter o mesmo tamanho")
    paragraphs: dict[int, list[str]] = {}
    for chunk, translated in zip(chunks, translations):
        paragraphs.setdefault(chunk.paragraph, []).append(translated.strip())
    return "\n\n".join(" ".join(parts) for _, parts in sorted(paragraphs.items()))
