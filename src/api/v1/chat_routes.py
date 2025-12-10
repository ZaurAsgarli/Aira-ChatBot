from fastapi import APIRouter, Depends
from src.models.chat_schema import ChatRequest, ChatResponse
from src.config import settings

router = APIRouter()

@router.post("/query", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # TODO: Connect Orchestrator here
    return ChatResponse(
        answer=f"This is a placeholder response from {settings.APP_NAME}. I received: {request.query}",
        sources=[],
        recommendations=[]
    )
