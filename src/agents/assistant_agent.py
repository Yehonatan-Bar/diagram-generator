"""
Assistant agent for conversational interface
Handles user intent, provides clarifications, and coordinates diagram generation
"""
import json
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel

from ..llm.base import BaseLLMClient
from ..llm.prompt_manager import PromptManager
from ..core.logging import logger, FeatureTag, ModuleTag
from ..utils.decorators import log_execution_time
from .diagram_agent import DiagramAgent


class ToolAction(Enum):
    """Available actions for the assistant"""
    GENERATE_DIAGRAM = "generate_diagram"
    ASK_CLARIFICATION = "ask_clarification"
    EXPLAIN_CONCEPT = "explain_concept"


class AgentAction(BaseModel):
    """Action decision from the assistant"""
    action: ToolAction
    reasoning: str
    parameters: Dict[str, Any]


class ConversationTurn(BaseModel):
    """Single turn in a conversation"""
    role: str  # "user" or "assistant"
    content: str
    metadata: Optional[Dict[str, Any]] = None


class AssistantAgent:
    """Conversational assistant that can reason about actions"""
    
    def __init__(
        self,
        llm_client: BaseLLMClient,
        prompt_manager: PromptManager,
        diagram_agent: Optional[DiagramAgent] = None
    ):
        """
        Initialize the assistant agent
        
        Args:
            llm_client: LLM client for reasoning
            prompt_manager: Manager for prompt templates
            diagram_agent: Diagram generation agent (optional)
        """
        self.llm = llm_client
        self.prompts = prompt_manager
        self.diagram_agent = diagram_agent
        
        logger.info(
            "Initialized AssistantAgent",
            feature=FeatureTag.ASSISTANT,
            module=ModuleTag.AGENT_FRAMEWORK,
            function="__init__",
            params={"has_diagram_agent": diagram_agent is not None}
        )
    
    @log_execution_time(FeatureTag.ASSISTANT, ModuleTag.AGENT_FRAMEWORK)
    async def process_conversation(
        self,
        current_input: str,
        history: Optional[List[ConversationTurn]] = None
    ) -> Dict[str, Any]:
        """
        Process user input with conversation history
        
        Args:
            current_input: Current user message
            history: Previous conversation turns
            
        Returns:
            Response dictionary with type, content, and optional metadata
        """
        logger.info(
            "Assistant processing request",
            feature=FeatureTag.ASSISTANT,
            module=ModuleTag.AGENT_FRAMEWORK,
            function="process_conversation",
            params={
                "input_length": len(current_input),
                "history_length": len(history or [])
            }
        )
        
        # Build context from history
        context = self._build_context(history) if history else ""
        
        # Get reasoning prompt
        prompt = self.prompts.get_prompt(
            "assistant_reasoning",
            context=context,
            user_input=current_input,
            available_tools=self._get_tool_descriptions()
        )
        
        # Get LLM reasoning
        reasoning_response = await self.llm.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=1024
        )
        
        # Parse action from reasoning
        action = self._parse_action(reasoning_response.content)
        
        # Execute action
        result = await self._execute_action(action, current_input)
        
        logger.info(
            f"Assistant completed action: {action.action.value}",
            feature=FeatureTag.ASSISTANT,
            module=ModuleTag.AGENT_FRAMEWORK,
            function="process_conversation",
            params={"action": action.action.value, "result_type": result.get("type")}
        )
        
        return result
    
    def _build_context(self, history: List[ConversationTurn]) -> str:
        """Build context string from conversation history"""
        if not history:
            return ""
        
        # Take last 5 turns to avoid context overflow
        recent_history = history[-5:]
        
        context_parts = []
        for turn in recent_history:
            context_parts.append(f"{turn.role.upper()}: {turn.content}")
        
        return "\n".join(context_parts)
    
    def _get_tool_descriptions(self) -> str:
        """Get descriptions of available tools"""
        descriptions = [
            "1. generate_diagram - Generate a cloud architecture diagram from a description",
            "2. ask_clarification - Ask the user for more specific information",
            "3. explain_concept - Explain how to use the diagram generation system"
        ]
        return "\n".join(descriptions)
    
    def _parse_action(self, reasoning_response: str) -> AgentAction:
        """Parse action from LLM reasoning response"""
        try:
            # Try to parse as JSON
            data = json.loads(reasoning_response)
            
            # Map string action to enum
            action_str = data.get("action", "ask_clarification")
            action_map = {
                "generate_diagram": ToolAction.GENERATE_DIAGRAM,
                "ask_clarification": ToolAction.ASK_CLARIFICATION,
                "explain_concept": ToolAction.EXPLAIN_CONCEPT
            }
            
            action = action_map.get(action_str, ToolAction.ASK_CLARIFICATION)
            
            return AgentAction(
                action=action,
                reasoning=data.get("reasoning", ""),
                parameters=data.get("parameters", {})
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(
                f"Failed to parse action from response, defaulting to clarification",
                feature=FeatureTag.ASSISTANT,
                module=ModuleTag.AGENT_FRAMEWORK,
                function="_parse_action",
                error=e
            )
            
            # Default to asking for clarification
            return AgentAction(
                action=ToolAction.ASK_CLARIFICATION,
                reasoning="Could not understand the request",
                parameters={
                    "question": "I'm not sure I understood your request. Could you please provide more details about what kind of diagram you'd like to create?"
                }
            )
    
    async def _execute_action(
        self,
        action: AgentAction,
        original_input: str
    ) -> Dict[str, Any]:
        """Execute the chosen action"""
        if action.action == ToolAction.GENERATE_DIAGRAM:
            if not self.diagram_agent:
                return {
                    "type": "error",
                    "message": "Diagram generation is not available in this configuration"
                }
            
            try:
                # Use provided description or original input
                description = action.parameters.get("description", original_input)
                
                logger.debug(
                    "Generating diagram from assistant",
                    feature=FeatureTag.ASSISTANT,
                    module=ModuleTag.AGENT_FRAMEWORK,
                    function="_execute_action",
                    params={"description_length": len(description)}
                )
                
                image_data = await self.diagram_agent.generate_diagram(description)
                
                return {
                    "type": "diagram",
                    "content": image_data,
                    "message": "Here's your cloud architecture diagram!",
                    "metadata": {
                        "description": description,
                        "image_size": len(image_data)
                    }
                }
                
            except Exception as e:
                logger.error(
                    "Error generating diagram",
                    feature=FeatureTag.ASSISTANT,
                    module=ModuleTag.AGENT_FRAMEWORK,
                    function="_execute_action",
                    error=e
                )
                
                return {
                    "type": "error",
                    "message": f"I encountered an error creating the diagram: {str(e)}",
                    "metadata": {"error_type": type(e).__name__}
                }
        
        elif action.action == ToolAction.ASK_CLARIFICATION:
            question = action.parameters.get(
                "question",
                "Could you provide more details about the architecture you want to create?"
            )
            
            return {
                "type": "clarification",
                "message": question,
                "metadata": {"reasoning": action.reasoning}
            }
        
        elif action.action == ToolAction.EXPLAIN_CONCEPT:
            concept = action.parameters.get("concept", "diagram creation")
            explanation = await self._generate_explanation(concept)
            
            return {
                "type": "explanation",
                "message": explanation,
                "metadata": {"concept": concept}
            }
        
        else:
            return {
                "type": "error",
                "message": f"Unknown action: {action.action}"
            }
    
    async def _generate_explanation(self, concept: str) -> str:
        """Generate an explanation for a concept"""
        prompt = self.prompts.get_prompt(
            "explanation_template",
            user_input=concept,
            node_types="EC2, RDS, LoadBalancer, SQS, Lambda, S3"
        )
        
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=1024
        )
        
        return response.content