from pydantic_settings import BaseSettings
from typing import List, Literal
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Settings
    api_title: str = "Diagram Generator API"
    api_version: str = "1.0.0"
    api_description: str = "Convert natural language to cloud architecture diagrams"
    
    # LLM Settings
    llm_provider: Literal["gemini", "openai", "mock"] = "gemini"
    llm_api_key: str = ""
    llm_model: str = "gemini-pro"
    use_mock_llm: bool = False
    max_retry_attempts: int = 3
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    
    # Diagram Settings
    supported_nodes: List[str] = ["EC2", "RDS", "LoadBalancer", "SQS", "Lambda", "S3"]
    temp_dir: str = "/tmp/diagrams"
    cleanup_temp_files: bool = True
    diagram_direction: Literal["TB", "LR", "BT", "RL"] = "LR"
    diagram_format: Literal["png", "jpg", "svg", "pdf"] = "png"
    
    # Logging Settings
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"
    enable_request_logging: bool = True
    
    # Security Settings
    api_key_header: str = "X-API-Key"
    require_api_key: bool = False
    allowed_api_keys: List[str] = []
    cors_origins: List[str] = ["*"]
    
    # Server Settings
    environment: str = "development"
    
    # Performance Settings
    request_timeout: int = 30
    max_concurrent_requests: int = 100
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Allow extra fields from environment
        extra = "ignore"
        
        # Custom parsing for lists
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name in ["supported_nodes", "allowed_api_keys", "cors_origins"]:
                return [x.strip() for x in raw_val.split(",") if x.strip()]
            return raw_val


# Global settings instance
settings = Settings()


# Helper functions
def get_temp_dir() -> Path:
    """Get and ensure temp directory exists"""
    temp_path = Path(settings.temp_dir)
    temp_path.mkdir(parents=True, exist_ok=True)
    return temp_path


def is_mock_mode() -> bool:
    """Check if running in mock mode"""
    return settings.use_mock_llm or settings.llm_provider == "mock"


def get_llm_config() -> dict:
    """Get LLM configuration as dict"""
    return {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        "api_key": settings.llm_api_key if not is_mock_mode() else None
    }