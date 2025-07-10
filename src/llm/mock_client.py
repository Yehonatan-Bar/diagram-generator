import json
import re
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
import random

from .base import BaseLLMClient, LLMResponse
from ..core.logging import logger, FeatureTag, ModuleTag


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing and development"""
    
    def __init__(self, api_key: str = "mock", model: str = "mock", **kwargs):
        super().__init__(api_key, model, **kwargs)
        
        # Load mock responses
        self.mock_responses = self._load_mock_responses()
        self.response_delay = kwargs.get("response_delay", 0.5)  # Simulate API delay
        
        logger.info(
            f"Initialized MockLLMClient with {len(self.mock_responses)} response patterns",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.LLM_CLIENT,
            function="__init__",
            params={"pattern_count": len(self.mock_responses)}
        )
    
    def _load_mock_responses(self) -> Dict[str, Any]:
        """Load mock response patterns"""
        mock_data_path = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "mock_responses.json"
        
        # Default mock responses if file doesn't exist
        default_responses = {
            "basic_web_app": {
                "input_patterns": [
                    r".*load\s*balancer.*ec2.*database.*",
                    r".*web\s*application.*server.*database.*",
                    r".*application\s*load\s*balancer.*web.*rds.*"
                ],
                "response": {
                    "nodes": [
                        {"type": "LoadBalancer", "name": "ALB", "properties": {"scheme": "internet-facing"}},
                        {"type": "EC2", "name": "WebServer1", "properties": {"instance_type": "t3.micro"}},
                        {"type": "EC2", "name": "WebServer2", "properties": {"instance_type": "t3.micro"}},
                        {"type": "RDS", "name": "Database", "properties": {"engine": "postgres"}}
                    ],
                    "connections": [
                        {"from": "ALB", "to": "WebServer1", "label": "http"},
                        {"from": "ALB", "to": "WebServer2", "label": "http"},
                        {"from": "WebServer1", "to": "Database", "label": "sql"},
                        {"from": "WebServer2", "to": "Database", "label": "sql"}
                    ],
                    "clusters": [
                        {"name": "Web Tier", "nodes": ["WebServer1", "WebServer2"]}
                    ]
                }
            },
            "microservices": {
                "input_patterns": [
                    r".*microservice.*api\s*gateway.*queue.*",
                    r".*authentication.*payment.*order.*service.*",
                    r".*api\s*gateway.*sqs.*services.*"
                ],
                "response": {
                    "nodes": [
                        {"type": "LoadBalancer", "name": "APIGateway", "properties": {}},
                        {"type": "Lambda", "name": "AuthService", "properties": {"runtime": "python3.9"}},
                        {"type": "Lambda", "name": "PaymentService", "properties": {"runtime": "python3.9"}},
                        {"type": "Lambda", "name": "OrderService", "properties": {"runtime": "python3.9"}},
                        {"type": "SQS", "name": "MessageQueue", "properties": {}},
                        {"type": "RDS", "name": "SharedDB", "properties": {}},
                        {"type": "S3", "name": "CloudWatch", "properties": {"purpose": "monitoring"}}
                    ],
                    "connections": [
                        {"from": "APIGateway", "to": "AuthService", "label": "route"},
                        {"from": "APIGateway", "to": "PaymentService", "label": "route"},
                        {"from": "APIGateway", "to": "OrderService", "label": "route"},
                        {"from": "OrderService", "to": "MessageQueue", "label": "publish"},
                        {"from": "PaymentService", "to": "MessageQueue", "label": "subscribe"},
                        {"from": "AuthService", "to": "SharedDB", "label": "query"},
                        {"from": "PaymentService", "to": "SharedDB", "label": "query"},
                        {"from": "OrderService", "to": "SharedDB", "label": "query"}
                    ],
                    "clusters": [
                        {"name": "Microservices", "nodes": ["AuthService", "PaymentService", "OrderService"]}
                    ]
                }
            },
            "simple_storage": {
                "input_patterns": [
                    r".*s3.*lambda.*",
                    r".*storage.*function.*",
                    r".*bucket.*serverless.*"
                ],
                "response": {
                    "nodes": [
                        {"type": "S3", "name": "DataBucket", "properties": {"versioning": True}},
                        {"type": "Lambda", "name": "ProcessFunction", "properties": {"runtime": "python3.9"}},
                        {"type": "SQS", "name": "EventQueue", "properties": {}}
                    ],
                    "connections": [
                        {"from": "DataBucket", "to": "EventQueue", "label": "event"},
                        {"from": "EventQueue", "to": "ProcessFunction", "label": "trigger"}
                    ],
                    "clusters": []
                }
            },
            "error_response": {
                "input_patterns": [
                    r".*test\s*error.*",
                    r".*invalid\s*json.*"
                ],
                "response": "This is not valid JSON to test error handling"
            },
            "clarification_needed": {
                "input_patterns": [
                    r".*create\s*diagram.*",
                    r".*help.*",
                    r"^diagram$"
                ],
                "response": {
                    "action": "ask_clarification",
                    "reasoning": "The request is too vague",
                    "parameters": {
                        "question": "What type of architecture would you like to create? Please provide more details about the components you need."
                    }
                }
            }
        }
        
        # Try to load from file
        if mock_data_path.exists():
            try:
                with open(mock_data_path, 'r') as f:
                    loaded_responses = json.load(f)
                    logger.info(
                        f"Loaded mock responses from {mock_data_path}",
                        feature=FeatureTag.DIAGRAM_GENERATION,
                        module=ModuleTag.LLM_CLIENT,
                        function="_load_mock_responses",
                        params={"file": str(mock_data_path)}
                    )
                    return loaded_responses
            except Exception as e:
                logger.warning(
                    f"Failed to load mock responses from file: {str(e)}",
                    feature=FeatureTag.DIAGRAM_GENERATION,
                    module=ModuleTag.LLM_CLIENT,
                    function="_load_mock_responses",
                    error=e
                )
        
        return default_responses
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate mock response based on input patterns"""
        # Simulate API delay
        await asyncio.sleep(self.response_delay)
        
        # Extract user input from prompt
        user_input = self._extract_user_input(prompt)
        
        logger.debug(
            f"Generating mock response for input",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.LLM_CLIENT,
            function="generate",
            params={
                "input_length": len(user_input),
                "temperature": temperature
            }
        )
        
        # Find matching pattern
        response_data = None
        for pattern_name, pattern_config in self.mock_responses.items():
            for pattern in pattern_config.get("input_patterns", []):
                if re.search(pattern, user_input, re.IGNORECASE):
                    response_data = pattern_config["response"]
                    logger.info(
                        f"Matched mock pattern: {pattern_name}",
                        feature=FeatureTag.DIAGRAM_GENERATION,
                        module=ModuleTag.LLM_CLIENT,
                        function="generate",
                        params={"pattern": pattern_name}
                    )
                    break
            if response_data:
                break
        
        # Default response if no pattern matches
        if response_data is None:
            logger.info(
                f"No pattern matched for input: '{user_input[:100]}...', using default response",
                feature=FeatureTag.DIAGRAM_GENERATION,
                module=ModuleTag.LLM_CLIENT,
                function="generate"
            )
            response_data = {
                "nodes": [
                    {"type": "EC2", "name": "Server1", "properties": {}},
                    {"type": "RDS", "name": "Database", "properties": {}}
                ],
                "connections": [
                    {"from": "Server1", "to": "Database", "label": "queries"}
                ],
                "clusters": []
            }
        
        # Convert response to JSON string if it's a dict
        if isinstance(response_data, dict):
            content = json.dumps(response_data, indent=2)
        else:
            content = str(response_data)
        
        # Add some variation based on temperature
        if temperature > 0.8 and random.random() < 0.1:
            # Occasionally add variation for high temperature
            if isinstance(response_data, dict) and "nodes" in response_data:
                response_data["nodes"].append({
                    "type": random.choice(["EC2", "Lambda", "S3"]),
                    "name": f"Extra{random.randint(1, 100)}",
                    "properties": {}
                })
                content = json.dumps(response_data, indent=2)
        
        # Simulate token usage
        usage = {
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(content.split()),
            "total_tokens": len(prompt.split()) + len(content.split())
        }
        
        return LLMResponse(
            content=content,
            usage=usage,
            model=self.model,
            finish_reason="stop"
        )
    
    async def generate_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        **kwargs
    ) -> LLMResponse:
        """Mock retry logic - succeeds on second attempt for error patterns"""
        # Check if this is an error test
        user_input = self._extract_user_input(prompt)
        
        if "test error" in user_input.lower() and not hasattr(self, "_retry_count"):
            self._retry_count = 1
            # First attempt fails
            raise Exception("Mock error for testing retry logic")
        
        # Reset retry count and succeed
        if hasattr(self, "_retry_count"):
            delattr(self, "_retry_count")
        
        return await self.generate(prompt, system_prompt, **kwargs)
    
    def validate_response(self, response: str) -> bool:
        """Validate if response is valid JSON"""
        if not response or not response.strip():
            return False
        
        try:
            json.loads(response)
            return True
        except json.JSONDecodeError:
            return False
    
    def _extract_user_input(self, prompt: str) -> str:
        """Extract user input from formatted prompt"""
        # Try to extract from USER REQUEST section
        match = re.search(r"USER REQUEST.*?:\s*(.+?)(?:---|JSON SPECIFICATION|$)", 
                         prompt, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Try to extract from user request
        match = re.search(r"User request:\s*(.+?)(?:What action|$)", 
                         prompt, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Return full prompt if no pattern matches
        return prompt
    
    async def close(self):
        """Cleanup resources"""
        pass
    
    def set_response_pattern(self, pattern_name: str, response: Dict[str, Any]):
        """Add or update a response pattern for testing"""
        self.mock_responses[pattern_name] = response
        logger.info(
            f"Updated mock response pattern: {pattern_name}",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.LLM_CLIENT,
            function="set_response_pattern",
            params={"pattern": pattern_name}
        )