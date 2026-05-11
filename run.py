"""
Entry point — runs the FastAPI server via Uvicorn.

Usage:
    python run.py
"""

import uvicorn
from app.core.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )
