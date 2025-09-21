from langchain.callbacks.base import BaseCallbackHandler
import redis
import os
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

if os.getenv("IS_PROD") == "False":
    # Redis client for local development
    redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
else:
    # Redis client for production, requires username and password
    redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), decode_responses=True, username=os.getenv("REDIS_USER"), password=os.getenv("REDIS_PASSWORD"))

# Model configuration
MODEL_CONFIG = {
    "o3-mini": {
        "provider": "openai",
        "model_name": "o3-mini",
        "api_key_env": "OPENAI_API_KEY",
        "default": True
    },
    "o3-max": {
        "provider": "openai",
        "model_name": "gpt-4",
        "api_key_env": "OPENAI_API_KEY"
    }
}

def get_default_model() -> str:
    for model_name, config in MODEL_CONFIG.items():
        if config.get("default", False):
            return model_name
    raise ValueError("No default model configured")

class StreamingCallbackHandler(BaseCallbackHandler):
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.last_token = None

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if token == self.last_token:
            return
        self.last_token = token
        redis_client.publish(f"task:{self.task_id}", token)

    def on_llm_end(self, response, **kwargs) -> None:
        redis_client.publish(f"task:{self.task_id}", "[DONE]") 


def upload_to_gcp_bucket(source_file_path, destination_blob_name):
    """
    Uploads a file to a GCP bucket. Bucket name and service account key are read from environment variables.
    Args:
        source_file_path: Path to the local file to upload (e.g., 'local_file.txt').
        destination_blob_name: Name of the file in the bucket (e.g., 'uploaded_file.txt').
    """
    bucket_name = os.getenv("GCP_BUCKET_NAME")
    service_account_key = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
    if not bucket_name:
        raise ValueError("GCP_BUCKET_NAME environment variable not set")
    if not service_account_key:
        raise ValueError("GCP_SERVICE_ACCOUNT_KEY environment variable not set")
    # Initialize the client with your service account credentials
    client = storage.Client.from_service_account_json(service_account_key)
    # Get the bucket
    bucket = client.get_bucket(bucket_name)
    # Create a blob (object) in the bucket
    blob = bucket.blob(destination_blob_name)
    # Upload the file
    blob.upload_from_filename(source_file_path)
    print(f"File {source_file_path} uploaded to {bucket_name}/{destination_blob_name}.")

# # Example usage
# bucket_name = 'my-gcp-bucket'
# source_file_path = 'local_file.txt'  # Path to the file on your local machine
# destination_blob_name = 'uploaded_file.txt'  # Name of the file in the bucket

# upload_to_gcp_bucket(source_file_path, destination_blob_name)


