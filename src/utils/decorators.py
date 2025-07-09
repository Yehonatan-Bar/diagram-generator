import time
import functools
import asyncio
from typing import Callable, Any
from ..core.logging import logger, FeatureTag, ModuleTag


def log_execution_time(feature: FeatureTag, module: ModuleTag):
    """
    Decorator to log function execution time
    
    Usage:
        @log_execution_time(FeatureTag.DIAGRAM_GENERATION, ModuleTag.DIAGRAM_TOOLS)
        def my_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            function_name = func.__name__
            
            try:
                logger.debug(
                    f"Starting execution of {function_name}",
                    feature=feature,
                    module=module,
                    function=function_name,
                    params={"args": str(args)[:100], "kwargs": str(kwargs)[:100]}
                )
                
                result = await func(*args, **kwargs)
                
                execution_time_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"Successfully completed {function_name}",
                    feature=feature,
                    module=module,
                    function=function_name,
                    execution_time_ms=execution_time_ms
                )
                
                return result
                
            except Exception as e:
                execution_time_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Error in {function_name}",
                    feature=feature,
                    module=module,
                    function=function_name,
                    error=e,
                    execution_time_ms=execution_time_ms
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            function_name = func.__name__
            
            try:
                logger.debug(
                    f"Starting execution of {function_name}",
                    feature=feature,
                    module=module,
                    function=function_name,
                    params={"args": str(args)[:100], "kwargs": str(kwargs)[:100]}
                )
                
                result = func(*args, **kwargs)
                
                execution_time_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"Successfully completed {function_name}",
                    feature=feature,
                    module=module,
                    function=function_name,
                    execution_time_ms=execution_time_ms
                )
                
                return result
                
            except Exception as e:
                execution_time_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Error in {function_name}",
                    feature=feature,
                    module=module,
                    function=function_name,
                    error=e,
                    execution_time_ms=execution_time_ms
                )
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def with_error_handling(feature: FeatureTag, module: ModuleTag, fallback_value: Any = None):
    """
    Decorator to handle errors with logging
    
    Usage:
        @with_error_handling(FeatureTag.DIAGRAM_GENERATION, ModuleTag.VALIDATION, fallback_value={})
        def my_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Handled error in {func.__name__}",
                    feature=feature,
                    module=module,
                    function=func.__name__,
                    error=e,
                    params={"args": str(args)[:100], "kwargs": str(kwargs)[:100]}
                )
                return fallback_value
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Handled error in {func.__name__}",
                    feature=feature,
                    module=module,
                    function=func.__name__,
                    error=e,
                    params={"args": str(args)[:100], "kwargs": str(kwargs)[:100]}
                )
                return fallback_value
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator