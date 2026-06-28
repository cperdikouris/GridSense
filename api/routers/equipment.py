from fastapi import APIRouter, HTTPException, Body
from api.db.mongo import get_mongo_client

router = APIRouter(prefix="/equipment", tags=["Equipment Database (MongoDB)"])

def get_collection():
    client = get_mongo_client()
    return client.gridsense.equipment

@router.get("/{asset_id}")
async def get_equipment(asset_id: str):
    collection = get_collection()
    item = await collection.find_one({"asset_id": asset_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return item

@router.post("/")
async def create_equipment(payload: dict = Body(...)):
    if "asset_id" not in payload:
        raise HTTPException(status_code=400, detail="Missing required field: asset_id")
        
    collection = get_collection()
    existing = await collection.find_one({"asset_id": payload["asset_id"]})
    if existing:
        raise HTTPException(status_code=409, detail="Equipment with this asset_id already exists")
        
    await collection.insert_one(payload.copy())
    return {"status": "success", "message": f"Equipment {payload['asset_id']} created."}

@router.patch("/{asset_id}")
async def update_equipment(asset_id: str, payload: dict = Body(...)):
    collection = get_collection()
    
    # Use $set to only update the fields provided in the payload
    result = await collection.update_one(
        {"asset_id": asset_id},
        {"$set": payload}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Equipment not found")
        
    return {"status": "success", "message": f"Equipment {asset_id} updated."}