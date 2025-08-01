"""
Module: model.py

Contains SQLAlchemy ORM model definitions for the database schema. Each class
represents a table in the PostgreSQL database used by the project tracking
system.

Models:
    - Project: Represents a project entity.
    - Task: Represents a task associated with a specific project.

"""
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Project(Base):
    """ORM model for the Project table."""

    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String)
    tasks = relationship("Task", back_populates="project")


class Task(Base):
    """ORM model for the Task table, associated with a specific Project."""

    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    assigned_to = Column(String)
    status = Column(String)
    due_date = Column(Date)
    project_id = Column(Integer, ForeignKey("projects.id"))
    project = relationship("Project", back_populates="tasks")
