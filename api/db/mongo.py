import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

def get_mongo_client():
    return AsyncIOMotorClient(os.getenv("MONGO_URI"))