from celery import Celery
from .config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, CeleryConfig

celery_app = Celery(
    "celery_app",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

# Configure using the CeleryConfig class
celery_app.config_from_object(CeleryConfig)

# Optional: Set namespace for environment variables
celery_app.conf.namespace = 'CELERY'

# Import all tasks
from celery_app import tasks   

if __name__ == "__main__":
    celery_app.start()
