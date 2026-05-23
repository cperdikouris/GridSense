import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def get_postgres_pool():
    return await asyncpg.create_pool(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host="localhost",
        port=5432
    )