"""
API layer for the RAG-based question answering system.

Exposes HTTP endpoints that allow clients to:
- Check service health
- Ask questions and receive grounded answers from documents
- Manage user authentication
- Manage projects and conversations
- Generate building parameters from skeleton info
"""
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import json
import os

from openai import OpenAI
from src.rag.answer import get_answerer
from src.db.database import engine, get_db
from src.db import models
from src.db.models import User
from src.api.auth import router as auth_router
from src.api.dependencies import get_current_user
from src.api.conversations import router as conversations_router
from src.api.conversations import get_or_create_conversation, save_message
from src.api.projects import router as projects_router
from src.config import settings

# Initialize FastAPI application
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


class BuildingRequest(BaseModel):
    """
    Request model for /generate-building endpoint.

    Attributes:
        description (str): Natural language building description.
        floors (int): Number of floors in the skeleton.
        height (float): Total building height in meters.
        footprint_width (float): Building width in meters.
        footprint_depth (float): Building depth in meters.
    """
    description: str
    floors: int = 1
    height: float = 9.0
    footprint_width: float = 10.0
    footprint_depth: float = 10.0


@app.get("/health")
def health():
    """Health check endpoint."""
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


@app.post("/generate-building")
async def generate_building(req: BuildingRequest):
    """
    Takes skeleton info + building description,
    sends to NTNU LLM, returns architectural parameters as JSON.

    Args:
        req (BuildingRequest): Building description and skeleton dimensions.

    Returns:
        dict: window_ratio, wall_thickness, floor_height, facade_style
    """
    # Use same NTNU client as the rest of the app
    client = OpenAI(
        api_key=settings.ntnu_api_key,
        base_url=settings.ntnu_base_url
    )

    prompt = f"""
    You are an architectural assistant. Based on the building description and skeleton info,
    return ONLY a valid JSON object with no extra text or explanation.

    Building description: {req.description}
    Number of floors: {req.floors}
    Total height: {req.height}m
    Footprint: {req.footprint_width}m x {req.footprint_depth}m

    Return ONLY this JSON:
    {{
        "window_ratio": <float between 0.2 and 0.7>,
        "wall_thickness": <float between 0.1 and 0.5>,
        "floor_height": <float>,
        "facade_style": <"modern", "classic", or "industrial">
    }}
    """

    response = client.chat.completions.create(
        model=settings.chat_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    try:
        # Strip markdown code fences if the LLM wraps the JSON in ```json ... ```
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
    except Exception:
        # Fall back to safe defaults if the LLM returns invalid JSON
        result = {
            "window_ratio": 0.4,
            "wall_thickness": 0.2,
            "floor_height": req.height / max(req.floors, 2),
            "facade_style": "modern"
        }
    return result