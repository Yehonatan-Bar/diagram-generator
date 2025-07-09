#!/usr/bin/env python3
"""
Example script to test the diagram generation API
"""
import base64
import asyncio
from pathlib import Path
import httpx


async def test_health_check():
    """Test the health check endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        print(f"Health check: {response.json()}")
        return response.status_code == 200


async def test_diagram_generation():
    """Test diagram generation endpoint"""
    async with httpx.AsyncClient() as client:
        request_data = {
            "description": "Create a simple web application with a load balancer, two EC2 instances, and an RDS database",
            "output_format": "base64"
        }
        
        response = await client.post(
            "http://localhost:8000/api/v1/diagram/generate",
            json=request_data
        )
        
        result = response.json()
        print(f"Generation response: Success={result.get('success')}")
        
        if result.get('success') and result.get('diagram_data'):
            # Save the generated diagram
            image_data = base64.b64decode(result['diagram_data'])
            output_path = Path("generated_diagram.png")
            output_path.write_bytes(image_data)
            print(f"Diagram saved to: {output_path}")
        else:
            print(f"Error: {result.get('error')}")
        
        return response.status_code == 200


async def test_assistant():
    """Test assistant conversation endpoint"""
    async with httpx.AsyncClient() as client:
        request_data = {
            "message": "I want to create a serverless application"
        }
        
        response = await client.post(
            "http://localhost:8000/api/v1/diagram/assistant",
            json=request_data
        )
        
        result = response.json()
        print(f"Assistant response: Type={result.get('response_type')}, Message={result.get('message')}")
        
        return response.status_code == 200


async def main():
    """Run all tests"""
    print("Testing Diagram Generation API...\n")
    
    # Test health check
    print("1. Testing health check...")
    health_ok = await test_health_check()
    print(f"   Result: {'✓' if health_ok else '✗'}\n")
    
    # Test diagram generation
    print("2. Testing diagram generation...")
    gen_ok = await test_diagram_generation()
    print(f"   Result: {'✓' if gen_ok else '✗'}\n")
    
    # Test assistant
    print("3. Testing assistant...")
    assist_ok = await test_assistant()
    print(f"   Result: {'✓' if assist_ok else '✗'}\n")
    
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())