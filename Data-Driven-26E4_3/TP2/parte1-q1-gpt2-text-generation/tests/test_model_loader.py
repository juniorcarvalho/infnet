"""Testes do ModelLoader: singleton, memorizacao da falha e nova tentativa."""

import pytest

from model_loader import ModelError, ModelLoader


def test_loads_once():
    calls = []
    loader = ModelLoader(lambda: calls.append(1) or object())
    assert not loader.loaded
    first = loader.get()
    assert loader.get() is first
    assert loader.loaded and len(calls) == 1


def test_failure_is_memoized_until_retry(monkeypatch):
    attempts = []

    def factory():
        attempts.append(1)
        if len(attempts) == 1:
            raise OSError("sem rede")
        return "modelo"

    now = [1000.0]
    monkeypatch.setattr("model_loader.time.monotonic", lambda: now[0])
    loader = ModelLoader(factory, retry_seconds=30)

    with pytest.raises(ModelError, match="sem rede"):
        loader.get()
    # Dentro da janela: falha imediata, sem nova tentativa de carga.
    now[0] += 10
    with pytest.raises(ModelError):
        loader.get()
    assert len(attempts) == 1
    # Depois da janela: tenta de novo e carrega.
    now[0] += 30
    assert loader.get() == "modelo"
    assert len(attempts) == 2 and loader.loaded
