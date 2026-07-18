"""API route handlers for messaging."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas import MessageCreate, MessageResponse, ConversationResponse
from services import MessageService
from dependencies import get_current_user
from models import Account
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """
    Send a message to a conversation.
    
    - **conversation_id**: "dm:<id1>|<id2>" for direct message or "channel:department" for department channel
    - **text**: Message text (required, non-empty)
    """
    try:
        message = MessageService.send_message(db, current_user.id, message_data)
        return MessageResponse.model_validate(message)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/conversation/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """
    Get all messages in a conversation.
    
    - **conversation_id**: "dm:<id1>|<id2>" for direct message or "channel:department" for department channel
    """
    messages = MessageService.get_conversation(db, conversation_id)
    return {
        "conversation_id": conversation_id,
        "messages": [MessageResponse.model_validate(m) for m in messages]
    }


@router.post("/{message_id}/read", response_model=MessageResponse)
async def mark_message_read(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user)
):
    """Mark a message as read by current user."""
    try:
        message = MessageService.mark_as_read(db, message_id, current_user.id)
        return MessageResponse.model_validate(message)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
