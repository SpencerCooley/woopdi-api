"""
Simple example task demonstrating how to use the TaskStreamer.
"""

from celery_app.celery_app import celery_app
from celery_app.streamer import get_task_streamer
import time


@celery_app.task(bind=True, name='celery_app.tasks.example_streaming_task')
def example_streaming_task(self,user_id: int = None, duration: int = 10) -> dict:
    """
    Example task that demonstrates how to use the TaskStreamer.
    
    Args:
        duration: Duration in seconds to simulate work
        
    Returns:
        dict: Result of the task
    """
    # Get the task streamer for this task
    streamer = get_task_streamer(self)
    
    try:
        # Initial update
        streamer.update("Starting example streaming task", type="task_start")
        
        # Simulate work with progress updates
        for i in range(duration):
            streamer.progress(
                f"Processing step {i+1}/{duration}",
                i+1,
                duration
            )
            time.sleep(1)
        
        streamer.update("Example streaming task completed successfully", type="task_end")
        
        return {
            "status": "completed",
            "message": f"Processed for {duration} seconds"
        }
        
    except Exception as e:
        streamer.update(f"Task failed with error: {str(e)}", type="task_error")
        return {
            "status": "failed",
            "error": str(e)
        }
    
# you can also just write regular tasks without updating to the websocket. There is an endpoint for polling the status of a task. 
# the websockets updates are mostly for crafting nice user experiences with real time updates 
# it works great for ai pipelines likethis:  text + img prompt ---> generate image ---(update ui with image url) ---(report to ui with generative progress)---> use image to generate video