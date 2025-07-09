"""
Unit tests for the dual-tag logging system.
"""
import json
import pytest
from datetime import datetime, timedelta

from src.core.logging import (
    FeatureTag, ModuleTag, StructuredLogger, logger,
    setup_logging
)


class TestLoggingEnums:
    """Test logging enumeration classes."""
    
    def test_feature_tags(self):
        """Test feature tag enumeration."""
        assert FeatureTag.API == "API"
        assert FeatureTag.AGENTS == "AGENTS"
        assert FeatureTag.TOOLS == "TOOLS"
        assert FeatureTag.LLM == "LLM"
        assert FeatureTag.CONFIG == "CONFIG"
        assert FeatureTag.HEALTH == "HEALTH"
        assert FeatureTag.VALIDATION == "VALIDATION"
    
    def test_module_tags(self):
        """Test module tag enumeration."""
        assert ModuleTag.API_MAIN == "api.main"
        assert ModuleTag.API_ENDPOINTS == "api.endpoints"
        assert ModuleTag.AGENT_DIAGRAM == "agent.diagram"
        assert ModuleTag.AGENT_ASSISTANT == "agent.assistant"
        assert ModuleTag.TOOL_BUILDER == "tool.builder"
        assert ModuleTag.TOOL_VALIDATOR == "tool.validator"
        assert ModuleTag.LLM_CLIENT == "llm.client"
        assert ModuleTag.CORE_CONFIG == "core.config"
        assert ModuleTag.CORE_LOGGING == "core.logging"


class TestStructuredLogger:
    """Test StructuredLogger class."""
    
    def test_logger_initialization(self):
        """Test logger initialization."""
        test_logger = StructuredLogger("test")
        assert test_logger is not None
        assert hasattr(test_logger, 'log')
        assert hasattr(test_logger, 'get_logs_by_feature')
    
    def test_basic_logging(self, caplog):
        """Test basic logging functionality."""
        test_logger = StructuredLogger("test")
        
        test_logger.info(
            "Test message",
            feature=FeatureTag.API,
            module=ModuleTag.API_MAIN,
            extra={"key": "value"}
        )
        
        # Check that log was recorded
        assert len(caplog.records) > 0
        record = caplog.records[-1]
        assert record.message == "Test message"
    
    def test_log_with_tags(self):
        """Test logging with feature and module tags."""
        test_logger = StructuredLogger("test")
        
        # Clear existing logs
        test_logger._logs.clear()
        
        test_logger.info(
            "Tagged message",
            feature=FeatureTag.LLM,
            module=ModuleTag.LLM_CLIENT,
            request_id="test-123"
        )
        
        # Get logs by feature
        llm_logs = test_logger.get_logs_by_feature(FeatureTag.LLM)
        assert len(llm_logs) > 0
        assert llm_logs[0]["message"] == "Tagged message"
        assert llm_logs[0]["feature"] == FeatureTag.LLM.value
        assert llm_logs[0]["module"] == ModuleTag.LLM_CLIENT.value
    
    def test_log_levels(self):
        """Test different log levels."""
        test_logger = StructuredLogger("test")
        test_logger._logs.clear()
        
        test_logger.debug("Debug message", feature=FeatureTag.CONFIG)
        test_logger.info("Info message", feature=FeatureTag.CONFIG)
        test_logger.warning("Warning message", feature=FeatureTag.CONFIG)
        test_logger.error("Error message", feature=FeatureTag.CONFIG)
        
        # Check logs by level
        info_logs = test_logger.get_logs_by_level("INFO")
        assert any(log["message"] == "Info message" for log in info_logs)
        
        error_logs = test_logger.get_logs_by_level("ERROR")
        assert any(log["message"] == "Error message" for log in error_logs)
    
    def test_performance_tracking(self):
        """Test performance tracking functionality."""
        test_logger = StructuredLogger("test")
        test_logger._logs.clear()
        
        # Log with duration
        test_logger.info(
            "Performance test",
            feature=FeatureTag.API,
            module=ModuleTag.API_ENDPOINTS,
            duration=150.5
        )
        
        # Get performance metrics
        metrics = test_logger.get_performance_metrics()
        assert FeatureTag.API.value in metrics
        assert metrics[FeatureTag.API.value]["count"] > 0
        assert "avg_duration" in metrics[FeatureTag.API.value]
    
    def test_error_summary(self):
        """Test error summary functionality."""
        test_logger = StructuredLogger("test")
        test_logger._logs.clear()
        
        # Log some errors
        test_logger.error("Error 1", feature=FeatureTag.LLM)
        test_logger.error("Error 2", feature=FeatureTag.LLM)
        test_logger.error("Error 3", feature=FeatureTag.API)
        
        # Get error summary
        summary = test_logger.get_error_summary()
        assert summary[FeatureTag.LLM.value] >= 2
        assert summary[FeatureTag.API.value] >= 1
    
    def test_log_filtering_by_time(self):
        """Test filtering logs by time range."""
        test_logger = StructuredLogger("test")
        test_logger._logs.clear()
        
        # Log some messages
        test_logger.info("Recent message", feature=FeatureTag.API)
        
        # Get logs from last minute
        recent_logs = test_logger.get_logs_by_time(
            start_time=datetime.now() - timedelta(minutes=1)
        )
        assert len(recent_logs) > 0
        assert recent_logs[0]["message"] == "Recent message"
        
        # Get logs from future (should be empty)
        future_logs = test_logger.get_logs_by_time(
            start_time=datetime.now() + timedelta(minutes=1)
        )
        assert len(future_logs) == 0
    
    def test_json_logging_format(self):
        """Test JSON logging format."""
        test_logger = StructuredLogger("test", log_format="json")
        
        # The format is set during initialization
        # Just verify logger works with JSON format
        test_logger.info(
            "JSON format test",
            feature=FeatureTag.CONFIG,
            extra_field="extra_value"
        )
        
        # Should not raise any exceptions
        assert True


class TestGlobalLogger:
    """Test the global logger instance."""
    
    def test_global_logger_exists(self):
        """Test that global logger is available."""
        assert logger is not None
        assert isinstance(logger, StructuredLogger)
    
    def test_global_logger_functionality(self):
        """Test global logger basic functionality."""
        # Clear logs
        logger._logs.clear()
        
        # Log a message
        logger.info(
            "Global logger test",
            feature=FeatureTag.HEALTH,
            module=ModuleTag.API_MAIN
        )
        
        # Verify it was logged
        health_logs = logger.get_logs_by_feature(FeatureTag.HEALTH)
        assert len(health_logs) > 0
        assert any(log["message"] == "Global logger test" for log in health_logs)