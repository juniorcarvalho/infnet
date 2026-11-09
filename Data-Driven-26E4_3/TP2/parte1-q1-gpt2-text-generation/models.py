"""Schemas Pydantic de request/response."""

from pydantic import BaseModel, Field, field_validator

import config


class GenerateRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=config.MAX_PROMPT_CHARS,
        examples=["Once upon a time in a small village,"],
    )
    max_new_tokens: int = Field(
        default=config.DEFAULT_MAX_NEW_TOKENS, ge=1, le=config.MAX_NEW_TOKENS_LIMIT
    )
    temperature: float = Field(default=config.DEFAULT_TEMPERATURE, ge=0.1, le=2.0)
    top_k: int = Field(default=config.DEFAULT_TOP_K, ge=1, le=config.MAX_TOP_K)
    num_return_sequences: int = Field(default=1, ge=1, le=config.MAX_RETURN_SEQUENCES)
    seed: int | None = Field(default=None, description="Semente para resultado reproduzível")

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("o prompt não pode ser vazio")
        return cleaned


class Generation(BaseModel):
    generated_text: str = Field(description="Prompt + continuação")
    continuation: str = Field(description="Somente o texto gerado pelo modelo")


class GenerateResponse(BaseModel):
    prompt: str
    generations: list[Generation]
    model: str
    latency_ms: float


class HealthResponse(BaseModel):
    status: str
    model: str
    model_loaded: bool
