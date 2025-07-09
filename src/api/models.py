"""
Pydantic models for API requests and responses
"""
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class DiagramGenerationRequest(BaseModel):
    """Request model for diagram generation"""
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Natural language description of the architecture to generate"
    )
    output_format: Literal["png", "base64"] = Field(
        default="base64",
        description="Output format for the diagram"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "description": "Create a web application with a load balancer, two EC2 instances, and an RDS database",
                "output_format": "base64"
            }
        }


class DiagramGenerationResponse(BaseModel):
    """Response model for diagram generation"""
    success: bool
    diagram_data: Optional[str] = Field(
        None,
        description="Base64 encoded PNG image or null if error"
    )
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AssistantRequest(BaseModel):
    """Request model for assistant conversation"""
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User message to the assistant"
    )
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Previous conversation turns"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "I want to create a serverless application",
                "conversation_history": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi! How can I help you create a diagram today?"}
                ]
            }
        }


class AssistantResponse(BaseModel):
    """Response model for assistant conversation"""
    success: bool
    response_type: Literal["diagram", "clarification", "explanation", "error"]
    message: str
    diagram_data: Optional[str] = Field(
        None,
        description="Base64 encoded PNG image if response_type is 'diagram'"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationRequest(BaseModel):
    """Request model for specification validation"""
    specification: str = Field(
        ...,
        description="JSON specification to validate"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "specification": '''{"nodes": [{"type": "EC2", "name": "WebServer", "properties": {}}], "connections": [], "clusters": []}'''
            }
        }


class ValidationResponse(BaseModel):
    """Response model for specification validation"""
    valid: bool
    error: Optional[str] = None
    suggestions: Optional[str] = None
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)