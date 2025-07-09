"""
Main FastAPI application setup
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core.config import settings
from ..core.logging import logger, FeatureTag, ModuleTag
from .diagram import router as diagram_router
from .health import router as health_router
from .middleware import logging_middleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Manage application lifecycle
    """
    logger.info(
        "Starting diagram generation API service",
        feature=FeatureTag.API,
        module=ModuleTag.API,
        function="lifespan",
        params={
            "environment": settings.environment,
            "llm_provider": settings.llm_provider,
            "version": "0.1.0"
        }
    )
    
    yield
    
    logger.info(
        "Shutting down diagram generation API service",
        feature=FeatureTag.API,
        module=ModuleTag.API,
        function="lifespan"
    )


# Create FastAPI app
app = FastAPI(
    title="AI Diagram Generator",
    description="Transform natural language descriptions into cloud architecture diagrams",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.middleware("http")(logging_middleware)

# Include routers
app.include_router(health_router)
app.include_router(diagram_router, prefix="/api/v1")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Handle uncaught exceptions globally
    """
    logger.error(
        f"Unhandled exception: {str(exc)}",
        feature=FeatureTag.API,
        module=ModuleTag.API,
        function="global_exception_handler",
        params={
            "path": request.url.path,
            "method": request.method
        },
        error=exc
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": request.headers.get("X-Request-ID", "unknown")
        }
    )