from fastapi import APIRouter, Depends
from pydantic import BaseModel

from codesight.api.dependencies import get_graph, get_store

router = APIRouter()

class StatsResponse(BaseModel):
    total_files: int
    total_dependencies: int
    indexed_symbols: int
    root_path: str

@router.get("/stats", response_model=StatsResponse)
async def get_stats(graph=Depends(get_graph)):
    return {
        "total_files": len(graph.graph.nodes),
        "total_dependencies": len(graph.graph.edges),
        "indexed_symbols": sum(1 for _ in graph.graph.nodes),  # Simplified
        "root_path": str(graph.root)
    }