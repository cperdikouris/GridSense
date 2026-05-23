import os
import asyncio
from fastapi import APIRouter, HTTPException, Body, Query
from cassandra.cluster import Cluster
from datetime import datetime

router = APIRouter(prefix="/sensors", tags=["Sensor Data (Cassandra)"])

cassandra_cluster = None
cassandra_session = None

def get_cassandra():
    global cassandra_cluster, cassandra_session
    if cassandra_session is None:
        # Connect to the Docker container
        cassandra_cluster = Cluster([os.getenv("CASSANDRA_HOST")])
        cassandra_session = cassandra_cluster.connect('gridsense')
    return cassandra_session

@router.get("/{sensor_id}/readings")
async def get_sensor_readings(sensor_id: str, limit: int = Query(10, le=1000)):
    session = get_cassandra()
    query = "SELECT * FROM sensor_readings WHERE sensor_id = %s ORDER BY reading_time DESC LIMIT %s"
    
    # Cassandra uses standard threads. We run it in the background so it doesn't freeze our async API.
    loop = asyncio.get_event_loop()
    rows = await loop.run_in_executor(None, session.execute, query, (sensor_id, limit))
    
    data = [row._asdict() for row in rows]
    return {"sensor_id": sensor_id, "count": len(data), "readings": data}

@router.post("/readings")
async def ingest_reading(payload: dict = Body(...)):
    session = get_cassandra()
    query = """
        INSERT INTO sensor_readings (sensor_id, reading_time, metric_type, value, unit, quality_flag)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    r_time = datetime.now()
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, session.execute, query, (
        payload['sensor_id'], r_time, payload['metric_type'], 
        float(payload['value']), payload['unit'], payload.get('quality_flag', 0)
    ))
    
    return {"status": "success", "message": f"Reading inserted for {payload['sensor_id']}"}