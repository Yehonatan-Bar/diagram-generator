"""
Diagram generation agent with retry logic and repair capabilities
"""
import json
from typing import Optional, Dict, Any, Tuple

from ..llm.base import BaseLLMClient
from ..llm.prompt_manager import PromptManager
from ..tools.diagram_builder import DiagramBuilder
from ..tools.validator import SpecificationValidator, DiagramSpecification
from ..core.logging import logger, FeatureTag, ModuleTag
from ..core.config import settings
from ..utils.decorators import log_execution_time


class DiagramAgent:
    """Agent that orchestrates diagram generation from natural language"""
    
    def __init__(
        self,
        llm_client: BaseLLMClient,
        prompt_manager: PromptManager,
        validator: Optional[SpecificationValidator] = None,
        diagram_builder: Optional[DiagramBuilder] = None,
        max_retries: Optional[int] = None
    ):
        """
        Initialize the diagram agent
        
        Args:
            llm_client: LLM client for generating specifications
            prompt_manager: Manager for prompt templates
            validator: Specification validator (defaults to new instance)
            diagram_builder: Diagram builder (defaults to new instance)
            max_retries: Maximum retry attempts (defaults to config value)
        """
        self.llm = llm_client
        self.prompts = prompt_manager
        self.validator = validator or SpecificationValidator()
        self.builder = diagram_builder or DiagramBuilder()
        self.max_retries = max_retries or settings.max_retry_attempts
        
        logger.info(
            "Initialized DiagramAgent",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.AGENT_FRAMEWORK,
            function="__init__",
            params={
                "llm_provider": llm_client.__class__.__name__,
                "max_retries": self.max_retries
            }
        )
    
    @log_execution_time(FeatureTag.DIAGRAM_GENERATION, ModuleTag.AGENT_FRAMEWORK)
    async def generate_diagram(self, user_description: str) -> bytes:
        """
        Generate diagram from natural language description
        
        Args:
            user_description: Natural language description of the diagram
            
        Returns:
            PNG image data as bytes
            
        Raises:
            ValueError: If unable to generate valid specification after retries
            Exception: For other errors during generation
        """
        logger.info(
            f"Starting diagram generation",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.AGENT_FRAMEWORK,
            function="generate_diagram",
            params={"description_length": len(user_description)}
        )
        
        # Step 1: Generate initial specification
        prompt = self.prompts.get_prompt(
            "diagram_generation",
            {
                "user_input": user_description,
                "node_types": ", ".join(self.builder.get_supported_node_types())
            }
        )
        
        spec_json = None
        valid_spec = None
        
        # Retry loop with validation
        for attempt in range(self.max_retries):
            try:
                # Call LLM
                logger.debug(
                    f"Calling LLM for specification generation (attempt {attempt + 1})",
                    feature=FeatureTag.DIAGRAM_GENERATION,
                    module=ModuleTag.AGENT_FRAMEWORK,
                    function="generate_diagram",
                    params={"attempt": attempt + 1}
                )
                
                response = await self.llm.generate(
                    prompt=prompt,
                    system_prompt=None,  # System prompt is included in the template
                    temperature=0.3,     # Lower temperature for more consistent JSON
                    max_tokens=4096
                )
                
                spec_json = response.content
                
                logger.debug(
                    f"LLM response received (attempt {attempt + 1})",
                    feature=FeatureTag.DIAGRAM_GENERATION,
                    module=ModuleTag.LLM_CLIENT,
                    function="generate_diagram",
                    params={
                        "attempt": attempt + 1,
                        "response_length": len(spec_json),
                        "usage": response.usage
                    }
                )
                
                # Validate response
                is_valid, parsed_spec, error_msg = self.validator.validate(spec_json)
                
                if is_valid:
                    valid_spec = parsed_spec
                    logger.info(
                        f"Valid specification generated on attempt {attempt + 1}",
                        feature=FeatureTag.DIAGRAM_GENERATION,
                        module=ModuleTag.VALIDATION,
                        function="generate_diagram",
                        params={
                            "attempt": attempt + 1,
                            "node_count": len(parsed_spec.nodes),
                            "connection_count": len(parsed_spec.connections)
                        }
                    )
                    break
                else:
                    # Prepare repair prompt
                    logger.warning(
                        f"Validation failed: {error_msg}",
                        feature=FeatureTag.DIAGRAM_GENERATION,
                        module=ModuleTag.VALIDATION,
                        function="generate_diagram",
                        params={"error": error_msg, "attempt": attempt + 1}
                    )
                    
                    if attempt < self.max_retries - 1:
                        # Get fix suggestions
                        suggestions = self.validator.suggest_fix(error_msg, spec_json)
                        
                        # Create repair prompt
                        prompt = self.prompts.get_prompt(
                            "repair_specification",
                            {
                                "original_response": spec_json,
                                "error_message": error_msg,
                                "suggestions": suggestions,
                                "node_types": ", ".join(self.builder.get_supported_node_types())
                            }
                        )
            
            except Exception as e:
                logger.error(
                    f"Error during diagram generation",
                    feature=FeatureTag.DIAGRAM_GENERATION,
                    module=ModuleTag.AGENT_FRAMEWORK,
                    function="generate_diagram",
                    params={"attempt": attempt + 1},
                    error=e
                )
                if attempt == self.max_retries - 1:
                    raise
        
        if not valid_spec:
            raise ValueError(
                f"Failed to generate valid specification after {self.max_retries} attempts. "
                f"Last error: {error_msg}"
            )
        
        # Step 2: Build diagram
        return await self._build_diagram_from_spec(valid_spec, user_description)
    
    async def _build_diagram_from_spec(
        self, 
        spec: DiagramSpecification, 
        original_description: str
    ) -> bytes:
        """
        Convert specification to actual diagram
        
        Args:
            spec: Validated diagram specification
            original_description: Original user description (for title)
            
        Returns:
            PNG image data as bytes
        """
        logger.debug(
            "Building diagram from specification",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.DIAGRAM_TOOLS,
            function="_build_diagram_from_spec",
            params={
                "node_count": len(spec.nodes),
                "connection_count": len(spec.connections),
                "cluster_count": len(spec.clusters)
            }
        )
        
        # Extract a short title from description
        title = original_description[:50] + "..." if len(original_description) > 50 else original_description
        
        try:
            # Use the build_diagram context manager
            with self.builder.build_diagram(title=title) as builder:
                # Create nodes
                for node in spec.nodes:
                    builder.create_node(
                        node_type=node.type,
                        name=node.name,
                        properties=node.properties
                    )
                
                # Create connections
                for conn in spec.connections:
                    builder.connect_nodes(
                        from_name=conn.from_node,
                        to_name=conn.to_node,
                        label=conn.label
                    )
                
                # Create clusters (with limitations noted in DiagramBuilder)
                for cluster in spec.clusters:
                    builder.create_cluster(
                        cluster_name=cluster.name,
                        node_names=cluster.nodes
                    )
            
            # Get the generated image data
            image_data = self.builder.get_last_image_data()
            
            if not image_data:
                raise ValueError("No image data generated")
            
            logger.info(
                "Successfully built diagram",
                feature=FeatureTag.DIAGRAM_GENERATION,
                module=ModuleTag.DIAGRAM_TOOLS,
                function="_build_diagram_from_spec",
                params={"image_size": len(image_data)}
            )
            
            return image_data
            
        except Exception as e:
            logger.error(
                "Failed to build diagram from specification",
                feature=FeatureTag.DIAGRAM_GENERATION,
                module=ModuleTag.DIAGRAM_TOOLS,
                function="_build_diagram_from_spec",
                error=e
            )
            raise
    
    async def validate_specification(self, spec_json: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a specification without generating a diagram
        
        Args:
            spec_json: JSON specification to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        is_valid, _, error_msg = self.validator.validate(spec_json)
        return is_valid, error_msg