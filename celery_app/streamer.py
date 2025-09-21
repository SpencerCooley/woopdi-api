"""
Task streaming functionality for publishing updates to Redis channels.
This allows Celery tasks to publish progress and status updates via Redis.
"""

import redis
import json
import datetime
from contextlib import contextmanager
from typing import Any, Dict, Optional
from celery.app.task import Task
import os


class TaskStreamer:
    """
    A class for streaming task updates to Redis channels.
    This allows tasks to publish progress, status, and other information
    that can be consumed by WebSocket clients.
    """
    
    def __init__(self, task_id: str, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the TaskStreamer.
        
        Args:
            task_id: The ID of the Celery task
            redis_client: Optional Redis client instance. If not provided,
                         a new one will be created using environment settings.
        """
        self.task_id = task_id
        if redis_client:
            self.redis_client = redis_client
        else:
            # Use environment variables for Redis configuration
            redis_host = os.getenv('REDIS_HOST', 'redis')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=redis_db,
                decode_responses=False  # We'll handle JSON serialization ourselves
            )
    
    def update(self, message: str, type: str = "update", **kwargs: Any) -> None:
        """
        Publish an update to the task's Redis channel.
        
        Args:
            message: The message to send
            type: The type of update (e.g., "stage_start", "stage_end", "progress", "update")
            **kwargs: Additional data to include in the update
        """
        update = {
            "task_id": self.task_id,
            "message": message,
            "type": type,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            **kwargs
        }
        
        # Serialize to JSON and publish
        self.redis_client.publish(f"task:{self.task_id}", json.dumps(update))
    
    @contextmanager
    def stage(self, message: str, stage_num: Optional[int] = None, total: Optional[int] = None):
        """
        Context manager for tracking stages in a task.
        
        Args:
            message: Description of the stage
            stage_num: Current stage number (1-indexed)
            total: Total number of stages
        """
        self.update(message, type="stage_start", stage=stage_num, total_stages=total)
        try:
            yield self
        finally:
            self.update(f"Completed: {message}", type="stage_end")
    
    def progress(self, message: str, current: int, total: int, **data: Any) -> None:
        """
        Report progress for a task.
        
        Args:
            message: Description of the progress
            current: Current progress value
            total: Total progress value
            **data: Additional data to include in the progress update
        """
        self.update(
            message, 
            type="progress", 
            progress=current/total if total > 0 else 0,
            current=current, 
            total=total, 
            **data
        )


def get_task_streamer(task: Task) -> TaskStreamer:
    """
    Get a TaskStreamer instance for the current task.
    
    Args:
        task: The Celery task instance
        
    Returns:
        TaskStreamer: Instance for streaming updates
    """
    return TaskStreamer(task.request.id)