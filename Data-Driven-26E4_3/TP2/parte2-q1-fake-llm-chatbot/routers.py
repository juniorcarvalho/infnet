"""Rotas HTTP do chatbot (APIRouter)."""

from fastapi import APIRouter, Depends

from models import ChatRequest, ChatResponse, HealthResponse, QuestionsResponse
from services import ChatService, get_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> dict:
    return {"status": "ok", "llm": "fake"}


@router.get("/questions", response_model=QuestionsResponse)
def questions(service: ChatService = Depends(get_service)) -> dict:
    return {"questions": service.questions()}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, service: ChatService = Depends(get_service)) -> dict:
    response, matched = service.ask(request.message)
    return {"message": request.message, "response": response, "matched": matched, "llm": "fake"}
