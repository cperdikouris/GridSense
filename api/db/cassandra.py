import os
from cassandra.cluster import Cluster
from dotenv import load_dotenv

load_dotenv()

def get_cassandra_session():
    cluster = Cluster([os.getenv("CASSANDRA_HOST")])
    return cluster.connect()