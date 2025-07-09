"""
Diagram builder tool that wraps the diagrams package
This acts as an interface between LLM agents and the diagrams library
"""
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import EC2, Lambda
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB
from diagrams.aws.integration import SQS
from diagrams.aws.storage import S3

from ..core.logging import logger, FeatureTag, ModuleTag
from ..core.config import settings
from ..utils.decorators import log_execution_time


class DiagramBuilder:
    """
    Wrapper around diagrams package - the LLM doesn't know about this
    This is our tool that translates specifications into actual diagrams
    """
    
    # Node type mapping - maps string names to actual diagram classes
    NODE_TYPES = {
        "EC2": EC2,
        "RDS": RDS,
        "LoadBalancer": ELB,
        "SQS": SQS,
        "Lambda": Lambda,
        "S3": S3
    }
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the diagram builder
        
        Args:
            temp_dir: Directory for temporary files. Defaults to system temp or config
        """
        self.temp_dir = Path(temp_dir or settings.temp_dir)
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        self.nodes: Dict[str, Any] = {}  # name -> node instance mapping
        self._current_diagram = None
        self._diagram_context = None
        self._last_image_data = None
        self._last_image_path = None
        
        logger.info(
            "Initialized DiagramBuilder",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.DIAGRAM_TOOLS,
            function="__init__",
            params={"temp_dir": str(self.temp_dir)}
        )
    
    @contextmanager
    @log_execution_time(FeatureTag.DIAGRAM_GENERATION, ModuleTag.DIAGRAM_TOOLS)
    def build_diagram(self, title: str = "Cloud Architecture", filename: Optional[str] = None):
        """
        Context manager for building diagrams with automatic cleanup
        
        Args:
            title: Title of the diagram
            filename: Optional filename (without extension)
            
        Yields:
            tuple: (self, image_path) where image_path is the generated PNG file
        """
        if filename is None:
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".png",
                dir=self.temp_dir,
                delete=False
            )
            output_path = temp_file.name
            base_name = output_path[:-4]  # Remove .png extension
        else:
            base_name = str(self.temp_dir / filename)
            output_path = f"{base_name}.png"
        
        logger.debug(
            f"Starting diagram build: {title}",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.DIAGRAM_TOOLS,
            function="build_diagram",
            params={"title": title, "output_path": output_path}
        )
        
        try:
            # Reset node tracking for new diagram
            self.nodes = {}
            
            # Create diagram context
            with Diagram(title, filename=base_name, show=False, direction="TB") as diagram:
                self._current_diagram = diagram
                yield self
            
            # Ensure the diagram was created
            if not Path(output_path).exists():
                raise FileNotFoundError(f"Diagram file not created: {output_path}")
            
            # Read the generated image data
            with open(output_path, "rb") as f:
                image_data = f.read()
            
            logger.info(
                f"Successfully generated diagram: {title}",
                feature=FeatureTag.DIAGRAM_GENERATION,
                module=ModuleTag.DIAGRAM_TOOLS,
                function="build_diagram",
                params={"image_size": len(image_data)}
            )
            
            # Store the image data for retrieval
            self._last_image_data = image_data
            self._last_image_path = output_path
            
        except Exception as e:
            logger.error(
                f"Error building diagram: {str(e)}",
                feature=FeatureTag.DIAGRAM_GENERATION,
                module=ModuleTag.DIAGRAM_TOOLS,
                function="build_diagram",
                error=e
            )
            raise
            
        finally:
            # Cleanup temp files if configured
            if settings.cleanup_temp_files and Path(output_path).exists():
                try:
                    os.unlink(output_path)
                    logger.debug(
                        f"Cleaned up temp file: {output_path}",
                        feature=FeatureTag.DIAGRAM_GENERATION,
                        module=ModuleTag.DIAGRAM_TOOLS,
                        function="build_diagram"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to cleanup temp file: {output_path}",
                        feature=FeatureTag.DIAGRAM_GENERATION,
                        module=ModuleTag.DIAGRAM_TOOLS,
                        function="build_diagram",
                        error=e
                    )
            
            self._current_diagram = None
    
    def create_node(self, node_type: str, name: str, properties: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a node of specified type
        
        Args:
            node_type: Type of node (must be in NODE_TYPES)
            name: Unique name for the node
            properties: Optional properties (currently unused but reserved for future)
            
        Returns:
            The created node instance
            
        Raises:
            ValueError: If node type is not supported or name already exists
        """
        if node_type not in self.NODE_TYPES:
            supported = ", ".join(self.NODE_TYPES.keys())
            raise ValueError(f"Unsupported node type: {node_type}. Supported types: {supported}")
        
        if name in self.nodes:
            raise ValueError(f"Node with name '{name}' already exists")
        
        logger.debug(
            f"Creating node: {name} of type {node_type}",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.DIAGRAM_TOOLS,
            function="create_node",
            params={"node_type": node_type, "name": name}
        )
        
        NodeClass = self.NODE_TYPES[node_type]
        node = NodeClass(name)
        self.nodes[name] = node
        
        return node
    
    def connect_nodes(self, from_name: str, to_name: str, label: Optional[str] = None):
        """
        Create connection between nodes
        
        Args:
            from_name: Name of source node
            to_name: Name of destination node
            label: Optional label for the connection
            
        Raises:
            ValueError: If either node doesn't exist
        """
        if from_name not in self.nodes:
            raise ValueError(f"Source node not found: {from_name}")
        if to_name not in self.nodes:
            raise ValueError(f"Destination node not found: {to_name}")
        
        logger.debug(
            f"Connecting nodes: {from_name} -> {to_name}",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.DIAGRAM_TOOLS,
            function="connect_nodes",
            params={"from": from_name, "to": to_name, "label": label}
        )
        
        from_node = self.nodes[from_name]
        to_node = self.nodes[to_name]
        
        if label:
            from_node >> Edge(label=label) >> to_node
        else:
            from_node >> to_node
    
    def create_cluster(self, cluster_name: str, node_names: List[str]):
        """
        Group nodes in a cluster
        
        Note: This is a simplified implementation. In the diagrams library,
        clusters need to be created before nodes are added to them.
        This method is here for API compatibility but has limitations.
        
        Args:
            cluster_name: Name of the cluster
            node_names: List of node names to include
            
        Raises:
            ValueError: If any node doesn't exist
        """
        # Validate all nodes exist
        for name in node_names:
            if name not in self.nodes:
                raise ValueError(f"Node not found for cluster: {name}")
        
        logger.warning(
            f"Cluster creation after nodes is limited in diagrams library",
            feature=FeatureTag.DIAGRAM_GENERATION,
            module=ModuleTag.DIAGRAM_TOOLS,
            function="create_cluster",
            params={"cluster_name": cluster_name, "nodes": node_names}
        )
        
        # Note: In a full implementation, we'd need to restructure how nodes
        # are created to properly support clusters. For now, we just log it.
    
    def get_supported_node_types(self) -> List[str]:
        """Get list of supported node types"""
        return list(self.NODE_TYPES.keys())
    
    def validate_node_exists(self, node_name: str) -> bool:
        """Check if a node with given name exists"""
        return node_name in self.nodes
    
    def get_last_image_data(self) -> Optional[bytes]:
        """Get the last generated image data"""
        return self._last_image_data