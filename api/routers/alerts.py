import os
from fastapi import APIRouter, Body
import redis.asyncio as redis

router = APIRouter(prefix="/alerts", tags=["Live Alerts (Redis)"])

def get_redis():
    # Connect to the Redis Docker container
    return redis.Redis(
        host="localhost", # In a full Docker network, this would be the container name
        port=6379,
        decode_responses=True
    )

@router.post("/publish")
async def publish_alert(payload: dict = Body(...)):
    r = get_redis()
    alert_msg = payload.get("message", "Unknown System Fault")
    
    # 1. Broadcast it live to anyone listening (Pub/Sub)
    await r.publish("grid_alerts", alert_msg)
    
    # 2. Save it in a quick-access list so the dashboard can read it
    await r.lpush("active_alerts", alert_msg)
    # Keep only the 50 most recent alerts so we don't run out of RAM
    await r.ltrim("active_alerts", 0, 49) 
    
    await r.aclose()
    return {"status": "success", "message": "Alert broadcasted globally"}

@router.get("/active")
async def get_active_alerts():
    r = get_redis()
    # Fetch the entire list of active alerts instantly from RAM
    alerts = await r.lrange("active_alerts", 0, -1)
    await r.aclose()
    
    return {"count": len(alerts), "alerts": alerts}