"""Schemas Pydantic de request/response."""

from pydantic import BaseModel, Field, field_validator

import config


class TranslateRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=config.MAX_INPUT_CHARS,
        examples=["Hello, how are you? I hope you are having a great day."],
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("o texto não pode ser vazio")
        return cleaned


class TranslateResponse(BaseModel):
    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    model: str
    framework: str
    chunks: int
    latency_ms: float


class HealthResponse(BaseModel):
    status: str
    model: str
    framework: str
    model_loaded: bool
