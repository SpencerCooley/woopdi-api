from celery_app.celery_app import celery_app
from .example_streaming_task import example_streaming_task
from .generate_image_with_logo_task import generate_image_with_logo_task

# Re-export the tasks
__all__ = [
    'example_streaming_task',
    'generate_image_with_logo_task'
]
