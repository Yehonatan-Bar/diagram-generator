#!/usr/bin/env python3
"""
Run the diagram generation API server
"""
import sys
import uvicorn
from src.api.main import app
from src.core.config import settings

if __name__ == "__main__":
    # Configure uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level.lower(),
        reload=settings.environment == "development"
    )