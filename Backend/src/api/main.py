
"""
API layer for the RAG-based question answering system.

Exposes HTTP endpoints that allow clients to:
- Check service health
- Ask questions and receive grounded answers from documents
"""

from fastapi import FastAPI
from pydantic import BaseModel

from src.rag.answer import get_answerer

# Initialize FastAPI application
app = FastAPI(title="Bachelor RAG API")

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
