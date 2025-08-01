from datetime import date
from typing import Optional

from sqlalchemy.orm import Session
from . import model, schema


def create_project(db: Session, project: schema.ProjectCreate):
    """Create a new project entry in the database.

    Args:
        db (Session): SQLAlchemy session.
        project (ProjectCreate): Pydantic project creation schema.

    Returns:
        Project: Created project model instance.

    """
    db_project = model.Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project(db: Session, project_id: int):
    """Retrieve a project and its associated tasks by ID.

    Args:
        db (Session): SQLAlchemy session.
        project_id (int): Unique ID of the project.

    Returns:
        Project: Project instance with tasks if found, else None.

    """
    return db.query(model.Project).filter(model.Project.id == project_id).first()


def get_projects(db, **filters):
    """Return all projects filtered by optional criteria.

    Args:
        db (Session): SQLAlchemy session.
        filters (dict): Optional filters (e.g., status, start_date, end_date).

    Returns:
        list[Project]: Filtered list of project records.

    """
    query = db.query(model.Project)
    for attr, value in filters.items():
        if hasattr(model.Project, attr):
            query = query.filter(getattr(model.Project, attr) == value)

    return query.all()


def add_task_to_project(db: Session, project_id: int, task: schema.TaskCreate):
    """Add a task to the specified project.

    Args:
        db (Session): SQLAlchemy session.
        project_id (int): ID of the project.
        task (TaskCreate): Task creation schema.

    Returns:
        Task: Created task instance linked to the project.

    """
    db_task = model.Task(**task.model_dump(), project_id=project_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task
