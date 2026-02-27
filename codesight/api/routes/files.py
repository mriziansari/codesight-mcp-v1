from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from codesight.api.dependencies import get_graph

router = APIRouter()

class FileDetails(BaseModel):
    file: str
    dependencies: List[str]
    dependents: List[str]
    risk_score: float
    total_affected: int

@router.get("/files/{file_path:path}", response_model=FileDetails)
async def get_file_details(file_path: str, graph=Depends(get_graph)):
    if file_path not in graph.graph:
        raise HTTPException(status_code=404, detail="File not found")
    
    impact = graph.get_impact(file_path)
    
    return {
        "file": file_path,
        "dependencies": graph.get_dependencies(file_path),
        "dependents": graph.get_dependents(file_path),
        "risk_score": impact.get("risk_score", 0),
        "total_affected": impact.get("total_affected", 0)
    }