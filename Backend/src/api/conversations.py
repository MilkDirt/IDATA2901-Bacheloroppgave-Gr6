"""
Conversation and message management for the RAG API.

This module handles:
- Creating new conversations
- Saving user questions and AI answers to the database
- Retrieving conversation history for the sidebar
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from src.db.database import get_db
from src.db.models import User, Conversation, Message
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])


def save_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
    sources: str = None
) -> Message:
    """
    Save a single message to the database.

    Args:
        db (Session): Database session.
        conversation_id (int): The conversation this message belongs to.
        role (str): Either 'user' or 'ai'.
        content (str): The message text.
        sources (str): Optional JSON string of PDF sources cited.

    Returns:
        Message: The saved message object.
    """
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources=sources
    )
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
    """
    Get an existing conversation or create a new one.

    If conversation_id is provided, fetches that conversation.
    Otherwise creates a new one using the first question as the title.

    Args:
        db (Session): Database session.
        user_id (int): The user this conversation belongs to.
        conversation_id (int): Optional existing conversation ID.
        first_question (str): Used as title if creating a new conversation.
        project_id (Optional[int]): Optional project to link conversation to.

    Returns:
        Conversation: The existing or newly created conversation.
    """
    if conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        if conversation:
            return conversation

    # Title is first 60 chars of the question
    title = (first_question[:60] + "...") if first_question and len(first_question) > 60 else first_question or "Ny samtale"

    conversation = Conversation(
        user_id=user_id,
        title=title,
        project_id=project_id
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/")
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all conversations for the logged in user.

    Returns conversations sorted by most recent first.
    Used to populate the sidebar in the frontend.

    Args:
        current_user (User): The authenticated user.
        db (Session): Database session.

    Returns:
        list: All conversations belonging to the user.
    """
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.created_at.desc()).all()

    return [
        {
            "id": c.id,
            "title": c.title,
            "project_id": c.project_id,
            "created_at": c.created_at
        }
        for c in conversations
    ]


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation and all its messages.

    Only the owner of the conversation can delete it.

    Args:
        conversation_id (int): The conversation to delete.
        current_user (User): The authenticated user.
        db (Session): Database session.

    Returns:
        dict: Confirmation message.
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Samtale ikke funnet")

    # Delete all messages first
    db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).delete()

    db.delete(conversation)
    db.commit()

    return {"message": "Samtale slettet"}


@router.get("/{conversation_id}/messages")
def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all messages for a specific conversation.

    Only returns messages if the conversation belongs to the current user.

    Args:
        conversation_id (int): The conversation to load.
        current_user (User): The authenticated user.
        db (Session): Database session.

    Returns:
        list: All messages in the conversation ordered by time.
    """
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
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "sources": m.sources,
            "created_at": m.created_at
        }
        for m in messages
    ]