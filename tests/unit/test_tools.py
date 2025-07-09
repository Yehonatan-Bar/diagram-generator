"""
Unit tests for diagram tools (builder and validator).
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.tools.diagram_builder import DiagramBuilder, DiagramGenerationError
from src.tools.validator import (
    NodeSpec, ConnectionSpec, ClusterSpec, DiagramSpecification,
    SpecificationValidator, ValidationError
)


class TestDiagramBuilder:
    """Test DiagramBuilder functionality."""
    
    def test_builder_initialization(self):
        """Test DiagramBuilder initialization."""
        builder = DiagramBuilder()
        assert builder is not None
        assert builder._diagram is None
        assert builder._nodes == {}
        assert builder._last_image_data is None
    
    def test_create_node(self):
        """Test creating nodes."""
        builder = DiagramBuilder()
        
        # Create valid node
        result = builder.create_node("EC2", "WebServer")
        assert result is True
        assert "WebServer" in builder._nodes
        
        # Try to create duplicate node
        result = builder.create_node("EC2", "WebServer")
        assert result is False  # Should fail for duplicate
    
    def test_create_invalid_node_type(self):
        """Test creating node with invalid type."""
        builder = DiagramBuilder()
        
        result = builder.create_node("InvalidType", "Server")
        assert result is False
    
    def test_connect_nodes(self):
        """Test connecting nodes."""
        builder = DiagramBuilder()
        
        # Create nodes first
        builder.create_node("EC2", "WebServer")
        builder.create_node("RDS", "Database")
        
        # Connect them
        result = builder.connect_nodes("WebServer", "Database", "connects to")
        assert result is True
    
    def test_connect_nonexistent_nodes(self):
        """Test connecting non-existent nodes."""
        builder = DiagramBuilder()
        
        result = builder.connect_nodes("NonExistent1", "NonExistent2")
        assert result is False
    
    def test_create_cluster(self):
        """Test creating clusters."""
        builder = DiagramBuilder()
        
        # Create nodes
        builder.create_node("EC2", "Server1")
        builder.create_node("EC2", "Server2")
        
        # Create cluster
        result = builder.create_cluster("WebCluster", ["Server1", "Server2"])
        assert result is True
    
    @patch('src.tools.diagram_builder.Diagram')
    def test_build_diagram_simple(self, mock_diagram_class):
        """Test building a simple diagram."""
        # Setup mock
        mock_diagram = MagicMock()
        mock_diagram_class.return_value.__enter__.return_value = mock_diagram
        
        builder = DiagramBuilder()
        
        spec = {
            "nodes": [
                {"type": "EC2", "name": "WebServer"},
                {"type": "RDS", "name": "Database"}
            ],
            "connections": [
                {"from": "WebServer", "to": "Database"}
            ],
            "clusters": []
        }
        
        result = builder.build_diagram(spec)
        
        assert result is True
        assert builder._diagram is not None
        mock_diagram.render.assert_called_once()
    
    @patch('src.tools.diagram_builder.Diagram')
    @patch('src.tools.diagram_builder.base64.b64encode')
    @patch('builtins.open')
    def test_get_last_image_data(self, mock_open, mock_b64encode, mock_diagram_class):
        """Test getting last generated image data."""
        # Setup mocks
        mock_diagram = MagicMock()
        mock_diagram_class.return_value.__enter__.return_value = mock_diagram
        mock_b64encode.return_value = b"base64data"
        mock_open.return_value.__enter__.return_value.read.return_value = b"imagedata"
        
        builder = DiagramBuilder()
        
        # Build a diagram first
        spec = {
            "nodes": [{"type": "EC2", "name": "Server"}],
            "connections": [],
            "clusters": []
        }
        builder.build_diagram(spec)
        
        # Get image data
        image_data = builder.get_last_image_data()
        
        assert image_data == "base64data"
        assert builder._last_image_data == "base64data"
    
    def test_context_manager(self):
        """Test DiagramBuilder as context manager."""
        with DiagramBuilder() as builder:
            assert builder is not None
            builder.create_node("EC2", "TestServer")
        
        # After exiting context, should be cleaned up
        assert True  # If we get here, context manager worked
    
    def test_build_with_invalid_spec(self):
        """Test building with invalid specification."""
        builder = DiagramBuilder()
        
        # Invalid spec - missing required fields
        spec = {"invalid": "spec"}
        
        result = builder.build_diagram(spec)
        assert result is False


class TestValidationModels:
    """Test Pydantic validation models."""
    
    def test_node_spec_valid(self):
        """Test valid NodeSpec creation."""
        node = NodeSpec(
            type="EC2",
            name="WebServer",
            properties={"size": "t2.micro"}
        )
        
        assert node.type == "EC2"
        assert node.name == "WebServer"
        assert node.properties["size"] == "t2.micro"
    
    def test_node_spec_missing_name(self):
        """Test NodeSpec with missing name."""
        with pytest.raises(ValidationError):
            NodeSpec(type="EC2")  # Missing required 'name'
    
    def test_connection_spec_valid(self):
        """Test valid ConnectionSpec creation."""
        connection = ConnectionSpec(
            from_node="Server1",
            to="Server2",
            label="connects"
        )
        
        assert connection.from_node == "Server1"
        assert connection.to == "Server2"
        assert connection.label == "connects"
    
    def test_cluster_spec_valid(self):
        """Test valid ClusterSpec creation."""
        cluster = ClusterSpec(
            name="WebCluster",
            nodes=["Server1", "Server2"],
            properties={"region": "us-east-1"}
        )
        
        assert cluster.name == "WebCluster"
        assert len(cluster.nodes) == 2
        assert cluster.properties["region"] == "us-east-1"
    
    def test_diagram_specification_complete(self):
        """Test complete DiagramSpecification."""
        spec = DiagramSpecification(
            nodes=[
                NodeSpec(type="EC2", name="Server"),
                NodeSpec(type="RDS", name="Database")
            ],
            connections=[
                ConnectionSpec(from_node="Server", to="Database")
            ],
            clusters=[
                ClusterSpec(name="Cluster", nodes=["Server"])
            ]
        )
        
        assert len(spec.nodes) == 2
        assert len(spec.connections) == 1
        assert len(spec.clusters) == 1


class TestSpecificationValidator:
    """Test SpecificationValidator functionality."""
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = SpecificationValidator()
        assert validator is not None
    
    def test_validate_valid_spec(self):
        """Test validating a valid specification."""
        validator = SpecificationValidator()
        
        spec_dict = {
            "nodes": [
                {"type": "EC2", "name": "WebServer"},
                {"type": "RDS", "name": "Database"}
            ],
            "connections": [
                {"from": "WebServer", "to": "Database"}
            ],
            "clusters": []
        }
        
        is_valid, spec, errors = validator.validate(json.dumps(spec_dict))
        
        assert is_valid is True
        assert spec is not None
        assert len(errors) == 0
    
    def test_validate_invalid_json(self):
        """Test validating invalid JSON."""
        validator = SpecificationValidator()
        
        is_valid, spec, errors = validator.validate("invalid json {")
        
        assert is_valid is False
        assert spec is None
        assert len(errors) > 0
        assert "JSON parsing error" in errors[0]
    
    def test_validate_invalid_node_type(self):
        """Test validating specification with invalid node type."""
        validator = SpecificationValidator()
        
        spec_dict = {
            "nodes": [
                {"type": "InvalidType", "name": "Server"}
            ],
            "connections": [],
            "clusters": []
        }
        
        is_valid, spec, errors = validator.validate(json.dumps(spec_dict))
        
        assert is_valid is False
        assert len(errors) > 0
        assert "Invalid node type" in errors[0]
    
    def test_validate_invalid_connection(self):
        """Test validating specification with invalid connection."""
        validator = SpecificationValidator()
        
        spec_dict = {
            "nodes": [
                {"type": "EC2", "name": "Server"}
            ],
            "connections": [
                {"from": "NonExistent", "to": "Server"}
            ],
            "clusters": []
        }
        
        is_valid, spec, errors = validator.validate(json.dumps(spec_dict))
        
        assert is_valid is False
        assert len(errors) > 0
        assert "not found in nodes" in errors[0]
    
    def test_suggest_fix_for_node_type(self):
        """Test fix suggestions for invalid node types."""
        validator = SpecificationValidator()
        
        suggestion = validator.suggest_fix("Invalid node type 'WebServer'")
        
        assert suggestion is not None
        assert "EC2" in suggestion  # Should suggest valid types
    
    def test_suggest_fix_for_missing_node(self):
        """Test fix suggestions for missing nodes."""
        validator = SpecificationValidator()
        
        suggestion = validator.suggest_fix("Node 'Database' not found in nodes")
        
        assert suggestion is not None
        assert "Add the missing node" in suggestion
    
    def test_validate_complex_spec(self):
        """Test validating a complex specification."""
        validator = SpecificationValidator()
        
        spec_dict = {
            "nodes": [
                {"type": "LoadBalancer", "name": "ALB"},
                {"type": "EC2", "name": "Server1"},
                {"type": "EC2", "name": "Server2"},
                {"type": "RDS", "name": "Database"}
            ],
            "connections": [
                {"from": "ALB", "to": "Server1"},
                {"from": "ALB", "to": "Server2"},
                {"from": "Server1", "to": "Database"},
                {"from": "Server2", "to": "Database"}
            ],
            "clusters": [
                {
                    "name": "WebServers",
                    "nodes": ["Server1", "Server2"]
                }
            ]
        }
        
        is_valid, spec, errors = validator.validate(json.dumps(spec_dict))
        
        assert is_valid is True
        assert spec is not None
        assert len(spec.nodes) == 4
        assert len(spec.connections) == 4
        assert len(spec.clusters) == 1