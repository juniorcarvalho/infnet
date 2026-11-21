"""Exceções de domínio do assistente financeiro."""


class ConfigError(Exception):
    """Configuração ausente ou inválida (ex.: GROQ_API_KEY)."""


class ExternalServiceError(Exception):
    """Falha em serviço externo (timeout, HTTP != 200, JSON inesperado)."""


class InvalidInputError(Exception):
    """Entrada inválida (moeda/indicador desconhecido, valores negativos)."""
