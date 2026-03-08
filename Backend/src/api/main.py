"""
API layer for the RAG-based question answering system.

Exposes HTTP endpoints that allow clients to:
- Check service health
- Ask questions and receive grounded answers from documents
"""
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from src.rag.answer import get_answerer
from src.db.database import engine
from src.db import models
from src.db.models import User
from src.api.auth import router as auth_router
from src.api.dependencies import get_current_user

# Initialize FastAPI application FIRST
app = FastAPI(title="Bachelor RAG API")

# Register auth routes (/auth/register, /auth/login)
app.include_router(auth_router)

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
    """
    question: str


@app.get("/health")
def health():
    """
    Health check endpoint.

    Returns:
        dict: Simple status response used for monitoring.
    """
    return {"status": "ok"}


@app.post("/ask")
def ask(req: AskRequest, current_user: User = Depends(get_current_user)):
    """
    Protected endpoint for question answering.

    Requires a valid JWT token in the Authorization header.
    Only authenticated users can query the RAG system.

    Args:
        req (AskRequest): Incoming request containing the user's question.
        current_user (User): The authenticated user, injected by FastAPI.

    Returns:
        dict: Answer, sources, and metadata from the RAG system.
    """
    return answerer.answer(req.question)


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