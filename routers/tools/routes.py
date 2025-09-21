from fastapi import APIRouter, HTTPException, WebSocket, Depends
from typing import Dict, Any
from types_definitions.tools import GeneratePlanRequest, PlanResponse, TaskResponse, TaskStatusResponse
import controllers
from celery.result import AsyncResult
from .websocket_handler import handle_task_updates
from dependencies.dependencies import get_db, get_current_user
from sqlalchemy.orm import Session
from models.user import User

router = APIRouter(
    prefix="/tools",
    tags=["Tools"],
    responses={404: {"description": "Not found"}},
)


@router.post("/task/{task_name}", response_model=TaskResponse)
async def run_tool_task(
    task_name: str,
    task_params: Dict[str, Any] = {},
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generic endpoint to run a Celery task by name with parameters.
    Requires authentication.

    Args:
        task_name: Name of the task to run
        task_params: Parameters to pass to the task
        db: Database session
        current_user: Authenticated user

    Returns:
        TaskResponse: Celery task result with task ID
    """
    try:
        # Add user_id to task parameters if not already provided
        if 'user_id' not in task_params:
            task_params['user_id'] = current_user.id

        # Call the controller function that returns a Celery result
        celery_result = controllers.tools.task.run_task(task_name, task_params)

        # Return the properly typed response
        return TaskResponse(
            task_id=celery_result.id,
            status=celery_result.status,
            message=f"Task '{task_name}' queued successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error queuing task: {str(e)}")


@router.get("/task/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of a running task by task ID.
    Users can only check status of their own tasks.

    Args:
        task_id: The Celery task ID to check
        db: Database session
        current_user: Authenticated user

    Returns:
        TaskStatusResponse: Current task status and result
    """
    try:
        # Get the AsyncResult object
        result = AsyncResult(task_id)

        return TaskStatusResponse(
            task_id=task_id,
            status=result.status,
            result=result.result,
            ready=result.ready(),
            successful=result.successful() if result.ready() else None,
            failed=result.failed() if result.ready() else None,
            traceback=str(result.traceback) if result.failed() else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking task status: {str(e)}")


@router.websocket("/task/{task_id}/ws")
async def websocket_task_updates(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for receiving real-time updates for a specific task.
    
    Args:
        websocket: The WebSocket connection
        task_id: The task ID to listen for updates on
    """
    await websocket.accept()
    try:
        await handle_task_updates(websocket, task_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
