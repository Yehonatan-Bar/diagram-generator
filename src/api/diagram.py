"""
Diagram generation API endpoints
"""
import base64
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from ..core.logging import logger, FeatureTag, ModuleTag
from ..llm.client import get_llm_client
from ..llm.prompt_manager import PromptManager
from ..agents.diagram_agent import DiagramAgent
from ..agents.assistant_agent import AssistantAgent, ConversationTurn
from ..tools.validator import SpecificationValidator

from .models import (
    DiagramGenerationRequest,
    DiagramGenerationResponse,
    AssistantRequest,
    AssistantResponse,
    ValidationRequest,
    ValidationResponse
)

router = APIRouter(prefix="/diagram", tags=["diagram"])

# Global instances (could be dependency injected in production)
_prompt_manager: Optional[PromptManager] = None
_diagram_agent: Optional[DiagramAgent] = None
_assistant_agent: Optional[AssistantAgent] = None


def get_agents():
    """
    Initialize and cache agent instances
    """
    global _prompt_manager, _diagram_agent, _assistant_agent
    
    if not _prompt_manager:
        _prompt_manager = PromptManager()
        llm_client = get_llm_client()
        _diagram_agent = DiagramAgent(llm_client, _prompt_manager)
        _assistant_agent = AssistantAgent(llm_client, _prompt_manager, _diagram_agent)
        
        logger.info(
            "Initialized agent instances",
            feature=FeatureTag.API,
            module=ModuleTag.API,
            function="get_agents"
        )
    
    return _prompt_manager, _diagram_agent, _assistant_agent


@router.post("/generate", response_model=DiagramGenerationResponse)
async def generate_diagram(
    request: DiagramGenerationRequest,
    req: Request
) -> DiagramGenerationResponse:
    """
    Generate a cloud architecture diagram from natural language description
    
    Args:
        request: Diagram generation request with description
        req: FastAPI request object
        
    Returns:
        DiagramGenerationResponse with base64 encoded image or error
    """
    request_id = req.state.request_id
    
    logger.info(
        f"Generating diagram for description",
        feature=FeatureTag.DIAGRAM_GENERATION,
        module=ModuleTag.API,
        function="generate_diagram",
        params={
            "description_length": len(request.description),
            "output_format": request.output_format,
            "request_id": request_id
        }
    )
    
    try:
        # Get agents
        _, diagram_agent, _ = get_agents()
        
        # Generate diagram
        image_data = await diagram_agent.generate_diagram(request.description)
        
        # Convert to base64 if requested
        if request.output_format == "base64":
            diagram_data = base64.b64encode(image_data).decode('utf-8')
        else:
            diagram_data = image_data.hex()  # Fallback hex encoding
        
        logger.info(
            "Successfully generated diagram",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.API,
            function="generate_diagram",
            params={
                "image_size": len(image_data),
                "encoded_size": len(diagram_data),
                "request_id": request_id
            }
        )
        
        return DiagramGenerationResponse(
            success=True,
            diagram_data=diagram_data,
            metadata={
                "description": request.description,
                "image_size_bytes": len(image_data),
                "format": request.output_format
            },
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(
            f"Failed to generate diagram",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.API,
            function="generate_diagram",
            params={"request_id": request_id},
            error=e
        )
        
        return DiagramGenerationResponse(
            success=False,
            error=str(e),
            request_id=request_id
        )


@router.get("/generate/{diagram_id}")
async def get_diagram_image(diagram_id: str):
    """
    Get a previously generated diagram by ID (placeholder for future implementation)
    """
    raise HTTPException(
        status_code=501,
        detail="Diagram retrieval not yet implemented"
    )


@router.post("/assistant", response_model=AssistantResponse)
async def assistant_conversation(
    request: AssistantRequest,
    req: Request
) -> AssistantResponse:
    """
    Process a conversational request with the assistant
    
    Args:
        request: Assistant request with message and optional history
        req: FastAPI request object
        
    Returns:
        AssistantResponse with action taken and optional diagram
    """
    request_id = req.state.request_id
    
    logger.info(
        "Processing assistant request",
        feature=FeatureTag.ASSISTANT,
        module=ModuleTag.API,
        function="assistant_conversation",
        params={
            "message_length": len(request.message),
            "has_history": request.conversation_history is not None,
            "request_id": request_id
        }
    )
    
    try:
        # Get agents
        _, _, assistant_agent = get_agents()
        
        # Convert history to ConversationTurn objects
        history = None
        if request.conversation_history:
            history = [
                ConversationTurn(
                    role=turn["role"],
                    content=turn["content"]
                )
                for turn in request.conversation_history
            ]
        
        # Process conversation
        result = await assistant_agent.process_conversation(
            current_input=request.message,
            history=history
        )
        
        # Build response based on result type
        response_type = result["type"]
        message = result.get("message", "")
        diagram_data = None
        
        if response_type == "diagram":
            # Convert image bytes to base64
            image_bytes = result.get("content")
            if image_bytes:
                diagram_data = base64.b64encode(image_bytes).decode('utf-8')
        
        logger.info(
            f"Assistant completed action: {response_type}",
            feature=FeatureTag.ASSISTANT,
            module=ModuleTag.API,
            function="assistant_conversation",
            params={
                "response_type": response_type,
                "has_diagram": diagram_data is not None,
                "request_id": request_id
            }
        )
        
        return AssistantResponse(
            success=True,
            response_type=response_type,
            message=message,
            diagram_data=diagram_data,
            metadata=result.get("metadata", {}),
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(
            "Failed to process assistant request",
            feature=FeatureTag.ASSISTANT,
            module=ModuleTag.API,
            function="assistant_conversation",
            params={"request_id": request_id},
            error=e
        )
        
        return AssistantResponse(
            success=False,
            response_type="error",
            message=f"An error occurred: {str(e)}",
            request_id=request_id
        )


@router.post("/validate", response_model=ValidationResponse)
async def validate_specification(
    request: ValidationRequest,
    req: Request
) -> ValidationResponse:
    """
    Validate a diagram specification JSON
    
    Args:
        request: Validation request with specification
        req: FastAPI request object
        
    Returns:
        ValidationResponse with validation result
    """
    request_id = req.state.request_id
    
    logger.info(
        "Validating specification",
        feature=FeatureTag.VALIDATION,
        module=ModuleTag.API,
        function="validate_specification",
        params={
            "spec_length": len(request.specification),
            "request_id": request_id
        }
    )
    
    try:
        validator = SpecificationValidator()
        is_valid, parsed_spec, error_msg = validator.validate(request.specification)
        
        suggestions = None
        if not is_valid and error_msg:
            suggestions = validator.suggest_fix(error_msg, request.specification)
        
        return ValidationResponse(
            valid=is_valid,
            error=error_msg,
            suggestions=suggestions,
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(
            "Failed to validate specification",
            feature=FeatureTag.VALIDATION,
            module=ModuleTag.API,
            function="validate_specification",
            params={"request_id": request_id},
            error=e
        )
        
        return ValidationResponse(
            valid=False,
            error=f"Validation error: {str(e)}",
            request_id=request_id
        )