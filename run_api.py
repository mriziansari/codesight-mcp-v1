#!/usr/bin/env python3
import uvicorn
from codesight.api.server import app

if __name__ == "__main__":
    uvicorn.run(
        "codesight.api.server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )