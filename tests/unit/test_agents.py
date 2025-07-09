"""
Unit tests for agent implementations.
"""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from src.agents.diagram_agent import DiagramAgent, DiagramGenerationResult
from src.agents.assistant_agent import (
    AssistantAgent, ToolAction, AgentAction, ConversationTurn,
    AssistantResult
)
from src.llm.base import LLMResponse


class TestDiagramAgent:
    """Test DiagramAgent functionality."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test DiagramAgent initialization."""
        agent = DiagramAgent()
        assert agent is not None
        assert hasattr(agent, 'generate_diagram')
        assert hasattr(agent, 'validate_specification')
    
    @pytest.mark.asyncio
    async def test_generate_diagram_success(self):
        """Test successful diagram generation."""
        agent = DiagramAgent()
        
        # Mock dependencies
        mock_llm_response = LLMResponse(
            content=json.dumps({
                "nodes": [
                    {"type": "EC2", "name": "WebServer"},
                    {"type": "RDS", "name": "Database"}
                ],
                "connections": [
                    {"from": "WebServer", "to": "Database"}
                ]
            }),
            success=True
        )
        
        with patch.object(agent._llm_client, 'generate', return_value=mock_llm_response):
            with patch.object(agent._diagram_builder, 'build_diagram', return_value=True):
                with patch.object(agent._diagram_builder, 'get_last_image_data', return_value="base64data"):
                    
                    result = await agent.generate_diagram("Create a simple web app")
                    
                    assert result.success is True
                    assert result.diagram_data == "base64data"
                    assert result.error is None
    
    @pytest.mark.asyncio
    async def test_generate_diagram_with_retry(self):
        """Test diagram generation with retry on validation failure."""
        agent = DiagramAgent()
        
        # First response - invalid
        invalid_response = LLMResponse(
            content=json.dumps({
                "nodes": [{"type": "InvalidType", "name": "Server"}],
                "connections": []
            }),
            success=True
        )
        
        # Second response - valid
        valid_response = LLMResponse(
            content=json.dumps({
                "nodes": [{"type": "EC2", "name": "Server"}],
                "connections": []
            }),
            success=True
        )
        
        # Mock the generate method to return invalid then valid
        mock_generate = AsyncMock(side_effect=[invalid_response, valid_response])
        
        with patch.object(agent._llm_client, 'generate', mock_generate):
            with patch.object(agent._diagram_builder, 'build_diagram', return_value=True):
                with patch.object(agent._diagram_builder, 'get_last_image_data', return_value="base64data"):
                    
                    result = await agent.generate_diagram("Create a server")
                    
                    assert result.success is True
                    assert mock_generate.call_count == 2  # Should retry once
    
    @pytest.mark.asyncio
    async def test_generate_diagram_llm_failure(self):
        """Test diagram generation with LLM failure."""
        agent = DiagramAgent()
        
        # Mock LLM failure
        failed_response = LLMResponse(
            content="",
            success=False,
            error="LLM API error"
        )
        
        with patch.object(agent._llm_client, 'generate', return_value=failed_response):
            result = await agent.generate_diagram("Create something")
            
            assert result.success is False
            assert result.error == "Failed to generate specification: LLM API error"
            assert result.diagram_data is None
    
    @pytest.mark.asyncio
    async def test_validate_specification(self):
        """Test specification validation."""
        agent = DiagramAgent()
        
        valid_spec = json.dumps({
            "nodes": [{"type": "EC2", "name": "Server"}],
            "connections": []
        })
        
        result = await agent.validate_specification(valid_spec)
        
        assert result["valid"] is True
        assert result["error"] is None
        assert result["suggestions"] is None
    
    @pytest.mark.asyncio
    async def test_validate_invalid_specification(self):
        """Test invalid specification validation."""
        agent = DiagramAgent()
        
        invalid_spec = json.dumps({
            "nodes": [{"type": "InvalidType", "name": "Server"}],
            "connections": []
        })
        
        result = await agent.validate_specification(invalid_spec)
        
        assert result["valid"] is False
        assert result["error"] is not None
        assert result["suggestions"] is not None


class TestAssistantAgent:
    """Test AssistantAgent functionality."""
    
    @pytest.mark.asyncio
    async def test_assistant_initialization(self):
        """Test AssistantAgent initialization."""
        agent = AssistantAgent()
        assert agent is not None
        assert hasattr(agent, 'process_conversation')
    
    @pytest.mark.asyncio
    async def test_process_conversation_generate_intent(self):
        """Test processing conversation with generate intent."""
        agent = AssistantAgent()
        
        # Mock LLM response for intent detection
        intent_response = LLMResponse(
            content=json.dumps({
                "intent": "generate",
                "parameters": {
                    "description": "Create a web app with database"
                }
            }),
            success=True
        )
        
        # Mock diagram generation
        mock_diagram_result = DiagramGenerationResult(
            success=True,
            diagram_data="base64data",
            specification={"nodes": []},
            metadata={"nodes_created": 2}
        )
        
        with patch.object(agent._llm_client, 'generate', return_value=intent_response):
            with patch.object(agent._diagram_agent, 'generate_diagram', return_value=mock_diagram_result):
                
                result = await agent.process_conversation(
                    "I want to create a web app with a database",
                    []
                )
                
                assert result.success is True
                assert result.response_type == "diagram"
                assert result.diagram_data == "base64data"
    
    @pytest.mark.asyncio
    async def test_process_conversation_clarify_intent(self):
        """Test processing conversation with clarify intent."""
        agent = AssistantAgent()
        
        # Mock LLM response for clarification
        intent_response = LLMResponse(
            content=json.dumps({
                "intent": "clarify",
                "parameters": {
                    "question": "What type of database do you need?"
                }
            }),
            success=True
        )
        
        clarify_response = LLMResponse(
            content="I see you want to build an application. Could you provide more details about the database requirements?",
            success=True
        )
        
        mock_generate = AsyncMock(side_effect=[intent_response, clarify_response])
        
        with patch.object(agent._llm_client, 'generate', mock_generate):
            result = await agent.process_conversation(
                "I need a system",
                []
            )
            
            assert result.success is True
            assert result.response_type == "clarification"
            assert result.message is not None
            assert result.diagram_data is None
    
    @pytest.mark.asyncio
    async def test_process_conversation_with_history(self):
        """Test processing conversation with history."""
        agent = AssistantAgent()
        
        history = [
            {"role": "user", "content": "I need a web app"},
            {"role": "assistant", "content": "What kind of web app?"}
        ]
        
        intent_response = LLMResponse(
            content=json.dumps({
                "intent": "generate",
                "parameters": {
                    "description": "E-commerce web app with database"
                }
            }),
            success=True
        )
        
        mock_diagram_result = DiagramGenerationResult(
            success=True,
            diagram_data="base64data",
            specification={},
            metadata={}
        )
        
        with patch.object(agent._llm_client, 'generate', return_value=intent_response):
            with patch.object(agent._diagram_agent, 'generate_diagram', return_value=mock_diagram_result):
                
                result = await agent.process_conversation(
                    "An e-commerce platform",
                    history
                )
                
                assert result.success is True
                # Should have context from history
    
    @pytest.mark.asyncio
    async def test_process_conversation_error_handling(self):
        """Test error handling in conversation processing."""
        agent = AssistantAgent()
        
        # Mock LLM failure
        failed_response = LLMResponse(
            content="",
            success=False,
            error="LLM API error"
        )
        
        with patch.object(agent._llm_client, 'generate', return_value=failed_response):
            result = await agent.process_conversation("Create something", [])
            
            assert result.success is False
            assert result.error is not None
            assert "understand your request" in result.message


class TestAgentModels:
    """Test agent-related Pydantic models."""
    
    def test_tool_action_enum(self):
        """Test ToolAction enumeration."""
        assert ToolAction.GENERATE_DIAGRAM == "generate_diagram"
        assert ToolAction.VALIDATE_SPEC == "validate_specification"
        assert ToolAction.SUGGEST_FIX == "suggest_fix"
        assert ToolAction.CLARIFY == "clarify_requirements"
    
    def test_agent_action_model(self):
        """Test AgentAction model."""
        action = AgentAction(
            tool=ToolAction.GENERATE_DIAGRAM,
            parameters={"description": "web app"}
        )
        
        assert action.tool == ToolAction.GENERATE_DIAGRAM
        assert action.parameters["description"] == "web app"
    
    def test_conversation_turn_model(self):
        """Test ConversationTurn model."""
        turn = ConversationTurn(
            role="user",
            content="Create a diagram",
            timestamp="2025-01-08T12:00:00Z"
        )
        
        assert turn.role == "user"
        assert turn.content == "Create a diagram"
        assert turn.timestamp == "2025-01-08T12:00:00Z"
    
    def test_assistant_result_model(self):
        """Test AssistantResult model."""
        result = AssistantResult(
            success=True,
            message="Diagram created",
            response_type="diagram",
            diagram_data="base64data",
            action_taken=AgentAction(
                tool=ToolAction.GENERATE_DIAGRAM,
                parameters={}
            )
        )
        
        assert result.success is True
        assert result.response_type == "diagram"
        assert result.diagram_data == "base64data"
        assert result.action_taken.tool == ToolAction.GENERATE_DIAGRAM