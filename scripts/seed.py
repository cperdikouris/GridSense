import asyncio
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Database Drivers
import asyncpg
from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import AsyncGraphDatabase
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args

# Load environment variables from .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

async def seed_postgres():
    print("Seeding PostgreSQL (100 Accounts)...")
    conn = await asyncpg.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host="localhost"
    )
    
    # Generate 100 accounts idempotently
    for i in range(1, 101):
        premise_id = f"PREM_{10000 + i}"
        balance = round(random.uniform(0, 500), 2)
        date = datetime.now().date() - timedelta(days=random.randint(1, 30))
        
        await conn.execute("""
            INSERT INTO accounts (premise_id, balance, last_invoice_date)
            VALUES ($1, $2, $3)
            ON CONFLICT (premise_id) DO NOTHING
        """, premise_id, balance, date)
    
    await conn.close()
    print("PostgreSQL Seeding Complete.")

async def seed_mongodb():
    print("Seeding MongoDB (30 Equipment Records)...")
    client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
    db = client.gridsense
    collection = db.equipment
    
    # Check if already seeded to maintain idempotency
    count = await collection.count_documents({})
    if count >= 30:
        print("MongoDB already seeded. Skipping.")
        return

    equipment_data = []
    # 10 Transformers
    for i in range(1, 11):
        equipment_data.append({
            "asset_id": f"TX_00{i}_A", "type": "Transformer",
            "metadata": {"firmware_version": f"3.{random.randint(0,9)}", "oil_level": "Normal"}
        })
    # 10 Smart Meters
    for i in range(1, 11):
        equipment_data.append({
            "asset_id": f"SM_EQ_{i}", "type": "SmartMeter",
            "metadata": {"rated_voltage": 240, "communication": "LTE"}
        })
    # 10 Relays
    for i in range(1, 11):
        equipment_data.append({
            "asset_id": f"RLY_{i}", "type": "Relay",
            "metadata": {"trip_settings": {"overcurrent_amps": 500}}
        })
        
    await collection.insert_many(equipment_data)
    print("MongoDB Seeding Complete.")

async def seed_neo4j():
    print("Seeding Neo4j (Grid Topology)...")
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pwd = os.getenv("NEO4J_PASSWORD")
    driver = AsyncGraphDatabase.driver(uri, auth=(user, pwd))
    
    cypher_query = """
    // Ensure Constraints
    MERGE (g:GridSupplyPoint {gsp_id: "GSP_NORTH"})
    SET g.name = "Northern Grid Supply Point", g.voltage_kV = 132
    
    WITH g
    UNWIND range(1, 10) AS s_id
    MERGE (s:Substation {substation_id: "SS_" + s_id})
    MERGE (g)-[:FEEDS {feeder_id: "F_" + s_id}]->(s)
    
    WITH s, s_id
    UNWIND range(1, 4) AS t_idx
    WITH s, s_id, (s_id * 10) + t_idx AS t_id
    MERGE (t:Transformer {asset_id: "TX_" + t_id})
    MERGE (s)-[:SUPPLIES {cable_id: "CB_" + t_id}]->(t)
    
    WITH t, t_id
    UNWIND range(1, 5) AS m_idx
    WITH t, t_id, (t_id * 10) + m_idx AS m_id
    MERGE (m:SmartMeter {meter_id: "SM_" + m_id, premise_id: "PREM_" + m_id})
    MERGE (t)-[:CONNECTS_TO]->(m)
    """
    
    async with driver.session() as session:
        await session.run(cypher_query)
    
    await driver.close()
    print("Neo4j Seeding Complete.")

def seed_cassandra():
    print("Seeding Cassandra (50,000 Sensor Readings)... This may take a minute.")
    cluster = Cluster([os.getenv("CASSANDRA_HOST")])
    session = cluster.connect('gridsense')
    
    # Check if already seeded (Idempotency)
    row = session.execute("SELECT count(*) FROM sensor_readings LIMIT 1").one()
    if row and row[0] > 0:
        print("Cassandra already seeded. Skipping.")
        return

    insert_statement = session.prepare("""
        INSERT INTO sensor_readings (sensor_id, reading_time, metric_type, value, unit, quality_flag)
        VALUES (?, ?, ?, ?, ?, ?)
    """)
    
    insert_metric_statement = session.prepare("""
        INSERT INTO sensor_readings_by_metric (metric_type, reading_time, sensor_id, value, unit, quality_flag)
        VALUES (?, ?, ?, ?, ?, ?)
    """)

    metrics = [('voltage', 'V'), ('current', 'A'), ('power_factor', 'ratio')]
    sensors = [f"SENSOR_{i}" for i in range(1, 21)]
    
    # Generate 50,000 rows (20 sensors * 2500 readings each)
    base_time = datetime.now()
    
    # We will do this in standard batches so it doesn't crash the container
    count = 0
    for sensor in sensors:
        for i in range(2500):
            metric, unit = random.choice(metrics)
            val = random.uniform(220, 240) if metric == 'voltage' else random.uniform(10, 50)
            r_time = base_time - timedelta(minutes=i)
            
            # Insert into main table
            session.execute_async(insert_statement, (sensor, r_time, metric, val, unit, 0))
            # Insert into our TODO table
            session.execute_async(insert_metric_statement, (metric, r_time, sensor, val, unit, 0))
            count += 1
            
            if count % 10000 == 0:
                print(f"... inserted {count} records ...")
                
    print("Cassandra Seeding Complete.")

async def main():
    await seed_postgres()
    await seed_mongodb()
    await seed_neo4j()
    # Cassandra uses a synchronous driver, so we call it normally
    seed_cassandra()
    print("\n✅ DATA FACTORY FINISHED: All databases are fully seeded!")

if __name__ == "__main__":
    asyncio.run(main())