"""
Unit tests for configuration and settings management.
"""
import os
import pytest
from pydantic import ValidationError

from src.core.config import Settings, LLMProvider, get_temp_dir, is_mock_mode, get_llm_config


class TestSettings:
    """Test Settings configuration class."""
    
    def test_default_settings(self):
        """Test default settings initialization."""
        settings = Settings()
        assert settings.api_title == "Diagram Generator API"
        assert settings.api_version == "1.0.0"
        assert settings.environment == "test"
        assert settings.log_level == "WARNING"
    
    def test_llm_provider_enum(self):
        """Test LLM provider enumeration."""
        assert LLMProvider.GEMINI == "gemini"
        assert LLMProvider.OPENAI == "openai"
        assert LLMProvider.MOCK == "mock"
    
    def test_supported_nodes_parsing(self):
        """Test parsing of supported nodes from string."""
        settings = Settings(supported_nodes="EC2,RDS,Lambda")
        assert settings.get_supported_nodes() == ["EC2", "RDS", "Lambda"]
    
    def test_cors_origins_parsing(self):
        """Test parsing of CORS origins."""
        settings = Settings(cors_origins="http://localhost:3000,https://example.com")
        assert settings.get_cors_origins() == ["http://localhost:3000", "https://example.com"]
        
        settings_all = Settings(cors_origins="*")
        assert settings_all.get_cors_origins() == ["*"]
    
    def test_api_keys_parsing(self):
        """Test parsing of allowed API keys."""
        settings = Settings(allowed_api_keys="key1,key2,key3")
        assert settings.get_allowed_api_keys() == ["key1", "key2", "key3"]
        
        settings_empty = Settings(allowed_api_keys="")
        assert settings_empty.get_allowed_api_keys() == []


class TestHelperFunctions:
    """Test helper functions in config module."""
    
    def test_get_temp_dir(self):
        """Test getting temporary directory."""
        temp_dir = get_temp_dir()
        assert isinstance(temp_dir, str)
        assert len(temp_dir) > 0
    
    def test_is_mock_mode(self):
        """Test mock mode detection."""
        # Current test environment has USE_MOCK_LLM=true
        assert is_mock_mode() is True
        
        # Test with different settings
        os.environ["USE_MOCK_LLM"] = "false"
        assert is_mock_mode() is False
        
        # Reset
        os.environ["USE_MOCK_LLM"] = "true"
    
    def test_get_llm_config(self):
        """Test getting LLM configuration."""
        config = get_llm_config()
        assert isinstance(config, dict)
        assert "provider" in config
        assert "api_key" in config
        assert "model" in config
        assert "temperature" in config
        assert "max_tokens" in config


class TestEnvironmentVariables:
    """Test environment variable handling."""
    
    def test_env_override(self):
        """Test that environment variables override defaults."""
        os.environ["API_TITLE"] = "Test API"
        os.environ["API_VERSION"] = "2.0.0"
        
        settings = Settings()
        assert settings.api_title == "Test API"
        assert settings.api_version == "2.0.0"
        
        # Cleanup
        del os.environ["API_TITLE"]
        del os.environ["API_VERSION"]
    
    def test_boolean_env_parsing(self):
        """Test parsing of boolean environment variables."""
        os.environ["CLEANUP_TEMP_FILES"] = "false"
        settings = Settings()
        assert settings.cleanup_temp_files is False
        
        os.environ["CLEANUP_TEMP_FILES"] = "true"
        settings = Settings()
        assert settings.cleanup_temp_files is True
        
        # Cleanup
        del os.environ["CLEANUP_TEMP_FILES"]