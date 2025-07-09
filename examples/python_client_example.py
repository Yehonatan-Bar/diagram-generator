#!/usr/bin/env python3
"""
Example of using the AI Diagram Generator API from Python

This script demonstrates various ways to interact with the API:
1. Simple diagram generation
2. Using the assistant for complex architectures
3. Handling errors and retries
4. Saving generated diagrams
"""

import base64
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import httpx


class DiagramGeneratorClient:
    """Client for interacting with the AI Diagram Generator API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def check_health(self) -> bool:
        """Check if the API is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    async def generate_diagram(
        self, 
        description: str, 
        output_format: str = "base64"
    ) -> Dict[str, Any]:
        """Generate a diagram from a description"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/diagram/generate",
            json={
                "description": description,
                "output_format": output_format
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def ask_assistant(
        self, 
        message: str,
        conversation_history: Optional[list] = None
    ) -> Dict[str, Any]:
        """Interact with the assistant"""
        request_data = {"message": message}
        if conversation_history:
            request_data["conversation_history"] = conversation_history
            
        response = await self.client.post(
            f"{self.base_url}/api/v1/diagram/assistant",
            json=request_data
        )
        response.raise_for_status()
        return response.json()
    
    async def validate_specification(self, specification: str) -> Dict[str, Any]:
        """Validate a diagram specification"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/diagram/validate",
            json={"specification": specification}
        )
        response.raise_for_status()
        return response.json()
    
    def save_diagram(self, diagram_data: str, filename: str):
        """Save a base64 encoded diagram to file"""
        image_data = base64.b64decode(diagram_data)
        Path(filename).write_bytes(image_data)
        print(f"✅ Diagram saved to: {filename}")


async def example_simple_generation():
    """Example: Generate a simple diagram"""
    print("\n📊 Example 1: Simple Diagram Generation")
    print("-" * 40)
    
    async with DiagramGeneratorClient() as client:
        # Check health first
        if not await client.check_health():
            print("❌ API is not available")
            return
        
        # Generate diagram
        result = await client.generate_diagram(
            "Create a web application with a load balancer, "
            "two web servers, and a database"
        )
        
        if result["success"]:
            print(f"✅ Diagram generated successfully!")
            print(f"   Request ID: {result['request_id']}")
            print(f"   Nodes created: {result['metadata'].get('nodes_created', 'N/A')}")
            
            # Save the diagram
            client.save_diagram(result["diagram_data"], "simple_web_app.png")
        else:
            print(f"❌ Error: {result['error']}")


async def example_complex_architecture():
    """Example: Use assistant for complex architecture"""
    print("\n🤖 Example 2: Complex Architecture with Assistant")
    print("-" * 40)
    
    async with DiagramGeneratorClient() as client:
        conversation = []
        
        # Initial request
        response = await client.ask_assistant(
            "I need to design a microservices architecture for an e-commerce platform"
        )
        print(f"Assistant: {response['message']}")
        
        # Update conversation history
        conversation.append({"role": "user", "content": "I need to design a microservices architecture for an e-commerce platform"})
        conversation.append({"role": "assistant", "content": response['message']})
        
        # Provide more details
        response = await client.ask_assistant(
            "It should have services for orders, payments, inventory, and notifications. "
            "Each service should have its own database. Include a message queue for async communication.",
            conversation_history=conversation
        )
        
        print(f"\nAssistant: {response['message'][:200]}...")
        
        if response["response_type"] == "diagram" and response["diagram_data"]:
            print("\n✅ Diagram generated!")
            client.save_diagram(response["diagram_data"], "microservices_architecture.png")
        elif response["response_type"] == "clarification":
            print("\n💡 The assistant needs more information")


async def example_iterative_design():
    """Example: Iterative design process"""
    print("\n🔄 Example 3: Iterative Design Process")
    print("-" * 40)
    
    architectures = [
        {
            "name": "serverless_pipeline",
            "description": "Create a serverless data processing pipeline with S3 trigger, "
                          "Lambda function, SQS queue, and RDS database"
        },
        {
            "name": "multi_tier_app",
            "description": "Build a three-tier application with load balancer, "
                          "multiple app servers in a cluster, cache layer with Redis, "
                          "and primary-replica database setup"
        },
        {
            "name": "event_driven_system",
            "description": "Design an event-driven system with API Gateway, "
                          "multiple Lambda functions, EventBridge for routing, "
                          "DynamoDB for storage, and SNS for notifications"
        }
    ]
    
    async with DiagramGeneratorClient() as client:
        for arch in architectures:
            print(f"\n🏗️ Generating: {arch['name']}")
            
            try:
                result = await client.generate_diagram(arch["description"])
                
                if result["success"]:
                    filename = f"{arch['name']}.png"
                    client.save_diagram(result["diagram_data"], filename)
                    print(f"   ✅ Success! Saved as {filename}")
                else:
                    print(f"   ❌ Failed: {result['error']}")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
            
            # Small delay between requests
            await asyncio.sleep(1)


async def example_error_handling():
    """Example: Error handling and validation"""
    print("\n⚠️ Example 4: Error Handling and Validation")
    print("-" * 40)
    
    async with DiagramGeneratorClient() as client:
        # Try with invalid description (too short)
        try:
            result = await client.generate_diagram("web app")
        except httpx.HTTPStatusError as e:
            print(f"❌ Expected error for short description: {e.response.status_code}")
        
        # Validate a specification
        valid_spec = '''
        {
            "nodes": [
                {"type": "EC2", "name": "WebServer", "properties": {}},
                {"type": "RDS", "name": "Database", "properties": {}}
            ],
            "connections": [
                {"from": "WebServer", "to": "Database"}
            ],
            "clusters": []
        }
        '''
        
        validation_result = await client.validate_specification(valid_spec)
        print(f"\n✅ Valid specification: {validation_result['valid']}")
        
        # Try invalid specification
        invalid_spec = '''
        {
            "nodes": [{"type": "InvalidType", "name": "Server"}],
            "connections": []
        }
        '''
        
        validation_result = await client.validate_specification(invalid_spec)
        print(f"\n❌ Invalid specification: {validation_result['valid']}")
        print(f"   Error: {validation_result['error']}")
        if validation_result.get('suggestions'):
            print(f"   Suggestions: {validation_result['suggestions']}")


async def main():
    """Run all examples"""
    print("🎨 AI Diagram Generator - Python Client Examples")
    print("=" * 50)
    
    # Run examples
    await example_simple_generation()
    await example_complex_architecture()
    await example_iterative_design()
    await example_error_handling()
    
    print("\n✨ All examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())