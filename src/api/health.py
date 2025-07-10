"""
Health check endpoints
"""
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, status

from ..core.config import settings
from ..llm.client import get_llm_client
from ..core.logging import logger, FeatureTag, ModuleTag

router = APIRouter(tags=["health"])


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "environment": settings.environment
    }


@router.get("/health/ready", response_model=Dict[str, Any])
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available
    """
    checks = {
        "llm_client": False,
        "mock_mode": settings.use_mock_llm
    }
    
    try:
        # Check LLM client
        client = get_llm_client()
        if client:
            checks["llm_client"] = True
            checks["llm_provider"] = settings.llm_provider
    except Exception as e:
        logger.error(
            "LLM client check failed",
            feature=FeatureTag.API,
            module=ModuleTag.API_ENDPOINTS,
            function="readiness_check",
            error=e
        )
    
    # Overall status
    all_ready = all(checks.values()) if not settings.use_mock_llm else checks["llm_client"]
    
    return {
        "ready": all_ready,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """
    Liveness check - simple ping endpoint
    """
    return {"status": "alive"}