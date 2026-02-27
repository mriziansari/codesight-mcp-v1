from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from codesight.api.dependencies import get_vector_store, get_dependency_graph
from codesight.api.routes import stats, search, graph, files

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize heavy resources
    app.state.vector_store = get_vector_store()
    app.state.dependency_graph = get_dependency_graph()
    yield
    # Shutdown: cleanup if needed
    pass

app = FastAPI(
    title="CodeSight API",
    description="Code intelligence for AI-assisted development",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stats.router, prefix="/api", tags=["stats"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(graph.router, prefix="/api", tags=["graph"])
app.include_router(files.router, prefix="/api", tags=["files"])