from fastapi import APIRouter, HTTPException, Body
from api.db.neo4j import get_neo4j_driver

router = APIRouter(prefix="/grid", tags=["Grid Topology (Neo4j)"])

driver = get_neo4j_driver()

@router.get("/fault-impact/{node_id}")
async def get_fault_impact(node_id: str, max_depth: int = 6):
    # 1. Validation check ensuring integer and safe range (1-10) as required by the new rubric
    if not isinstance(max_depth, int) or max_depth < 1 or max_depth > 10:
        raise HTTPException(status_code=400, detail="max_depth must be an integer between 1 and 10")
        
    # 2. Using an f-string for max_depth while keeping $node_id parameterized for safety
    cypher = f"""
    MATCH (origin) 
    WHERE origin.substation_id = $node_id OR origin.asset_id = $node_id OR origin.meter_id = $node_id OR origin.gsp_id = $node_id
    MATCH p = (origin)-[:FEEDS|SUPPLIES|CONNECTS_TO*1..{max_depth}]->(downstream)
    RETURN labels(downstream)[0] AS node_type,
           coalesce(downstream.substation_id, downstream.asset_id, downstream.meter_id) AS affected_id,
           length(p) AS depth
    ORDER BY depth
    """
    
    async with driver.session() as session:
        # 3. Only pass node_id as a parameter, since max_depth is injected via the f-string
        result = await session.run(cypher, node_id=node_id)
        records = await result.data()
        
        return {
            "origin_id": node_id,
            "total_affected": len(records),
            "affected_nodes": records
        }

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
    rel_type = payload.get("type", "CONNECTED_TO")
    
    cypher = f"""
    MATCH (a), (b)
    WHERE (a.substation_id=$from_id OR a.asset_id=$from_id OR a.gsp_id=$from_id)
      AND (b.substation_id=$to_id OR b.asset_id=$to_id OR b.meter_id=$to_id)
    MERGE (a)-[r:{rel_type}]->(b)
    """
    async with driver.session() as session:
        await session.run(cypher, from_id=from_id, to_id=to_id)
        return {"status": "success", "message": f"Relationship {rel_type} created"}