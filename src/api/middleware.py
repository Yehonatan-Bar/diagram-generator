"""
Custom middleware for the API
"""
import time
import uuid
from fastapi import Request, Response

from ..core.logging import logger, FeatureTag, ModuleTag


async def logging_middleware(request: Request, call_next):
    """
    Log all incoming requests and responses
    """
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Start timer
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Incoming request: {request.method} {request.url.path}",
        feature=FeatureTag.API,
        module=ModuleTag.API,
        function="logging_middleware",
        params={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown",
            "request_id": request_id
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(duration)
    
    # Log response
    logger.info(
        f"Request completed: {request.method} {request.url.path}",
        feature=FeatureTag.API,
        module=ModuleTag.API,
        function="logging_middleware",
        params={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_seconds": duration,
            "request_id": request_id
        }
    )
    
    return response