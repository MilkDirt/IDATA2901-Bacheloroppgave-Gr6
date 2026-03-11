"""Conversation and message endpoints — create, retrieve and delete chat history."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from src.db.database import get_db
from src.db.models import User, Conversation, Message
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])


def save_message(db: Session, conversation_id: int, role: str, content: str, sources: str = None) -> Message:
    """Save a single message to the database."""
    message = Message(conversation_id=conversation_id, role=role, content=content, sources=sources)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_or_create_conversation(
    db: Session,
    user_id: int,
    conversation_id: int = None,
    first_question: str = None,
    project_id: Optional[int] = None
) -> Conversation:
    """Fetch existing conversation or create a new one titled from the first question."""
    if conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        if conversation:
            return conversation

    title = (first_question[:60] + "...") if first_question and len(first_question) > 60 else first_question or "Ny samtale"

    conversation = Conversation(user_id=user_id, title=title, project_id=project_id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/")
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return all conversations for the logged in user, newest first."""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.created_at.desc()).all()

    return [
        {"id": c.id, "title": c.title, "project_id": c.project_id, "created_at": c.created_at}
        for c in conversations
    ]


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation and all its messages. Only the owner can delete."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Samtale ikke funnet")

    db.query(Message).filter(Message.conversation_id == conversation_id).delete()
    db.delete(conversation)
    db.commit()
    return {"message": "Samtale slettet"}


@router.get("/{conversation_id}/messages")
def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return all messages in a conversation ordered by time."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        return []

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()

    return [
        {"id": m.id, "role": m.role, "content": m.content, "sources": m.sources, "created_at": m.created_at}
        for m in messages
    ]