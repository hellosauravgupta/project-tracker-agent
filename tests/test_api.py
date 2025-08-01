import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_create_project():
    response = client.post("/projects/", json={
        "name": "Test Project",
        "description": "A sample project",
        "start_date": "2025-07-01",
        "end_date": "2025-08-01",
        "status": "active"
    })

    assert response.status_code == 200
    assert response.json()["name"] == "Test Project"

def test_add_task_to_project():
    project_payload = {
        "name": "Sample Project",
        "description": "Test project",
        "start_date": "2025-07-01",
        "end_date": "2025-08-01",
        "status": "active"
    }
    project_resp = client.post("/projects/", json=project_payload)
    project_id = project_resp.json()["id"]

    task_payload = {
        "title": "Sample Task",
        "assigned_to": "Bob",
        "status": "pending",
        "due_date": "2025-08-01"
    }
    response = client.post(f"/projects/{project_id}/tasks/", json=task_payload)

    assert response.status_code == 200
    assert response.json()["title"] == "Sample Task"

def test_get_project_by_id():
    project_payload = {
        "name": "Project Fetch",
        "description": "Project for fetch test",
        "start_date": "2025-07-01",
        "end_date": "2025-08-01",
        "status": "active"
    }
    created = client.post("/projects/", json=project_payload)
    pid = created.json()["id"]
    response = client.get(f"/projects/{pid}")

    assert response.status_code == 200
    assert response.json()["name"] == "Project Fetch"

def test_list_projects():
    response = client.get("/projects/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_agent_prompt_all_tasks():
    response = client.post("/agent", json={"prompt": "Show me all tasks assigned to Alice"})

    assert response.status_code == 200
    assert "tasks" in response.json().get("response", "").lower() or "sorry" in response.json().get("response", "").lower()

def test_agent_prompt_fallback():
    response = client.post("/agent", json={"prompt": "Tell me a joke"})

    assert response.status_code == 200
    assert "sorry" in response.json().get("response", "").lower()

def test_seed_endpoint():
    response = client.post("/seed")

    assert response.status_code == 200
    assert response.json()["message"] == "Seed data added"
