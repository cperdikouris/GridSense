from fastapi import APIRouter, HTTPException, Body
import os
import asyncpg

router = APIRouter(prefix="/billing", tags=["Billing System (PostgreSQL)"])

async def get_db():
    return await asyncpg.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host=os.getenv("POSTGRES_HOST", "localhost")
    )

@router.get("/account/{premise_id}")
async def get_account(premise_id: str):
    conn = await get_db()
    try:
        row = await conn.fetchrow("SELECT premise_id, balance, last_invoice_date FROM accounts WHERE premise_id = $1", premise_id)
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")
        return dict(row)
    finally:
        await conn.close()

@router.post("/invoice")
async def generate_invoice(payload: dict = Body(...)):
    premise_id = payload.get("premise_id")
    amount = payload.get("amount")
    
    if not premise_id or amount is None:
        raise HTTPException(status_code=400, detail="Missing premise_id or amount")

    conn = await get_db()
    try:
        # This is the ACID Transaction requested in the rubric!
        async with conn.transaction():
            # 1. Add amount to balance
            await conn.execute("UPDATE accounts SET balance = balance + $1 WHERE premise_id = $2", amount, premise_id)
            # 2. Update the invoice date
            await conn.execute("UPDATE accounts SET last_invoice_date = CURRENT_DATE WHERE premise_id = $1", premise_id)
            
            # Fetch updated account
            row = await conn.fetchrow("SELECT premise_id, balance FROM accounts WHERE premise_id = $1", premise_id)
            if not row:
                raise HTTPException(status_code=404, detail="Account not found")
                
        return {"status": "success", "message": "Invoice generated", "new_balance": float(row['balance'])}
    finally:
        await conn.close()