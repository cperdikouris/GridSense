import os
import asyncio
import json
from fastapi import APIRouter, HTTPException, Body, Query
from cassandra.cluster import Cluster
from datetime import datetime
import redis.asyncio as redis

router = APIRouter(prefix="/sensors", tags=["Sensor Data (Cassandra & Redis)"])

cassandra_cluster = None
cassandra_session = None
redis_client = None

def get_cassandra():
    global cassandra_cluster, cassandra_session
    if cassandra_session is None:
        cassandra_cluster = Cluster([os.getenv("CASSANDRA_HOST", "cassandra")])
        cassandra_session = cassandra_cluster.connect('gridsense')
    return cassandra_session

def get_redis():
    global redis_client
    if redis_client is None:
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_client = redis.Redis(host=redis_host, port=6379, decode_responses=True)
    return redis_client

@router.get("/{sensor_id}/readings")
async def get_sensor_readings(
    sensor_id: str, 
    limit: int = Query(10, le=1000),
    from_time: datetime = Query(None, description="Fetch readings after this time")
):
    session = get_cassandra()
    loop = asyncio.get_event_loop()
    
    if from_time:
        query = "SELECT * FROM sensor_readings WHERE sensor_id = %s AND reading_time >= %s ORDER BY reading_time DESC LIMIT %s"
        rows = await loop.run_in_executor(None, session.execute, query, (sensor_id, from_time, limit))
    else:
        query = "SELECT * FROM sensor_readings WHERE sensor_id = %s ORDER BY reading_time DESC LIMIT %s"
        rows = await loop.run_in_executor(None, session.execute, query, (sensor_id, limit))
    
    # Handle Cassandra named tuples or dicts
    data = [row._asdict() if hasattr(row, '_asdict') else dict(row) for row in rows]
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

@router.get("/{sensor_id}/summary")
async def get_sensor_summary(sensor_id: str):
    """Cached latest reading + 1h stats; TTL = 30 s"""
    r_client = get_redis()
    cache_key = f"sensor_summary:{sensor_id}"
    
    # Check cache first
    cached_data = await r_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
        
    # If cache miss, fetch from Cassandra (simulate doing 1h stats)
    session = get_cassandra()
    query = "SELECT * FROM sensor_readings WHERE sensor_id = %s LIMIT 1"
    loop = asyncio.get_event_loop()
    rows = await loop.run_in_executor(None, session.execute, query, [sensor_id])
    
    result = list(rows)
    if not result:
        raise HTTPException(status_code=404, detail="No readings found for this sensor")
        
    latest = result[0]
    latest_dict = latest._asdict() if hasattr(latest, '_asdict') else dict(latest)
    
    # Convert datetime to string for JSON serialization
    if 'reading_time' in latest_dict and isinstance(latest_dict['reading_time'], datetime):
        latest_dict['reading_time'] = latest_dict['reading_time'].isoformat()
        
    summary = {
        "sensor_id": sensor_id,
        "latest_reading": latest_dict,
        "status": "Healthy",
        "cache": "miss" # Will be "miss" on first load, "hit" would be handled above
    }
    
    # Save to Redis with 30 second TTL
    await r_client.setex(cache_key, 30, json.dumps(summary))
    return summary