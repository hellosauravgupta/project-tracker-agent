"""
Module: main.py

This module serves as the FastAPI entrypoint. It initializes the database,
provides utility routes including a `/seed` endpoint to populate sample data,
and integrates with the LangChain agent executor for prompt handling.

Key Routes:
    - POST /seed: Populate initial project and task data.
    - POST /agent: Execute agent-based prompt and return structured result.

Dependencies:
    - SQLAlchemy models and session from model.py and database.py
    - LangChain agent interface via agent.py

"""
import datetime
from datetime import date, timedelta
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from . import model, schema, project
from .database import SessionLocal, engine, Base
from .agent import agent_executor


Base.metadata.create_all(bind=engine)
app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/seed")
def seed_data(db: Session = Depends(get_db)):
    """Clear & seed the database with sample projects and tasks.

    Creates 3 projects with 4, 8, and 3 tasks each, assigned across 5 users
    with due dates spread over the last and next 15 days.

    """
    db.query(model.Task).delete()
    db.query(model.Project).delete()
    db.commit()

    users = ["Alice", "Bob", "Carol", "David", "Eve"]
    now = datetime.datetime.now(datetime.timezone.utc).date()

    for i, task_count in enumerate([4, 8, 3], start=1):
        current_project = model.Project(
            name=f"Demo Project {i}",
            description=f"Sample project {i}",
            start_date=now - timedelta(days=15),
            end_date=now + timedelta(days=15),
            status="active"
        )
        db.add(current_project)
        db.flush()  # get project.id

        for j in range(task_count):
            due = now + timedelta(days=(j - task_count // 2) * 2)
            task = model.Task(
                title=f"Task {j+1} for Project {i}",
                assigned_to=users[(i * j) % len(users)],
                status="pending" if j % 3 else "in-progress",
                due_date=due,
                project_id=current_project.id
            )
            db.add(task)

    db.commit()
    return {"message": "Seed data added"}


@app.post("/projects/", response_model=schema.Project)
def create_project(project_request: schema.ProjectCreate, db: Session = Depends(get_db)):
    return project.create_project(db, project_request)


@app.get("/projects/{project_id}", response_model=schema.Project)
def read_project(project_id: int, db: Session = Depends(get_db)):
    db_project = project.get_project(db, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project


@app.post("/projects/{project_id}/tasks/", response_model=schema.Task)
def add_task(project_id: int, task: schema.TaskCreate, db: Session = Depends(get_db)):
    return project.add_task_to_project(db, project_id, task)


@app.get("/projects/", response_model=List[schema.Project])
def list_projects(
    name: Optional[str] = None,
    description: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    filters = {}

    if name: filters["name"] = name
    if description: filters["description"] = description
    if start_date: filters["start_date"] = start_date
    if end_date: filters["end_date"] = end_date
    if status: filters["status"] = status

    return project.get_projects(db, **filters)


@app.post("/agent")
def query_agent(prompt_request: schema.PromptRequest):
    """
    POST /agent

    Run the agent executor with a given natural language prompt.

    This endpoint triggers the LangChain-powered agent to analyze the prompt,
    select the appropriate internal tool, call the Project Tracker API, and
    return a structured JSON response along with a redacted PDF.

    Args:
        prompt_request (PromptRequest): The request body containing a user prompt.

    Returns:
        dict: A dictionary with keys `response` (redacted text) and `pdf` (filename),
            or error message.

    """
    return agent_executor(prompt_request.prompt)
