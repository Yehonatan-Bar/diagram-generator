import google.generativeai as genai
from typing import Optional, Dict, Any
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base import BaseLLMClient, LLMResponse
from ..core.logging import logger, FeatureTag, ModuleTag
from ..utils.decorators import log_execution_time


class GeminiClient(BaseLLMClient):
    """Google Gemini LLM client implementation"""
    
    def __init__(self, api_key: str, model: str = "gemini-pro", **kwargs):
        super().__init__(api_key, model, **kwargs)
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)
        
        # Safety settings
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        logger.info(
            f"Initialized Gemini client with model {model}",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.LLM_CLIENT,
            function="__init__",
            params={"model": model}
        )
    
    @log_execution_time(FeatureTag.DIAGRAM_GENERATION, ModuleTag.LLM_CLIENT)
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate response from Gemini"""
        try:
            # Combine system prompt and user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Configure generation settings
            generation_config = genai.types.GenerationConfig(
                candidate_count=1,
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=kwargs.get("top_p", 0.95),
                top_k=kwargs.get("top_k", 40)
            )
            
            logger.debug(
                "Sending request to Gemini",
                feature=FeatureTag.DIAGRAM_GENERATION,
                module=ModuleTag.LLM_CLIENT,
                function="generate",
                params={
                    "prompt_length": len(prompt),
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            # Generate response (Gemini SDK is synchronous)
            response = await asyncio.to_thread(
                self.client.generate_content,
                full_prompt,
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )
            
            # Extract response text
            if response.text:
                content = response.text
            else:
                # Handle blocked responses
                logger.warning(
                    "Gemini response was blocked by safety filters",
                    feature=FeatureTag.DIAGRAM_GENERATION,
                    module=ModuleTag.LLM_CLIENT,
                    function="generate",
                    params={"safety_ratings": str(response.safety_ratings)}
                )
                raise ValueError("Response blocked by safety filters")
            
            # Extract usage information if available
            usage = None
            if hasattr(response, 'usage_metadata'):
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count
                }
            
            logger.info(
                "Successfully generated response from Gemini",
                feature=FeatureTag.DIAGRAM_GENERATION,
                module=ModuleTag.LLM_CLIENT,
                function="generate",
                params={
                    "response_length": len(content),
                    "usage": usage
                }
            )
            
            return LLMResponse(
                content=content,
                usage=usage,
                model=self.model,
                finish_reason="stop"
            )
            
        except Exception as e:
            logger.error(
                f"Error generating response from Gemini: {str(e)}",
                feature=FeatureTag.DIAGRAM_GENERATION,
                module=ModuleTag.LLM_CLIENT,
                function="generate",
                error=e
            )
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def generate_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        **kwargs
    ) -> LLMResponse:
        """Generate response with automatic retry on failure"""
        return await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            **kwargs
        )
    
    def validate_response(self, response: str) -> bool:
        """Validate if response is valid JSON for diagram specification"""
        if not response or not response.strip():
            return False
        
        # Basic validation - check if it looks like JSON
        trimmed = response.strip()
        return trimmed.startswith('{') and trimmed.endswith('}')
    
    async def close(self):
        """Cleanup resources"""
        # Gemini client doesn't need explicit cleanup
        pass