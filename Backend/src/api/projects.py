"""Project management endpoints — create, list, delete projects and their conversations."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.db.database import get_db
from src.db.models import User, Project, Conversation
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectRequest(BaseModel):
    name: str


@router.post("/")
def create_project(
    req: ProjectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = Project(user_id=current_user.id, name=req.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"id": project.id, "name": project.name, "created_at": project.created_at}


@router.get("/")
def get_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
    """Deletes project but keeps its conversations — they become project-less."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Prosjekt ikke funnet")

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
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Prosjekt ikke funnet")

    conversations = db.query(Conversation).filter(
        Conversation.project_id == project_id
    ).order_by(Conversation.created_at.desc()).all()

    return [{"id": c.id, "title": c.title, "created_at": c.created_at} for c in conversations]