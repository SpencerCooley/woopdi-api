# define your pydantic models here for request and response.
from pydantic import BaseModel
from typing import Any, Optional

class GeneratePlanRequest(BaseModel):
    intent: str # give some context for the plan. "I want to get stronger, but I work every monday and tuesday"
    plan_type: str # strength, endurance, mobility, etc. 
    response_schema: object # tell the llm what you want your response to look like. 


class PlanResponse(BaseModel):
    plan: object #unstructured. 


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED
    result: Any = None
    ready: bool
    successful: Optional[bool] = None
    failed: Optional[bool] = None
    traceback: Optional[str] = None
    progress: Optional[dict] = None  # For tasks that report progress