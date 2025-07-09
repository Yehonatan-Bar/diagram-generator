"""
Specification validator for diagram generation
Validates LLM-generated JSON specifications before building diagrams
"""
import json
from typing import Dict, List, Tuple, Optional, Any
from pydantic import BaseModel, Field, ValidationError, field_validator

from ..core.logging import logger, FeatureTag, ModuleTag
from ..core.config import settings
from ..utils.decorators import log_execution_time


class NodeSpec(BaseModel):
    """Specification for a diagram node"""
    type: str = Field(..., description="Type of node (e.g., EC2, RDS, LoadBalancer)")
    name: str = Field(..., description="Unique name for the node")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Optional properties")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is not empty and contains valid characters"""
        if not v or not v.strip():
            raise ValueError("Node name cannot be empty")
        # Remove any characters that might cause issues
        cleaned = v.strip()
        if len(cleaned) > 50:
            raise ValueError("Node name too long (max 50 characters)")
        return cleaned


class ConnectionSpec(BaseModel):
    """Specification for a connection between nodes"""
    # Using 'from_node' and 'to_node' instead of 'from' and 'to' (reserved keywords)
    from_node: str = Field(..., alias="from", description="Source node name")
    to_node: str = Field(..., alias="to", description="Destination node name")
    label: Optional[str] = Field(None, description="Optional connection label")
    
    class Config:
        populate_by_name = True  # Allow both 'from' and 'from_node'


class ClusterSpec(BaseModel):
    """Specification for grouping nodes in a cluster"""
    name: str = Field(..., description="Cluster name")
    nodes: List[str] = Field(..., description="List of node names in this cluster")
    
    @field_validator('nodes')
    @classmethod
    def validate_nodes(cls, v: List[str]) -> List[str]:
        """Ensure cluster has at least one node"""
        if not v:
            raise ValueError("Cluster must contain at least one node")
        return v


class DiagramSpecification(BaseModel):
    """Complete specification for a diagram"""
    nodes: List[NodeSpec] = Field(..., description="List of nodes in the diagram")
    connections: List[ConnectionSpec] = Field(default_factory=list, description="List of connections")
    clusters: List[ClusterSpec] = Field(default_factory=list, description="List of clusters")
    
    @field_validator('nodes')
    @classmethod
    def validate_nodes(cls, v: List[NodeSpec]) -> List[NodeSpec]:
        """Ensure at least one node exists"""
        if not v:
            raise ValueError("Diagram must contain at least one node")
        return v


class SpecificationValidator:
    """Validates LLM-generated specifications"""
    
    def __init__(self, supported_nodes: Optional[List[str]] = None):
        """
        Initialize validator
        
        Args:
            supported_nodes: List of supported node types. Defaults to config value.
        """
        self.supported_nodes = supported_nodes or settings.supported_nodes
        
        logger.info(
            f"Initialized SpecificationValidator",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.VALIDATION,
            function="__init__",
            params={"supported_nodes": self.supported_nodes}
        )
    
    @log_execution_time(FeatureTag.DIAGRAM_GENERATION, ModuleTag.VALIDATION)
    def validate(self, spec_json: str) -> Tuple[bool, Optional[DiagramSpecification], Optional[str]]:
        """
        Validate specification JSON
        
        Args:
            spec_json: JSON string containing diagram specification
            
        Returns:
            Tuple of (is_valid, parsed_spec, error_message)
        """
        logger.debug(
            "Starting specification validation",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.VALIDATION,
            function="validate",
            params={"json_length": len(spec_json)}
        )
        
        # Step 1: Valid JSON?
        try:
            data = json.loads(spec_json)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON: {str(e)}"
            logger.warning(
                error_msg,
                feature=FeatureTag.DIAGRAM_GENERATION,
                module=ModuleTag.VALIDATION,
                function="validate",
                error=e
            )
            return False, None, error_msg
        
        # Step 2: Valid structure?
        try:
            spec = DiagramSpecification(**data)
        except ValidationError as e:
            error_msg = f"Invalid structure: {self._format_validation_error(e)}"
            logger.warning(
                error_msg,
                feature=FeatureTag.DIAGRAM_GENERATION,
                module=ModuleTag.VALIDATION,
                function="validate",
                error=e
            )
            return False, None, error_msg
        
        # Step 3: Valid node types?
        invalid_types = [
            node.type for node in spec.nodes 
            if node.type not in self.supported_nodes
        ]
        if invalid_types:
            error_msg = f"Unsupported node types: {invalid_types}. Supported types: {self.supported_nodes}"
            logger.warning(
                error_msg,
                feature=FeatureTag.DIAGRAM_GENERATION,
                module=ModuleTag.VALIDATION,
                function="validate",
                params={"invalid_types": invalid_types}
            )
            return False, None, error_msg
        
        # Step 4: Check for duplicate node names
        node_names = [node.name for node in spec.nodes]
        if len(node_names) != len(set(node_names)):
            duplicates = [name for name in node_names if node_names.count(name) > 1]
            error_msg = f"Duplicate node names found: {list(set(duplicates))}"
            logger.warning(
                error_msg,
                feature=FeatureTag.DIAGRAM_GENERATION,
                module=ModuleTag.VALIDATION,
                function="validate",
                params={"duplicates": duplicates}
            )
            return False, None, error_msg
        
        # Step 5: Valid connections?
        node_name_set = {node.name for node in spec.nodes}
        for conn in spec.connections:
            if conn.from_node not in node_name_set:
                error_msg = f"Connection references unknown node: '{conn.from_node}'"
                logger.warning(
                    error_msg,
                    feature=FeatureTag.DIAGRAM_GENERATION,
                    module=ModuleTag.VALIDATION,
                    function="validate",
                    params={"unknown_node": conn.from_node}
                )
                return False, None, error_msg
            if conn.to_node not in node_name_set:
                error_msg = f"Connection references unknown node: '{conn.to_node}'"
                logger.warning(
                    error_msg,
                    feature=FeatureTag.DIAGRAM_GENERATION,
                    module=ModuleTag.VALIDATION,
                    function="validate",
                    params={"unknown_node": conn.to_node}
                )
                return False, None, error_msg
        
        # Step 6: Valid clusters?
        for cluster in spec.clusters:
            for node_name in cluster.nodes:
                if node_name not in node_name_set:
                    error_msg = f"Cluster '{cluster.name}' references unknown node: '{node_name}'"
                    logger.warning(
                        error_msg,
                        feature=FeatureTag.DIAGRAM_GENERATION,
                        module=ModuleTag.VALIDATION,
                        function="validate",
                        params={"cluster": cluster.name, "unknown_node": node_name}
                    )
                    return False, None, error_msg
        
        logger.info(
            "Specification validation successful",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.VALIDATION,
            function="validate",
            params={
                "node_count": len(spec.nodes),
                "connection_count": len(spec.connections),
                "cluster_count": len(spec.clusters)
            }
        )
        
        return True, spec, None
    
    def _format_validation_error(self, error: ValidationError) -> str:
        """Format Pydantic validation error into readable message"""
        errors = []
        for err in error.errors():
            loc = " -> ".join(str(l) for l in err['loc'])
            msg = err['msg']
            errors.append(f"{loc}: {msg}")
        return "; ".join(errors)
    
    def suggest_fix(self, error_message: str, original_spec: str) -> str:
        """
        Suggest a fix for common validation errors
        
        Args:
            error_message: The validation error message
            original_spec: The original specification that failed
            
        Returns:
            Suggestion for fixing the error
        """
        suggestions = []
        
        if "Invalid JSON" in error_message:
            suggestions.append("Ensure the response is valid JSON format")
            suggestions.append("Check for missing commas, quotes, or brackets")
        
        elif "Unsupported node types" in error_message:
            suggestions.append(f"Use only these node types: {', '.join(self.supported_nodes)}")
            suggestions.append("Check spelling and capitalization of node types")
        
        elif "unknown node" in error_message:
            suggestions.append("Ensure all nodes are defined before being referenced in connections or clusters")
            suggestions.append("Check spelling of node names in connections matches node definitions")
        
        elif "Duplicate node names" in error_message:
            suggestions.append("Each node must have a unique name")
            suggestions.append("Consider adding numbers or descriptive suffixes to duplicate names")
        
        else:
            suggestions.append("Check the specification structure matches the expected format")
            suggestions.append("Ensure all required fields are present")
        
        return ". ".join(suggestions)