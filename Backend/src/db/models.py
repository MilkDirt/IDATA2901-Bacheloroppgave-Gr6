"""
Database models for the RAG application.

Defines the SQLAlchemy ORM models for:
- User: stores user accounts and credentials
- Project: groups conversations by topic or assignment
- Conversation: a chat session belonging to a user and optionally a project
- Message: individual messages within a conversation
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.db.database import Base


class User(Base):
    __tablename__ = "users"

    """
    Represents a registered user in the system.
    Passwords are stored as bcrypt hashes, never plain text.
    """

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    """
    Represents a project that groups conversations together.
    A user can have multiple projects, each with multiple conversations.
    Conversations can also exist without a project (project_id = None).
    """

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="projects")
    conversations = relationship("Conversation", back_populates="project")


class Conversation(Base):
    __tablename__ = "conversations"

    """
    Represents a single chat session.
    Belongs to a user and optionally to a project.
    Title is auto-generated from the first message.
    """

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    title = Column(String, default="Ny samtale")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    project = relationship("Project", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    """
    Represents a single message within a conversation.
    Role is either 'user' or 'ai'.
    Sources stores cited PDF pages as a JSON string.
    """

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")