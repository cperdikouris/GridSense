import os
from fastapi import APIRouter, Body
import redis.asyncio as redis

router = APIRouter(prefix="/alerts", tags=["Live Alerts (Redis)"])

def get_redis():
    # Connect to the Redis Docker container using the .env variable
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=6379,
        decode_responses=True
    )

@router.post("/publish")
async def publish_alert(payload: dict = Body(...)):
    r = get_redis()
    alert_msg = payload.get("message", "Unknown System Fault")
    
    await r.publish("grid_alerts", alert_msg)
    await r.lpush("active_alerts", alert_msg)
    await r.ltrim("active_alerts", 0, 49) 
    
    await r.aclose()
    return {"status": "success", "message": "Alert broadcasted globally"}

@router.get("/active")
async def get_active_alerts():
    r = get_redis()
    alerts = await r.lrange("active_alerts", 0, -1)
    await r.aclose()
    
    return {"count": len(alerts), "alerts": alerts}