from typing import Optional, Dict, Any
from enum import Enum

from .base import BaseLLMClient
from .gemini_client import GeminiClient
from ..core.config import settings, is_mock_mode
from ..core.logging import logger, FeatureTag, ModuleTag


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    MOCK = "mock"


class LLMClientFactory:
    """Factory for creating LLM clients"""
    
    @staticmethod
    def create_client(
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> BaseLLMClient:
        """
        Create an LLM client based on provider
        
        Args:
            provider: LLM provider name (defaults to settings)
            api_key: API key (defaults to settings)
            model: Model name (defaults to settings)
            **kwargs: Additional provider-specific configuration
            
        Returns:
            LLM client instance
        """
        # Use settings defaults if not provided
        provider = provider or settings.llm_provider
        api_key = api_key or settings.llm_api_key
        model = model or settings.llm_model
        
        # Check if mock mode is enabled
        if is_mock_mode() or provider == LLMProvider.MOCK:
            logger.info(
                "Creating mock LLM client",
                feature=FeatureTag.DIAGRAM_GENERATION,
                module=ModuleTag.LLM_CLIENT,
                function="create_client",
                params={"provider": "mock", "model": model}
            )
            from .mock_client import MockLLMClient
            return MockLLMClient(api_key="mock", model=model, **kwargs)
        
        # Validate API key
        if not api_key:
            raise ValueError(f"API key required for provider: {provider}")
        
        # Create client based on provider
        if provider == LLMProvider.GEMINI:
            logger.info(
                f"Creating Gemini client with model: {model}",
                feature=FeatureTag.DIAGRAM_GENERATION,
                module=ModuleTag.LLM_CLIENT,
                function="create_client",
                params={"provider": provider, "model": model}
            )
            return GeminiClient(api_key=api_key, model=model, **kwargs)
        
        elif provider == LLMProvider.OPENAI:
            logger.info(
                f"Creating OpenAI client with model: {model}",
                feature=FeatureTag.DIAGRAM_GENERATION,
                module=ModuleTag.LLM_CLIENT,
                function="create_client",
                params={"provider": provider, "model": model}
            )
            from .openai_client import OpenAIClient
            return OpenAIClient(api_key=api_key, model=model, **kwargs)
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")


# Convenience function
def get_llm_client(**kwargs) -> BaseLLMClient:
    """Get LLM client with default settings"""
    return LLMClientFactory.create_client(**kwargs)