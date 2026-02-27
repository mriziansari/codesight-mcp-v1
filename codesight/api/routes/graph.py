from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from codesight.api.dependencies import get_graph

router = APIRouter()

class Node(BaseModel):
    id: str
    name: str
    path: str
    dependents: int
    group: str  # "high", "medium", "low"

class Link(BaseModel):
    source: str
    target: str

class GraphResponse(BaseModel):
    nodes: List[Node]
    links: List[Link]

@router.get("/graph", response_model=GraphResponse)
async def get_graph_data(graph=Depends(get_graph)):
    from pathlib import Path
    
    nodes = []
    for node_id in graph.graph.nodes:
        dependents = len(list(graph.graph.predecessors(node_id)))
        nodes.append({
            "id": node_id,
            "name": Path(node_id).name,
            "path": node_id,
            "dependents": dependents,
            "group": "high" if dependents > 5 else "medium" if dependents > 0 else "low"
        })
    
    links = [
        {"source": s, "target": t}
        for s, t in graph.graph.edges
    ]
    
    return {"nodes": nodes, "links": links}