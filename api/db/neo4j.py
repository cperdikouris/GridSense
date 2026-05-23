import os
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv

load_dotenv()

def get_neo4j_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pwd = os.getenv("NEO4J_PASSWORD")
    return AsyncGraphDatabase.driver(uri, auth=(user, pwd))