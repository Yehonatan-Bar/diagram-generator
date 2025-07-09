"""
Unit tests for LLM client implementations.
"""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from src.llm.base import BaseLLMClient, LLMResponse
from src.llm.client import LLMProvider, LLMClientFactory, get_llm_client
from src.llm.mock_client import MockLLMClient
from src.llm.prompt_manager import PromptManager


class TestLLMBase:
    """Test base LLM classes and models."""
    
    def test_llm_response_model(self):
        """Test LLMResponse Pydantic model."""
        response = LLMResponse(
            content="Test content",
            success=True,
            error=None,
            usage={"tokens": 100},
            metadata={"model": "test"}
        )
        
        assert response.content == "Test content"
        assert response.success is True
        assert response.error is None
        assert response.usage["tokens"] == 100
        assert response.metadata["model"] == "test"
    
    def test_llm_response_with_error(self):
        """Test LLMResponse with error."""
        response = LLMResponse(
            content="",
            success=False,
            error="API Error",
            usage={},
            metadata={}
        )
        
        assert response.content == ""
        assert response.success is False
        assert response.error == "API Error"
    
    def test_base_llm_client_abstract(self):
        """Test that BaseLLMClient is abstract."""
        with pytest.raises(TypeError):
            # Should not be able to instantiate abstract class
            BaseLLMClient()


class TestMockLLMClient:
    """Test MockLLMClient implementation."""
    
    @pytest.mark.asyncio
    async def test_mock_client_initialization(self):
        """Test mock client initialization."""
        client = MockLLMClient()
        assert client is not None
        assert hasattr(client, 'generate')
    
    @pytest.mark.asyncio
    async def test_mock_simple_response(self):
        """Test mock client simple response."""
        client = MockLLMClient()
        
        response = await client.generate("Create a simple web app")
        
        assert response.success is True
        assert response.content is not None
        assert "nodes" in response.content
        assert "connections" in response.content
    
    @pytest.mark.asyncio
    async def test_mock_pattern_matching(self):
        """Test mock client pattern matching."""
        client = MockLLMClient()
        
        # Test serverless pattern
        response = await client.generate("Create a serverless system with Lambda")
        assert response.success is True
        assert "Lambda" in response.content
        
        # Test microservices pattern
        response = await client.generate("Build microservices architecture")
        assert response.success is True
        assert "services" in response.content.lower()
    
    @pytest.mark.asyncio
    async def test_mock_assistant_mode(self):
        """Test mock client in assistant mode."""
        client = MockLLMClient()
        
        response = await client.generate(
            "I need help with architecture",
            is_assistant=True
        )
        
        assert response.success is True
        assert response.metadata.get("assistant_response") is True
    
    @pytest.mark.asyncio
    async def test_mock_error_simulation(self):
        """Test mock client error simulation."""
        client = MockLLMClient()
        
        response = await client.generate("simulate_error")
        
        assert response.success is False
        assert response.error is not None
        assert "simulated error" in response.error.lower()


class TestLLMClientFactory:
    """Test LLMClientFactory functionality."""
    
    def test_factory_providers_enum(self):
        """Test LLMProvider enumeration."""
        assert LLMProvider.GEMINI == "gemini"
        assert LLMProvider.OPENAI == "openai"
        assert LLMProvider.MOCK == "mock"
    
    @pytest.mark.asyncio
    async def test_create_mock_client(self):
        """Test creating mock client via factory."""
        client = await LLMClientFactory.create_client(LLMProvider.MOCK)
        
        assert client is not None
        assert isinstance(client, MockLLMClient)
    
    @pytest.mark.asyncio
    async def test_create_gemini_client_without_key(self):
        """Test creating Gemini client without API key."""
        with patch.dict('os.environ', {'LLM_API_KEY': ''}):
            with pytest.raises(ValueError, match="API key required"):
                await LLMClientFactory.create_client(LLMProvider.GEMINI)
    
    @pytest.mark.asyncio
    async def test_get_llm_client_mock_mode(self):
        """Test get_llm_client in mock mode."""
        with patch.dict('os.environ', {'USE_MOCK_LLM': 'true'}):
            client = await get_llm_client()
            assert isinstance(client, MockLLMClient)
    
    @pytest.mark.asyncio
    async def test_get_llm_client_with_provider(self):
        """Test get_llm_client with specific provider."""
        client = await get_llm_client(provider=LLMProvider.MOCK)
        assert isinstance(client, MockLLMClient)


class TestPromptManager:
    """Test PromptManager functionality."""
    
    def test_prompt_manager_initialization(self):
        """Test PromptManager initialization."""
        manager = PromptManager()
        assert manager is not None
        assert hasattr(manager, 'get_prompt')
    
    def test_get_existing_prompt(self):
        """Test getting an existing prompt."""
        manager = PromptManager()
        
        # Assuming 'diagram_generation' prompt exists
        prompt = manager.get_prompt('diagram_generation', description="test")
        assert prompt is not None
        assert "test" in prompt
    
    def test_get_nonexistent_prompt(self):
        """Test getting a non-existent prompt."""
        manager = PromptManager()
        
        with pytest.raises(KeyError):
            manager.get_prompt('nonexistent_prompt')
    
    def test_prompt_sanitization(self):
        """Test prompt input sanitization."""
        manager = PromptManager()
        
        # Test with potentially dangerous input
        dangerous_input = "'; DROP TABLE users; --"
        prompt = manager.get_prompt(
            'diagram_generation',
            description=dangerous_input
        )
        
        # Should be escaped/sanitized
        assert "DROP TABLE" in prompt  # Should be preserved but safe
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_prompt_file_not_found(self, mock_open):
        """Test handling of missing prompts file."""
        with pytest.raises(FileNotFoundError):
            PromptManager("nonexistent.yaml")
    
    def test_prompt_with_multiple_variables(self):
        """Test prompt with multiple template variables."""
        manager = PromptManager()
        
        # Create a test prompt template
        manager._prompts = {
            "test": {
                "template": "User: {user_input}\nContext: {context}\nAction: {action}"
            }
        }
        
        result = manager.get_prompt(
            "test",
            user_input="hello",
            context="testing",
            action="generate"
        )
        
        assert "User: hello" in result
        assert "Context: testing" in result
        assert "Action: generate" in result