from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List
from api.db.neo4j import get_neo4j_driver

router = APIRouter(prefix="/grid", tags=["Grid Topology (Neo4j)"])

# --- PYDANTIC MODELS (From Rubric Section B.6) ---
class AffectedNode(BaseModel):
    node_id: str
    node_type: str
    name: str
    depth: int

class FaultImpactResponse(BaseModel):
    origin_id: str
    total_affected: int
    affected_nodes: List[AffectedNode]
# -------------------------------------------------

driver = get_neo4j_driver()

@router.get("/fault-impact/{node_id}", response_model=FaultImpactResponse)
async def get_fault_impact(node_id: str, max_depth: int = 6):
    if not isinstance(max_depth, int) or max_depth < 1 or max_depth > 10:
        raise HTTPException(status_code=400, detail="max_depth must be an integer between 1 and 10")
        
    cypher = f"""
    MATCH (origin) 
    WHERE origin.substation_id = $node_id OR origin.asset_id = $node_id OR origin.meter_id = $node_id OR origin.gsp_id = $node_id
    MATCH p = (origin)-[:FEEDS|SUPPLIES|CONNECTS_TO*1..{max_depth}]->(downstream)
    RETURN labels(downstream)[0] AS node_type,
           coalesce(downstream.substation_id, downstream.asset_id, downstream.meter_id) AS node_id,
           coalesce(downstream.name, 'Unknown') AS name,
           length(p) AS depth
    ORDER BY depth
    """
    
    async with driver.session() as session:
        result = await session.run(cypher, node_id=node_id)
        records = await result.data()
        
        # Convert raw dicts into the Pydantic models requested by the rubric
        affected = [AffectedNode(**r) for r in records]
        
        return FaultImpactResponse(
            origin_id=node_id,
            total_affected=len(affected),
            affected_nodes=affected
        )

@router.get("/restore-paths/{node_id}")
async def get_restore_paths(node_id: str):
    cypher = """
    MATCH (target) WHERE target.substation_id = $node_id OR target.asset_id = $node_id
    MATCH p = (gsp:GridSupplyPoint)-[*]->(target)
    RETURN [node in nodes(p) | coalesce(node.substation_id, node.asset_id, node.gsp_id)] AS path
    """
    async with driver.session() as session:
        result = await session.run(cypher, node_id=node_id)
        records = await result.data()
        return {"target_id": node_id, "alternative_paths": records}

@router.post("/nodes")
async def add_node(payload: dict = Body(...)):
    label = payload.get("label", "GenericNode")
    props = payload.get("properties", {})
    cypher = f"CREATE (n:{label} $props) RETURN n"
    
    async with driver.session() as session:
        await session.run(cypher, props=props)
        return {"status": "success", "message": f"{label} node created"}

@router.post("/relationships")
async def add_relationship(payload: dict = Body(...)):
    from_id = payload.get("from_id")
    to_id = payload.get("to_id")
    rel_type = payload.get("type", "CONNECTS_TO")
    
    cypher = f"""
    MATCH (a), (b)
    WHERE (a.substation_id=$from_id OR a.asset_id=$from_id OR a.gsp_id=$from_id)
      AND (b.substation_id=$to_id OR b.asset_id=$to_id OR b.meter_id=$to_id)
    MERGE (a)-[r:{rel_type}]->(b)
    """
    async with driver.session() as session:
        await session.run(cypher, from_id=from_id, to_id=to_id)
        return {"status": "success", "message": f"Relationship {rel_type} created"}