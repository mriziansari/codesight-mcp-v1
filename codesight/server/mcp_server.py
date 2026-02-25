import asyncio
from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import json
import sys
from typing import List
from mcp.server.stdio import stdio_server
from pathlib import Path
from codesight.config import settings
from codesight.index.file_discovery import FileDiscovery
from codesight.index.git_tracker import GitTracker
from codesight.index.vector_store import VectorStore
from codesight.index.file_reader import FileReader

# Initialize global tracker
git_tracker = None

app = Server("codesight-mcp")
_vector_store = None
_indexed = False

def get_vector_store():
    global _vector_store
    if _vector_store is None:
        from codesight.config import settings
        index_dir = settings.codebase_path / ".codesight" / "vectors"
        index_dir.parent.mkdir(parents=True, exist_ok=True)
        _vector_store = VectorStore(index_dir)
    return _vector_store

@app.list_resources()

async def list_resources() -> List[Resource]:
    """
    List all available codebase resources
    """
    return [
        Resource(
            uri = "codebase://status",
            name="Server Status",
            description="Current indexing status and state",
            mimeType= "application/json",
        ),
        Resource(
            uri="codebase://git/status",
            name="Git Repository Status",
            description="Git repository information and statistics",
            mimeType="application/json"
        )
    ]



@app.list_tools()

async def list_tools() -> List[Tool]:
    """
    List all available tools
    """
    return [
        Tool(
            name="initialize_codebase",
            description="Initialize the codebase for indexing",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the codebase root"
                    }
                }
            }
        ),
        Tool(
            name="git_blame",
            description="Get line-by-line author information for a specific file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Relative path to file (e.g., 'src/main.py')"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="search_code",
            description="Search codebase by natural language description",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for (e.g., 'authentication', 'database connection')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results (default 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )
    ]

@app.call_tool()

async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
    """
    Call a specific tool
    """
    if name == "initialize_codebase":
        path_str = arguments.get("path") if arguments else None
        if path_str:
            path = Path(path_str)
            settings.codebase_path = path
        else:
            path = settings.codebase_path

        discovery = FileDiscovery(path)
        count = discovery.count()   
        
        return [TextContent(
            type="text", 
            text=f"Found {count} files to index in {path}"
        )]
    
    elif name == "git_blame":
        
        
        file_path_str = arguments.get("file_path", "")
        if not file_path_str:
            raise ValueError("file_path is required")
    
        full_path = settings.codebase_path / file_path_str
        tracker = GitTracker(settings.codebase_path)
    
        if not tracker.is_valid():
            return [TextContent(type="text", text="Not a git repository")]
    
        blame = tracker.get_file_blame(full_path)
    
        if not blame:
            return [TextContent(type="text", text=f"No git history for {file_path_str}")]
    
        # Format output
        lines = []
        for hunk in blame[:10]:  # Limit to first 10 hunks
            lines.append(f"Lines {hunk['line_start']}-{hunk['line_start'] + hunk['lines_in_hunk']-1}: {hunk['author']}")
    
        return [TextContent(
            type="text", 
            text=f"Git blame for {file_path_str}:\n" + "\n".join(lines)
        )]
    
    elif name == "search_code":
        query = arguments.get("query", "")
        limit = arguments.get("limit", 5)
        
        if not query:
            raise ValueError("Query is required")

        store = get_vector_store()

        #Auto index if not done yet
        global _indexed

        if not _indexed:
            # Index files
            reader = FileReader(settings.codebase_path)
            discovery = FileDiscovery(settings.codebase_path)

            files = list(discovery.discover())
            py_files = [f for f in files if f.suffix == '.py'][:20]
            
            
            for file_path in py_files:
                try:
                    content = reader.read(file_path)
                    store.add_file(content)
                except Exception as e:
                    print(f"Error indexing file {file_path}: {e}", file=sys.stderr)
            
            _indexed = True
        
        # Ensure codebase is indexed
        if not _indexed:
            return [TextContent(
                type="text", 
                text="Codebase not indexed. Run 'initialize_codebase' first."
            )]
        
        # Search using vector store
        results = store.search(query, n_results=limit)
        
        if not results:
            return [TextContent(
                type="text", 
                text=f"No results found for '{query}'"
            )]
        
        # Format response
        lines = [f"Found {len(results)} results for '{query}':\n"]
        for i, r in enumerate(results, 1):
            meta = r['metadata']
            lines.append(f"{i}. `{meta['symbol_name']}` ({meta['symbol_type']}) in `{meta['file_path']}`")
            lines.append(f"   Line {meta['start_line']}")
            lines.append(f"   ```python\n   {r['content'][:200]}...\n   ```\n")
    
        return [TextContent(type="text", text="\n".join(lines))]
    
    raise ValueError(f"Tool {name} not found")

@app.read_resource()
# read codebase status and git repo

async def read_resource(uri: str) -> str:
    uri_str = str(uri)
    if uri_str == "codebase://status" or uri_str == "codebase://status/":
        return json.dumps({"status": "active", "files_indexed": 0})
    elif uri_str == "codebase://git/status" or uri_str == "codebase://git/status/":
        tracker = GitTracker(settings.codebase_path)
        if tracker.is_valid():
            #Get basic repo info
            repo = tracker.repo
            head = repo.head

            return json.dumps({
                "is_git_repo": True,
                "branch": head.name if not repo.head_is_detached else "Detached HEAD",
                "last_commit": str(head.target) if head.target else None,
                "commit_count": len(list(repo.walk(repo.head.target))) if head.target else 0
            })
        else:
            return json.dumps({
                "is_git_repo": False,
                "branch": None,
                "last_commit": None,
                "commit_count": 0,
                "message": "No git repository found"
            })
    
    raise ValueError(f"Unknown resource: {uri}")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream, 
            app.create_initialization_options()
            )

if __name__ == "__main__":
    asyncio.run(main())

