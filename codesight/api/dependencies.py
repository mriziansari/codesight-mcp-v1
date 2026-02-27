from functools import lru_cache
from pathlib import Path
from fastapi import Request

from codesight.config import settings
from codesight.index.vector_store import VectorStore
from codesight.index.dependency_graph import DependencyGraph

# Singleton pattern for heavy resources
@lru_cache()
def get_vector_store() -> VectorStore:
    index_dir = settings.codebase_path / ".codesight" / "vectors"
    index_dir.parent.mkdir(parents=True, exist_ok=True)
    return VectorStore(index_dir)

@lru_cache()
def get_dependency_graph() -> DependencyGraph:
    graph = DependencyGraph(settings.codebase_path)
    graph.build()
    return graph

# FastAPI dependency injection
def get_store(request: Request) -> VectorStore:
    return request.app.state.vector_store

def get_graph(request: Request) -> DependencyGraph:
    return request.app.state.dependency_graph