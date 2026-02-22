#!/usr/bin/env python3
import typer
from pathlib import Path
from codesight.index.file_discovery import FileDiscovery
from codesight.server.mcp_server import main as server_main

app = typer.Typer()

@app.command()
def init(path: Path = typer.Option(".", help="Path to codebase")):
    """Initialize codesight index for a codebase"""
    typer.echo(f"Initializing CodeSight for: {path.absolute()}")
    discovery = FileDiscovery(path)
    count = discovery.count()
    typer.echo(f"Found {count} files to index")

@app.command()
def server():
    """Start MCP server"""
    import asyncio
    asyncio.run(server_main())

if __name__ == "__main__":
    app()