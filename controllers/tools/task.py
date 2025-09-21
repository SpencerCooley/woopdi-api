"""
Controller for managing tools tasks.
"""
from typing import Dict, Any
from celery_app.tasks.example_streaming_task import example_streaming_task
from celery_app.tasks.generate_image_with_logo_task import generate_image_with_logo_task


def run_task(task_name: str, task_params: Dict[str, Any] = {}) -> Dict[str, Any]:
    """
    Run a Celery task by name with provided parameters.

    Args:
        task_name: Name of the task to run
        task_params: Parameters to pass to the task

    Returns:
        dict: Celery task result with task ID
    """
    # Map task names to actual task functions
    task_map = {
        "example_streaming": example_streaming_task,
        "generate_image_with_logo": generate_image_with_logo_task
    }

    # Check if the task exists
    if task_name not in task_map:
        raise ValueError(f"Unknown task: {task_name}")

    # Get the task function
    task_func = task_map[task_name]

    # Queue the task for background execution
    task_result = task_func.delay(**task_params)

    # Return the Celery result directly
    return task_result
