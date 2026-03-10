"""
Project management endpoints for the RAG API.

Allows users to create, list and delete their own projects.
Projects are used to group conversations together.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from src.db.database import get_db
from src.db.models import User, Project, Conversation
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectRequest(BaseModel):
    """
    Request model for creating a new project.

    Attributes:
        name (str): The name of the project.
    """
    name: str


@router.post("/")
def create_project(
    req: ProjectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new project for the logged in user.

    Args:
        req (ProjectRequest): Contains the project name.
        current_user (User): The authenticated user.
        db (Session): Database session.

    Returns:
        dict: The created project with id, name and created_at.
    """
    project = Project(
        user_id=current_user.id,
        name=req.name
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "created_at": project.created_at
    }


@router.get("/")
def get_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all projects for the logged in user.

    Returns projects sorted by most recent first.

    Args:
        current_user (User): The authenticated user.
        db (Session): Database session.

    Returns:
        list: All projects belonging to the user.
    """
    projects = db.query(Project).filter(
        Project.user_id == current_user.id
    ).order_by(Project.created_at.desc()).all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "created_at": p.created_at,
            "conversation_count": len(p.conversations)
        }
        for p in projects
    ]


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a project and unlink its conversations.

    Conversations are not deleted — they become project-less.
    Only the owner of the project can delete it.

    Args:
        project_id (int): The project to delete.
        current_user (User): The authenticated user.
        db (Session): Database session.

    Returns:
        dict: Confirmation message.
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Prosjekt ikke funnet")

    # Unlink conversations instead of deleting them
    db.query(Conversation).filter(
        Conversation.project_id == project_id
    ).update({"project_id": None})

    db.delete(project)
    db.commit()

    return {"message": "Prosjekt slettet"}


@router.get("/{project_id}/conversations")
def get_project_conversations(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all conversations belonging to a specific project.

    Args:
        project_id (int): The project to fetch conversations for.
        current_user (User): The authenticated user.
        db (Session): Database session.

    Returns:
        list: All conversations in the project.
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Prosjekt ikke funnet")

    conversations = db.query(Conversation).filter(
        Conversation.project_id == project_id
    ).order_by(Conversation.created_at.desc()).all()

    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at
        }
        for c in conversations
    ]