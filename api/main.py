from fastapi import FastAPI
from contextlib import asynccontextmanager

# IMPORT YOUR ROUTERS HERE
from api.routers import equipment
from api.routers import billing
from api.routers import sensors
from api.routers import grid
from api.routers import alerts

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("⚡ Powering up GridSense API...")
    yield
    print("🔌 Shutting down GridSense API...")

app = FastAPI(
    title="GridSense API", 
    description="Advanced Data Management - Final Assessment",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"status": "online", "message": "Welcome to the GridSense API!"}

# ATTACH YOUR ROUTERS HERE
app.include_router(equipment.router)
app.include_router(billing.router)
app.include_router(sensors.router)
app.include_router(grid.router)
app.include_router(alerts.router)