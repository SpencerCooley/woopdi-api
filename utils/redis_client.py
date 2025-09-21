import redis
import os
from dotenv import load_dotenv


load_dotenv()

if os.getenv("IS_PROD") == "False":
    # Redis client for local development
    redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
else:
    # Redis client for production, requires username and password
    redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), decode_responses=True, username=os.getenv("REDIS_USER"), password=os.getenv("REDIS_PASSWORD"))
