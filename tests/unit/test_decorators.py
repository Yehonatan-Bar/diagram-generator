"""
Unit tests for utility decorators.
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock

from src.utils.decorators import log_execution_time, with_error_handling
from src.core.logging import FeatureTag, ModuleTag


class TestLogExecutionTime:
    """Test log_execution_time decorator."""
    
    @pytest.mark.asyncio
    async def test_async_function_timing(self):
        """Test timing of async functions."""
        
        @log_execution_time(
            feature=FeatureTag.API,
            module=ModuleTag.API_ENDPOINTS
        )
        async def slow_function():
            await asyncio.sleep(0.1)
            return "done"
        
        with patch('src.core.logging.logger.info') as mock_log:
            result = await slow_function()
            
            assert result == "done"
            
            # Check that logging was called
            mock_log.assert_called()
            call_args = mock_log.call_args
            
            # Check log message
            assert "slow_function" in call_args[0][0]
            assert "completed in" in call_args[0][0]
            
            # Check kwargs
            kwargs = call_args[1]
            assert kwargs['feature'] == FeatureTag.API
            assert kwargs['module'] == ModuleTag.API_ENDPOINTS
            assert 'duration' in kwargs
            assert kwargs['duration'] >= 100  # At least 100ms
    
    def test_sync_function_timing(self):
        """Test timing of sync functions."""
        
        @log_execution_time(
            feature=FeatureTag.TOOLS,
            module=ModuleTag.TOOL_BUILDER
        )
        def quick_function(x, y):
            return x + y
        
        with patch('src.core.logging.logger.info') as mock_log:
            result = quick_function(2, 3)
            
            assert result == 5
            
            # Check that logging was called
            mock_log.assert_called()
            call_args = mock_log.call_args
            
            # Check log content
            assert "quick_function" in call_args[0][0]
            assert kwargs := call_args[1]
            assert kwargs['feature'] == FeatureTag.TOOLS
            assert kwargs['module'] == ModuleTag.TOOL_BUILDER
    
    @pytest.mark.asyncio
    async def test_function_with_exception(self):
        """Test timing when function raises exception."""
        
        @log_execution_time(
            feature=FeatureTag.LLM,
            module=ModuleTag.LLM_CLIENT
        )
        async def failing_function():
            await asyncio.sleep(0.05)
            raise ValueError("Test error")
        
        with patch('src.core.logging.logger.info') as mock_log:
            with pytest.raises(ValueError):
                await failing_function()
            
            # Should still log execution time even if exception
            mock_log.assert_called()
            kwargs = mock_log.call_args[1]
            assert 'duration' in kwargs
            assert kwargs['duration'] >= 50  # At least 50ms


class TestWithErrorHandling:
    """Test with_error_handling decorator."""
    
    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        """Test error handling for async functions."""
        
        @with_error_handling(
            feature=FeatureTag.AGENTS,
            module=ModuleTag.AGENT_DIAGRAM,
            default_return={"success": False}
        )
        async def risky_function():
            raise RuntimeError("Something went wrong")
        
        with patch('src.core.logging.logger.error') as mock_error:
            result = await risky_function()
            
            # Should return default value
            assert result == {"success": False}
            
            # Should log error
            mock_error.assert_called()
            call_args = mock_error.call_args
            
            assert "Error in risky_function" in call_args[0][0]
            kwargs = call_args[1]
            assert kwargs['feature'] == FeatureTag.AGENTS
            assert kwargs['module'] == ModuleTag.AGENT_DIAGRAM
            assert 'error_type' in kwargs
            assert kwargs['error_type'] == 'RuntimeError'
    
    def test_sync_error_handling(self):
        """Test error handling for sync functions."""
        
        @with_error_handling(
            feature=FeatureTag.VALIDATION,
            module=ModuleTag.TOOL_VALIDATOR,
            default_return=None
        )
        def problematic_function(x):
            if x == 0:
                raise ZeroDivisionError("Cannot divide by zero")
            return 10 / x
        
        with patch('src.core.logging.logger.error') as mock_error:
            # Should handle error and return default
            result = problematic_function(0)
            assert result is None
            
            # Check error logging
            mock_error.assert_called()
            kwargs = mock_error.call_args[1]
            assert kwargs['error_type'] == 'ZeroDivisionError'
            
            # Should work normally when no error
            result = problematic_function(2)
            assert result == 5.0
    
    @pytest.mark.asyncio
    async def test_no_default_return(self):
        """Test error handling without default return value."""
        
        @with_error_handling(
            feature=FeatureTag.API,
            module=ModuleTag.API_MAIN
        )
        async def no_default_function():
            raise Exception("Test exception")
        
        with patch('src.core.logging.logger.error'):
            result = await no_default_function()
            
            # Should return None when no default specified
            assert result is None
    
    def test_preserves_function_signature(self):
        """Test that decorator preserves function signature."""
        
        @with_error_handling(
            feature=FeatureTag.CONFIG,
            module=ModuleTag.CORE_CONFIG
        )
        def original_function(a: int, b: str = "default") -> str:
            """Original function docstring."""
            return f"{a}-{b}"
        
        # Check function name and docstring preserved
        assert original_function.__name__ == "original_function"
        assert original_function.__doc__ == "Original function docstring."
    
    @pytest.mark.asyncio
    async def test_combined_decorators(self):
        """Test combining both decorators."""
        
        @log_execution_time(
            feature=FeatureTag.API,
            module=ModuleTag.API_ENDPOINTS
        )
        @with_error_handling(
            feature=FeatureTag.API,
            module=ModuleTag.API_ENDPOINTS,
            default_return={"error": "failed"}
        )
        async def complex_function(should_fail=False):
            await asyncio.sleep(0.05)
            if should_fail:
                raise ValueError("Requested failure")
            return {"success": True}
        
        with patch('src.core.logging.logger.info') as mock_info:
            with patch('src.core.logging.logger.error') as mock_error:
                # Test success case
                result = await complex_function(should_fail=False)
                assert result == {"success": True}
                mock_info.assert_called()  # Timing logged
                
                # Test failure case
                result = await complex_function(should_fail=True)
                assert result == {"error": "failed"}
                mock_error.assert_called()  # Error logged
                
                # Both decorators should work together
                assert mock_info.call_count >= 2  # Called for both executions