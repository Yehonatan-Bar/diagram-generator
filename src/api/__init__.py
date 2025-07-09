"""
FastAPI endpoints for diagram generation service
"""
from .main import app
from .diagram import router as diagram_router
from .health import router as health_router

__all__ = ["app", "diagram_router", "health_router"]