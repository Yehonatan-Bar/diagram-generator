"""
Integration tests for API endpoints.
"""
import pytest
import json
from httpx import AsyncClient
from fastapi import status

from src.api.main import app


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_basic_health_check(self, async_client: AsyncClient):
        """Test basic health endpoint."""
        response = await async_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_readiness_check(self, async_client: AsyncClient):
        """Test readiness endpoint."""
        response = await async_client.get("/health/ready")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data
        assert data["checks"]["llm_client"]["status"] == "healthy"
        assert data["checks"]["diagram_builder"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_liveness_check(self, async_client: AsyncClient):
        """Test liveness endpoint."""
        response = await async_client.get("/health/live")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "alive"
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0


class TestDiagramEndpoints:
    """Test diagram generation endpoints."""
    
    @pytest.mark.asyncio
    async def test_generate_diagram_simple(self, async_client: AsyncClient):
        """Test simple diagram generation."""
        response = await async_client.post(
            "/api/v1/diagram/generate",
            json={
                "description": "Create a simple web application with a database"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "diagram_data" in data
        assert data["diagram_data"] is not None
        assert "metadata" in data
        assert "request_id" in data
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_generate_diagram_with_format(self, async_client: AsyncClient):
        """Test diagram generation with output format."""
        response = await async_client.post(
            "/api/v1/diagram/generate",
            json={
                "description": "Create a serverless architecture with Lambda and S3",
                "output_format": "base64"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["diagram_data"] is not None
        # In mock mode, should return mock base64 data
        assert isinstance(data["diagram_data"], str)
    
    @pytest.mark.asyncio
    async def test_generate_diagram_invalid_request(self, async_client: AsyncClient):
        """Test diagram generation with invalid request."""
        response = await async_client.post(
            "/api/v1/diagram/generate",
            json={
                # Missing required 'description' field
                "output_format": "base64"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_generate_diagram_empty_description(self, async_client: AsyncClient):
        """Test diagram generation with empty description."""
        response = await async_client.post(
            "/api/v1/diagram/generate",
            json={
                "description": ""
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_assistant_endpoint(self, async_client: AsyncClient):
        """Test assistant conversation endpoint."""
        response = await async_client.post(
            "/api/v1/diagram/assistant",
            json={
                "message": "I need help creating a microservices architecture"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "message" in data
        assert "response_type" in data
        assert data["response_type"] in ["clarification", "diagram", "explanation"]
        assert "request_id" in data
    
    @pytest.mark.asyncio
    async def test_assistant_with_history(self, async_client: AsyncClient):
        """Test assistant with conversation history."""
        response = await async_client.post(
            "/api/v1/diagram/assistant",
            json={
                "message": "Add a load balancer to it",
                "conversation_history": [
                    {"role": "user", "content": "Create a web app"},
                    {"role": "assistant", "content": "I'll help you create a web application. What components do you need?"}
                ]
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "message" in data
        # Should understand context from history
    
    @pytest.mark.asyncio
    async def test_validate_specification_valid(self, async_client: AsyncClient):
        """Test specification validation with valid spec."""
        valid_spec = {
            "nodes": [
                {"type": "EC2", "name": "WebServer"},
                {"type": "RDS", "name": "Database"}
            ],
            "connections": [
                {"from": "WebServer", "to": "Database"}
            ],
            "clusters": []
        }
        
        response = await async_client.post(
            "/api/v1/diagram/validate",
            json={
                "specification": json.dumps(valid_spec)
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["valid"] is True
        assert data["error"] is None
        assert data["suggestions"] is None
    
    @pytest.mark.asyncio
    async def test_validate_specification_invalid(self, async_client: AsyncClient):
        """Test specification validation with invalid spec."""
        invalid_spec = {
            "nodes": [
                {"type": "InvalidType", "name": "Server"}
            ],
            "connections": []
        }
        
        response = await async_client.post(
            "/api/v1/diagram/validate",
            json={
                "specification": json.dumps(invalid_spec)
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["valid"] is False
        assert data["error"] is not None
        assert data["suggestions"] is not None
        assert "Invalid node type" in data["error"]


class TestAPIFeatures:
    """Test API features like CORS, request IDs, etc."""
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client: AsyncClient):
        """Test CORS headers are present."""
        response = await async_client.options(
            "/api/v1/diagram/generate",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert "access-control-allow-origin" in response.headers
    
    @pytest.mark.asyncio
    async def test_request_id_generation(self, async_client: AsyncClient):
        """Test that request IDs are generated."""
        response = await async_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        assert "x-request-id" in response.headers
        
        # Request ID should be a valid UUID format
        request_id = response.headers["x-request-id"]
        assert len(request_id) == 36  # Standard UUID length
        assert request_id.count("-") == 4  # UUID has 4 hyphens
    
    @pytest.mark.asyncio
    async def test_api_documentation(self, async_client: AsyncClient):
        """Test that API documentation is accessible."""
        response = await async_client.get("/docs")
        
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_openapi_schema(self, async_client: AsyncClient):
        """Test that OpenAPI schema is accessible."""
        response = await async_client.get("/openapi.json")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Diagram Generator API"
        assert "paths" in data
        assert "/api/v1/diagram/generate" in data["paths"]