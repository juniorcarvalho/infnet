"""Carregamento preguicoso (lazy) e thread-safe do servico que contem o modelo.

- O modelo e carregado uma unica vez (singleton) e reaproveitado pelas requisicoes.
- Se o carregamento falhar (ex.: sem rede para baixar os pesos), o erro e
  memorizado: as requisicoes seguintes recebem 503 imediatamente, e uma nova
  tentativa so acontece depois de ``retry_seconds``. Assim uma falha nao faz
  cada requisicao tentar baixar o modelo de novo.
"""

import logging
import threading
import time
from collections.abc import Callable
from typing import Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ModelError(RuntimeError):
    """Falha ao carregar ou executar o modelo."""


class ModelLoader(Generic[T]):
    def __init__(self, factory: Callable[[], T], retry_seconds: float = 30.0):
        self._factory = factory
        self._retry_seconds = retry_seconds
        self._lock = threading.Lock()
        self._instance: T | None = None
        self._error: str | None = None
        self._failed_at = 0.0

    @property
    def loaded(self) -> bool:
        return self._instance is not None

    def get(self) -> T:
        if self._instance is not None:
            return self._instance
        with self._lock:
            if self._instance is not None:
                return self._instance
            if self._error and time.monotonic() - self._failed_at < self._retry_seconds:
                raise ModelError(self._error)
            try:
                self._instance = self._factory()
                self._error = None
            except Exception as exc:
                logger.exception("Falha ao carregar o modelo")
                self._error = f"Não foi possível carregar o modelo: {exc}"
                self._failed_at = time.monotonic()
                raise ModelError(self._error) from exc
            return self._instance
