"""
Module: agent_tools.py

This module contains LangChain agent tool implementations for interacting with
project and task data through an LLM-driven agentic interface. Tools allow querying
and processing project data using MCP-compatible flows.

Exposes:
- redact_pii: Utility for redacting sensitive info from text.
- fetch_overdue_tasks: Get overdue tasks assigned to a user.
- fetch_all_tasks: Get all tasks assigned to a user.
- list_all_projects: Returns all available projects.
- get_project_by_id: Fetch project details by ID.
- agent_executor: Entrypoint to invoke tools using an LLM agent.

"""
import requests
import os
from datetime import date
from uuid import uuid4
from datetime import datetime
import re

from langchain.agents import Tool, initialize_agent, AgentType
from langchain_community.llms import OpenAI
from langchain.schema.output_parser import StrOutputParser
import redis
from fpdf import FPDF

from .constant import CACHE_TTL, API_ROOT


llm = OpenAI(
    temperature=0.3,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)
redis_client = redis.Redis(host="redis", port=6379, db=0)


def redact_pii(text: str) -> str:
    """Redact personally identifiable information from a given *text*.

    Args:
        text (str): The string to parse

    Supports email, SSN & phone numbers.

    Returns:
        str: The redacted string.

    """
    text = re.sub(r"\b[\w.-]+@[\w.-]+\.[a-zA-Z]{2,6}\b", "[REDACTED_EMAIL]", text)
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", text)
    text = re.sub(r"\b\d{10}\b", "[REDACTED_PHONE]", text)

    return text


def log_telemetry(prompt: str, response: str):
    """Log prompt-response telemetry to Redis.

    Args:
        prompt (str): Original user prompt.
        response (str): Agent-generated response.

    Returns:
        None

    """
    timestamp = datetime.now().isoformat()
    redis_client.hset(
        name=f"telemetry:{timestamp}",
        mapping={
            "prompt": prompt,
            "response": response,
            "timestamp": timestamp
        }
    )


def export_to_pdf(content: str) -> str:
    """Exports given content to a PDF file.

    Args:
        content (str): Text to be added to PDF.

    Returns:
        str: Filename of the created PDF.

    """
    filename = f"output_{uuid4().hex[:8]}.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    safe_content = content.replace("’", "'")  # Fix fancy apostrophe

    for line in safe_content.splitlines():
        pdf.cell(
            200,
            10,
            txt=line.encode(
                "latin-1", errors="ignore"
            ).decode("latin-1"),
            ln=True
        )

    pdf.output(filename)
    return filename



def fetch_overdue_tasks(assignee: str):
    """Fetch overdue tasks for the given assignee.

    Args:
        assignee (str): The assignee name.

    Returns:
        dict: Error or the response.
            The response is in this shape::
                {"tasks": [overdue_tasks....]}

    """
    cache_key = f"overdue:{assignee.lower()}"
    if redis_client.exists(cache_key):
        return eval(redis_client.get(cache_key))

    response = requests.get(f"{API_ROOT}/projects/?status=active")
    if response.status_code != 200:
        return {"error": "API call failed"}

    projects = response.json()
    overdue_tasks = []
    today = date.today()

    for project in projects:
        for task in project["tasks"]:
            try:
                due = date.fromisoformat(task["due_date"])
                if task["assigned_to"].lower() == assignee.lower() and task["status"] != "done" and due < today:
                    overdue_tasks.append(task)
            except Exception as error:
                continue

    result = {"tasks": overdue_tasks}
    redis_client.setex(cache_key, CACHE_TTL, str(result))  # Cache for 10 mins.

    return result


def fetch_all_tasks(assignee: str):
    """Fetch all tasks for the given assignee.

    Args:
        assignee (str): The assignee name.

    Returns:
        dict: Error or the response.
            The response is in this shape::
                {"tasks": [tasks....]}

    """
    cache_key = f"all:{assignee.lower()}"
    if redis_client.exists(cache_key):
        return eval(redis_client.get(cache_key))

    response = requests.get(f"{API_ROOT}/projects/?status=active")
    if response.status_code != 200:
        return {"error": "API call failed"}
    projects = response.json()
    all_tasks = []
    for project in projects:
        for task in project["tasks"]:
            if task["assigned_to"].lower() == assignee.lower():
                all_tasks.append(task)

    result = {"tasks": all_tasks}
    redis_client.setex(cache_key, CACHE_TTL, str(result))
    return result


def list_all_projects(_: str=""):
    """Return a list of all projects.

    Args:
        _ (str): Ignored input placeholder.

    Returns:
        list: List of project dictionaries or error.

    """
    cache_key = "projects:all"
    if redis_client.exists(cache_key):
        return eval(redis_client.get(cache_key))

    response = requests.get(f"{API_ROOT}/projects")

    if response.status_code == 200:
        data = response.json()
        redis_client.setex(cache_key, CACHE_TTL, str(data))
        return data

    return {"error": "Project API error"}


def get_project_by_id(prompt: str):
    """Parses project ID from prompt or raw string and returns project.

    Args:
        prompt (str): Input prompt or ID.

    Returns:
        dict: Project details or error message.

    """
    if not isinstance(prompt, str):
        prompt = str(prompt)

    # Check if it's an integer string like "1", "5" etc.
    if prompt.strip().isdigit():
        pid = prompt.strip()
    else:
        match = re.search(r"project[\s#]*(\d+)", prompt, re.IGNORECASE)
        if not match:
            return {"error": "No project ID found in prompt."}
        pid = match.group(1)

    cache_key = f"project:{pid}"
    if redis_client.exists(cache_key):
        return eval(redis_client.get(cache_key))

    response = requests.get(f"{API_ROOT}/projects/{pid}")
    if response.status_code == 200:
        data = response.json()
        redis_client.setex(cache_key, CACHE_TTL, str(data))
        return data

    return {"error": "Project not found"}

def unknown_prompt_fallback(_: str):
    """Fallback for unrecognized prompts.

    Args:
        _ (str): Ignored input string.

    Returns:
        dict: Default fallback message.

    """
    return {
        "message": "Sorry, I couldn’t find a tool to help with that. Please try a different query or be more specific."
    }


FetchOverdueTasksTool = Tool(
    name="FetchOverdueTasks",
    func=fetch_overdue_tasks,
    description="Fetch only overdue tasks assigned to a specific user",
    return_direct=True
)


FetchAllTasksTool = Tool(
    name="FetchAllTasks",
    func=fetch_all_tasks,
    description="Fetch all tasks assigned to a specific user",
    return_direct=True
)


ListProjectsTool = Tool(
    name="ListProjects",
    func=list_all_projects,
    description="List all projects",
    return_direct=True
)


GetProjectByIdTool = Tool(
    name="GetProjectById",
    func=get_project_by_id,
    description="Get a specific project and its tasks by ID",
    return_direct=True
)


FallbackTool = Tool(
    name="FallbackTool",
    func=unknown_prompt_fallback,
    description="Used when the prompt doesn’t match any known tools",
    return_direct=True
)


def agent_executor(prompt: str):
    """Main agent execution function for MCP-compatible flow.

    Args:
        prompt (str): Input user prompt.

    Returns:
        dict: Error or Structured response including redacted output and PDF.
            The response is in this shape::
                {"response": safe_output, "pdf": pdf_path}

    """
    tools = [
        FetchOverdueTasksTool,
        FetchAllTasksTool,
        ListProjectsTool,
        GetProjectByIdTool,
        FallbackTool
    ]
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        output_parser=StrOutputParser()
    )
    try:
        output = agent.invoke(prompt)
        output = str(output)
        safe_output = redact_pii(output)
        log_telemetry(prompt, safe_output)
        pdf_path = export_to_pdf(safe_output)

        return {"response": safe_output, "pdf": pdf_path}
    except Exception as error:
        return {"error": str(error)}
