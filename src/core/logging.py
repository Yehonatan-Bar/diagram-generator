import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
import structlog
from pythonjsonlogger import jsonlogger


class FeatureTag(Enum):
    """User-facing features for logging categorization"""
    DIAGRAM_GENERATION = "diagram_generation"
    ASSISTANT = "assistant"
    HEALTH_CHECK = "health_check"
    API_REQUEST = "api_request"
    API = "api"
    AUTHENTICATION = "authentication"
    FILE_MANAGEMENT = "file_management"
    VALIDATION = "validation"


class ModuleTag(Enum):
    """Internal modules for logging categorization"""
    API_ENDPOINTS = "api_endpoints"
    LLM_CLIENT = "llm_client"
    DIAGRAM_TOOLS = "diagram_tools"
    AGENT_FRAMEWORK = "agent_framework"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    MIDDLEWARE = "middleware"
    UTILITIES = "utilities"


class StructuredLogger:
    """
    Two-dimensional logging system for feature and module tracking
    with comprehensive parameter capture and analysis capabilities
    """
    
    def __init__(self, log_format: str = "json", log_file: Optional[str] = None):
        self.log_format = log_format
        self.log_file = log_file
        self.logs: List[Dict[str, Any]] = []  # In-memory storage for analysis
        
        # Configure structlog
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]
        
        if log_format == "json":
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())
        
        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        self._logger = structlog.get_logger()
        
        # Setup file handler if specified
        if self.log_file:
            self._setup_file_handler()
    
    def _setup_file_handler(self):
        """Setup file logging with JSON formatter"""
        import logging
        
        file_handler = logging.FileHandler(self.log_file)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
    
    def log(
        self,
        level: str,
        message: str,
        feature: FeatureTag,
        module: ModuleTag,
        function: str,
        params: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
        execution_time_ms: Optional[float] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """
        Log an event with comprehensive context and dual tagging
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Human-readable log message
            feature: User-facing feature tag
            module: Internal module tag
            function: Function name where log originated
            params: Parameters and their values
            error: Exception object if applicable
            execution_time_ms: Execution time in milliseconds
            user_id: User identifier if applicable
            request_id: Request identifier for tracing
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "tags": {
                "feature": feature.value,
                "module": module.value
            },
            "context": {
                "function": function,
                "parameters": params or {},
                "execution_time_ms": execution_time_ms,
                "user_id": user_id,
                "request_id": request_id
            },
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": None  # Will be populated by structlog
            } if error else None
        }
        
        # Remove None values
        entry = {k: v for k, v in entry.items() if v is not None}
        entry["context"] = {k: v for k, v in entry["context"].items() if v is not None}
        
        # Store in memory for analysis
        self.logs.append(entry)
        
        # Log using structlog
        log_method = getattr(self._logger, level.lower())
        log_method(
            message,
            **entry
        )
    
    def debug(self, message: str, feature: FeatureTag, module: ModuleTag, **kwargs):
        """Convenience method for DEBUG logging"""
        self.log("DEBUG", message, feature, module, **kwargs)
    
    def info(self, message: str, feature: FeatureTag, module: ModuleTag, **kwargs):
        """Convenience method for INFO logging"""
        self.log("INFO", message, feature, module, **kwargs)
    
    def warning(self, message: str, feature: FeatureTag, module: ModuleTag, **kwargs):
        """Convenience method for WARNING logging"""
        self.log("WARNING", message, feature, module, **kwargs)
    
    def error(self, message: str, feature: FeatureTag, module: ModuleTag, **kwargs):
        """Convenience method for ERROR logging"""
        self.log("ERROR", message, feature, module, **kwargs)
    
    def critical(self, message: str, feature: FeatureTag, module: ModuleTag, **kwargs):
        """Convenience method for CRITICAL logging"""
        self.log("CRITICAL", message, feature, module, **kwargs)
    
    # Analysis methods
    def get_logs_by_feature(self, feature: FeatureTag) -> List[Dict[str, Any]]:
        """Filter logs by feature tag"""
        return [log for log in self.logs if log["tags"]["feature"] == feature.value]
    
    def get_logs_by_module(self, module: ModuleTag) -> List[Dict[str, Any]]:
        """Filter logs by module tag"""
        return [log for log in self.logs if log["tags"]["module"] == module.value]
    
    def get_logs_by_level(self, level: str) -> List[Dict[str, Any]]:
        """Filter logs by level"""
        return [log for log in self.logs if log["level"] == level.upper()]
    
    def get_logs_by_time_range(self, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        """Filter logs by time range"""
        return [
            log for log in self.logs
            if start <= datetime.fromisoformat(log["timestamp"]) <= end
        ]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors"""
        errors = [log for log in self.logs if log["level"] in ["ERROR", "CRITICAL"]]
        
        error_summary = {
            "total_errors": len(errors),
            "by_feature": {},
            "by_module": {},
            "by_type": {}
        }
        
        for error in errors:
            # By feature
            feature = error["tags"]["feature"]
            error_summary["by_feature"][feature] = error_summary["by_feature"].get(feature, 0) + 1
            
            # By module
            module = error["tags"]["module"]
            error_summary["by_module"][module] = error_summary["by_module"].get(module, 0) + 1
            
            # By error type
            if error.get("error"):
                error_type = error["error"]["type"]
                error_summary["by_type"][error_type] = error_summary["by_type"].get(error_type, 0) + 1
        
        return error_summary
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from logs"""
        timed_logs = [
            log for log in self.logs 
            if log.get("context", {}).get("execution_time_ms") is not None
        ]
        
        if not timed_logs:
            return {"message": "No performance data available"}
        
        metrics = {
            "by_feature": {},
            "by_module": {},
            "overall": {
                "count": len(timed_logs),
                "total_time_ms": sum(log["context"]["execution_time_ms"] for log in timed_logs),
                "avg_time_ms": sum(log["context"]["execution_time_ms"] for log in timed_logs) / len(timed_logs)
            }
        }
        
        # Group by feature
        for log in timed_logs:
            feature = log["tags"]["feature"]
            if feature not in metrics["by_feature"]:
                metrics["by_feature"][feature] = {"count": 0, "total_time_ms": 0}
            
            metrics["by_feature"][feature]["count"] += 1
            metrics["by_feature"][feature]["total_time_ms"] += log["context"]["execution_time_ms"]
        
        # Calculate averages
        for feature, data in metrics["by_feature"].items():
            data["avg_time_ms"] = data["total_time_ms"] / data["count"]
        
        return metrics
    
    def export_logs(self, filepath: str, format: str = "json"):
        """Export logs to file"""
        path = Path(filepath)
        
        if format == "json":
            with open(path, "w") as f:
                json.dump(self.logs, f, indent=2)
        elif format == "csv":
            import csv
            
            if not self.logs:
                return
            
            # Flatten logs for CSV
            flattened_logs = []
            for log in self.logs:
                flat_log = {
                    "timestamp": log["timestamp"],
                    "level": log["level"],
                    "message": log["message"],
                    "feature": log["tags"]["feature"],
                    "module": log["tags"]["module"],
                    "function": log.get("context", {}).get("function", ""),
                    "execution_time_ms": log.get("context", {}).get("execution_time_ms", ""),
                    "error_type": log.get("error", {}).get("type", "") if log.get("error") else ""
                }
                flattened_logs.append(flat_log)
            
            with open(path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=flattened_logs[0].keys())
                writer.writeheader()
                writer.writerows(flattened_logs)
    
    def clear_logs(self):
        """Clear in-memory log storage"""
        self.logs.clear()


# Initialize global logger instance
from ..core.config import settings

logger = StructuredLogger(
    log_format=settings.log_format,
    log_file=None  # Can be configured to write to file
)