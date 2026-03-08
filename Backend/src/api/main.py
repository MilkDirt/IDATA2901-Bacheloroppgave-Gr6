
"""
API layer for the RAG-based question answering system.

Exposes HTTP endpoints that allow clients to:
- Check service health
- Ask questions and receive grounded answers from documents
"""
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from src.rag.answer import get_answerer
from src.db.database import engine
from src.db import models
from src.api.auth import router as auth_router

# Initialize FastAPI application FIRST
app = FastAPI(title="Bachelor RAG API")

# Then include routers
app.include_router(auth_router)

# Create tables
models.Base.metadata.create_all(bind=engine)

#Testing to connect front to backend
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a single shared RAG answerer instance
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
def ask(req: AskRequest):
    """
       Main API endpoint for question answering.

       Receives a user question, retrieves relevant document
       content using RAG, and returns a grounded answer.

       Args:
           req (AskRequest): Incoming request with user question.

       Returns:
           dict: Answer, sources, and metadata.
       """
    return answerer.answer(req.question)

@app.post("/generate-application")
async def generate_application(data: dict):
    # bruk data direkte i prompt
    return {
        "application_text": "Generert byggesøknad her..."
    }
