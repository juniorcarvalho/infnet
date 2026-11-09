"""Schemas Pydantic de request/response."""

from pydantic import BaseModel, Field, field_validator

import config


class ChatRequest(BaseModel):
    message: str = Field(
        ..., min_length=1, max_length=config.MAX_MESSAGE_CHARS, examples=["O que é LangChain?"]
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("a mensagem não pode ser vazia")
        return cleaned


class ChatResponse(BaseModel):
    message: str
    response: str
    matched: bool | None = Field(description="A pergunta foi encontrada no FAQ? (None se o LLM nao for o PredefinedFakeLLM)")
    llm: str


class QuestionsResponse(BaseModel):
    questions: list[str]


class HealthResponse(BaseModel):
    status: str
    llm: str
