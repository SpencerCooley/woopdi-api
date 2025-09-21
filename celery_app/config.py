import os
from celery.schedules import crontab

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

class CeleryConfig:
    broker_url = CELERY_BROKER_URL
    result_backend = CELERY_RESULT_BACKEND
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    timezone = 'UTC'
    enable_utc = True
    worker_prefetch_multiplier = 1
    task_track_started = True
    task_acks_late = True
    worker_send_task_events = True
    task_send_sent_event = True
    broker_connection_retry_on_startup = True
