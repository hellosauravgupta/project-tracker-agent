"""
Module: schema.py

Defines Pydantic models used for request validation and response serialization
in the API.

Schemas:
    - ProjectCreate: Input model for creating a project.
    - TaskCreate: Input model for creating a task within a project.
    - Task: Output model for returning task data.
    - Project: Output model for returning project data with associated tasks.
    - Prompt: Output model for returning prompt data.

"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    title: str
    assigned_to: str
    status: str
    due_date: date


class Task(TaskCreate):
    """Schema for reading task data, extends TaskCreate with ID."""

    id: int
    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str
    description: str
    start_date: date
    end_date: date
    status: str


class Project(ProjectCreate):
    """Schema for reading project data, includes task list and project ID."""

    id: int
    tasks: List[Task] = []
    class Config:
        from_attributes = True


class PromptRequest(BaseModel):
    """Model representing a user prompt for the agent.

    Attributes:
        prompt (str): The natural language instruction to be processed by the agent.

    """
    prompt: str
