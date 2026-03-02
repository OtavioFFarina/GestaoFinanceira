"""
Chat routes — Avocado AI Financial Assistant
POST /api/chat
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Avocado AI"])
_svc = ChatService()


class ChatRequest(BaseModel):
    usuario_id: str
    mensagem: str
    # Optional conversation history for multi-turn context
    historico: list[dict] | None = None


class ChatResponse(BaseModel):
    resposta: str


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    resposta = await _svc.responder(
        db=db,
        usuario_id=payload.usuario_id,
        mensagem=payload.mensagem,
        historico=payload.historico,
    )
    return ChatResponse(resposta=resposta)
