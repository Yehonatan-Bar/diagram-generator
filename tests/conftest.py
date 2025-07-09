"""
Pytest configuration and shared fixtures for all tests.
"""
import os
import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Set test environment variables before importing app
os.environ["USE_MOCK_LLM"] = "true"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["ENVIRONMENT"] = "test"
os.environ["CLEANUP_TEMP_FILES"] = "true"

from src.api.main import app
from src.core.config import settings
from src.llm.client import get_llm_client
from src.llm.mock_client import MockLLMClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_llm_client():
    """Get a mock LLM client for testing."""
    return MockLLMClient()


@pytest.fixture
def test_settings():
    """Get test settings."""
    return settings


@pytest.fixture
def sample_diagram_spec():
    """Sample diagram specification for testing."""
    return {
        "nodes": [
            {"type": "EC2", "name": "WebServer"},
            {"type": "RDS", "name": "Database"},
            {"type": "LoadBalancer", "name": "ALB"}
        ],
        "connections": [
            {"from": "ALB", "to": "WebServer"},
            {"from": "WebServer", "to": "Database"}
        ],
        "clusters": []
    }


@pytest.fixture
def sample_invalid_spec():
    """Sample invalid diagram specification for testing."""
    return {
        "nodes": [
            {"type": "InvalidType", "name": "Server"},
            {"type": "EC2"}  # Missing name
        ],
        "connections": [
            {"from": "NonExistent", "to": "Server"}
        ]
    }


@pytest.fixture
def temp_cleanup():
    """Ensure temp files are cleaned up after tests."""
    yield
    # Cleanup any temp files created during tests
    import shutil
    temp_dir = settings.get_temp_dir()
    if os.path.exists(temp_dir):
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception:
                pass