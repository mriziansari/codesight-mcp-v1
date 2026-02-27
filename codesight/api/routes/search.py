from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List

from codesight.api.dependencies import get_store

router = APIRouter()

class SearchResult(BaseModel):
    id: str
    file: str
    symbol: str
    type: str
    line: int
    preview: str
    score: float

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]

@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(5, ge=1, le=20),
    store=Depends(get_store)
):
    # Auto-index on first search (simplified)
    results = store.search(q, n_results=limit)
    
    return {
        "query": q,
        "results": [
            {
                "id": r["id"],
                "file": r["metadata"]["file_path"],
                "symbol": r["metadata"]["symbol_name"],
                "type": r["metadata"]["symbol_type"],
                "line": r["metadata"]["start_line"],
                "preview": r["content"][:200],
                "score": 1 - r["distance"]
            }
            for r in results
        ]
    }