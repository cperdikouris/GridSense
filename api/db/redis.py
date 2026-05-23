import os
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

def get_redis_client():
    return redis.from_url(os.getenv("REDIS_URI"))