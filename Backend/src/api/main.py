"""
API layer for the RAG-based question answering system.

Exposes HTTP endpoints that allow clients to:
- Check service health
- Ask questions and receive grounded answers from documents
- Manage user authentication
- Manage projects and conversations
"""
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import json

from src.rag.answer import get_answerer
from src.db.database import engine, get_db
from src.db import models
from src.db.models import User
from src.api.auth import router as auth_router
from src.api.dependencies import get_current_user
from src.api.conversations import router as conversations_router
from src.api.conversations import get_or_create_conversation, save_message
from src.api.projects import router as projects_router

# Initialize FastAPI application FIRST
app = FastAPI(title="Bachelor RAG API")

# Register auth routes (/auth/register, /auth/login)
app.include_router(auth_router)

# Register conversation routes (/conversations/)
app.include_router(conversations_router)

# Register project routes (/projects/)
app.include_router(projects_router)

# Create all database tables on startup if they don't exist
models.Base.metadata.create_all(bind=engine)

# Allow frontend (Vite dev server) to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared RAG answerer instance (loads FAISS index once)
answerer = get_answerer()


class AskRequest(BaseModel):
    """
    Request model for the /ask endpoint.

    Attributes:
        question (str): Natural language question from the user.
        conversation_id (Optional[int]): Continues an existing conversation.
        project_id (Optional[int]): Links the conversation to a project.
    """
    question: str
    conversation_id: Optional[int] = None
    project_id: Optional[int] = None


@app.get("/health")
def health():
    """
    Health check endpoint.

    Returns:
        dict: Simple status response used for monitoring.
    """
    return {"status": "ok"}


@app.post("/ask")
def ask(
    req: AskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Protected endpoint for question answering.

    Asks the RAG system a question, saves both the question
    and answer to the database, and returns the answer.

    Args:
        req (AskRequest): Contains the question, optional conversation_id
                          and optional project_id.
        current_user (User): The authenticated user.
        db (Session): Database session.

    Returns:
        dict: Answer, sources, conversation_id and metadata.
    """
    # Get or create a conversation for this chat session
    conversation = get_or_create_conversation(
        db=db,
        user_id=current_user.id,
        conversation_id=req.conversation_id,
        first_question=req.question,
        project_id=req.project_id
    )

    # Save the user's question
    save_message(db, conversation.id, "user", req.question)

    # Get answer from RAG system
    result = answerer.answer(req.question)

    # Save the AI answer with sources
    sources_str = json.dumps(result.get("sources", []))
    save_message(db, conversation.id, "ai", result.get("answer", ""), sources_str)

    # Return result with conversation_id so frontend can continue the chat
    return {
        **result,
        "conversation_id": conversation.id
    }


@app.post("/generate-application")
async def generate_application(data: dict):
    """
    Placeholder endpoint for generating applications.

    Returns:
        dict: Generated application text.
    """
    return {
        "application_text": "Generert byggesøknad her..."
    }