"""Testes unitarios do algoritmo de chunking."""

import pytest

from text_chunking import Chunk, chunk_text, reassemble, split_sentences


def word_count(text: str) -> int:
    return len(text.split())


def test_short_text_is_single_chunk():
    chunks = chunk_text("Hello world. How are you?", word_count, max_tokens=400)
    assert chunks == [Chunk(0, "Hello world. How are you?")]


def test_split_sentences():
    assert split_sentences("One. Two! Three?\nFour") == ["One.", "Two!", "Three?", "Four"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Dr. Smith moved to the U.S. in 2020. He likes it, e.g. the food.",
            ["Dr. Smith moved to the U.S. in 2020.", "He likes it, e.g. the food."],
        ),
        ("J. K. Rowling wrote books. They sold well.", ["J. K. Rowling wrote books.", "They sold well."]),
        ("Mr. and Mrs. Brown arrived. It was 5 p.m. and late.", ["Mr. and Mrs. Brown arrived.", "It was 5 p.m. and late."]),
        ("I live in the U.S. It is big.", ["I live in the U.S.", "It is big."]),
    ],
)
def test_split_sentences_keeps_abbreviations(text, expected):
    assert split_sentences(text) == expected


def test_long_text_splits_without_losing_sentences():
    sentences = [f"Sentence number {i} has some words." for i in range(50)]
    text = " ".join(sentences)
    chunks = chunk_text(text, word_count, max_tokens=30)
    assert len(chunks) > 1
    assert all(word_count(c.text) <= 30 for c in chunks)
    # Nenhuma frase perdida, ordem preservada.
    assert " ".join(c.text for c in chunks) == text


def test_oversized_sentence_is_split_without_losing_words():
    big = " ".join(["Word"] + ["word"] * 24) + "."
    chunks = chunk_text(f"Small one. {big} Another small.", word_count, max_tokens=10)
    texts = [c.text for c in chunks]
    assert texts[0] == "Small one."
    assert texts[-1] == "Another small."
    assert all(word_count(t) <= 10 for t in texts)
    assert " ".join(texts[1:-1]) == big


def test_one_sentence_per_chunk_when_not_grouping():
    chunks = chunk_text("Hello, how are you? It is raining.", word_count, group_sentences=False)
    assert [c.text for c in chunks] == ["Hello, how are you?", "It is raining."]


def test_paragraphs_are_preserved():
    text = "First paragraph. Still first.\n\nSecond paragraph."
    chunks = chunk_text(text, word_count, max_tokens=400)
    assert [c.paragraph for c in chunks] == [0, 1]
    assert reassemble(chunks, [c.text.upper() for c in chunks]) == (
        "FIRST PARAGRAPH. STILL FIRST.\n\nSECOND PARAGRAPH."
    )


def test_reassemble_size_mismatch():
    with pytest.raises(ValueError):
        reassemble([Chunk(0, "a")], [])
