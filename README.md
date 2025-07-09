# 🎨 AI-Powered Diagram Generator

Transform natural language descriptions into professional cloud architecture diagrams using LLM-powered agents. Built with FastAPI, this service provides a REST API for generating AWS architecture diagrams from plain English descriptions.

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

</div>

## 🚀 Quick Start

Get started in under 5 minutes! Check out our [Quick Start Guide](docs/QUICKSTART.md) or follow the installation instructions below.

## ✨ Key Features

- **🤖 Natural Language Understanding**: Describe your architecture in plain English - no diagram syntax knowledge required
- **☁️ AWS Component Support**: EC2, RDS, Load Balancers, SQS, Lambda, S3 - all the building blocks you need
- **🚀 High-Performance API**: Async/stateless design with FastAPI for lightning-fast responses
- **🧪 Mock Mode**: Test and develop without API keys using realistic mock responses
- **📊 Smart Logging**: Two-dimensional tagging system (Feature × Module) for precise debugging
- **🐳 Production Ready**: Docker support with multi-stage builds and health checks
- **💬 Conversational Assistant**: Interactive mode for clarifying requirements and iterative design
- **🔧 Self-Healing**: Automatic specification repair when validation fails
- **📝 Type Safety**: Full Pydantic validation for all requests and responses

## 🎯 Use Cases

- **Architecture Documentation**: Quickly create diagrams for documentation and presentations
- **Design Reviews**: Generate consistent diagrams for architecture review meetings  
- **Proof of Concepts**: Rapidly prototype cloud architectures
- **Learning Tool**: Understand AWS components and their relationships
- **CI/CD Integration**: Automatically generate architecture diagrams from code comments

## 📋 Requirements

- Python 3.12+
- UV package manager (recommended) or pip
- Graphviz (system dependency for diagram generation)

## 🛠️ Installation

### Option 1: Using UV (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd diagram-generator
```

2. Install UV if not already installed:
```bash
# Using pip
pip install uv

# Or using the installer script
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Create virtual environment and install dependencies:
```bash
# Create venv and install all dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Or install with dev dependencies
uv pip install -e ".[dev]"
```

### Option 2: Using pip

1. Clone the repository:
```bash
git clone <repository-url>
cd diagram-generator
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
# Note: diagrams package v0.24.4+ is required (avoids typed-ast issues with Python 3.12)
pip install -r requirements.txt
```

### Install System Dependencies

Install Graphviz:
```bash
# Ubuntu/Debian
sudo apt-get install graphviz

# macOS
brew install graphviz

# Windows
# Download from https://graphviz.org/download/
```

### Environment Configuration

Copy environment configuration:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## 🚀 Running the API

### Local Development

Start the API server:
```bash
# With virtual environment activated
python run.py

# Or directly
./venv/bin/python run.py
```

### Docker Deployment

Run with Docker:
```bash
# Build the image
./docker/build.sh

# Configure environment
cp .env.docker.example .env
# Edit .env with your API keys

# Deploy
docker-compose up -d

# View logs
docker-compose logs -f diagram-generator
```

For development with hot reload:
```bash
docker-compose -f docker-compose.dev.yml up
```

The API will be available at:
- API endpoints: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc

## 📡 API Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check with dependency status
- `GET /health/live` - Liveness check

### Diagram Generation
- `POST /api/v1/diagram/generate` - Generate diagram from description
- `POST /api/v1/diagram/assistant` - Conversational assistant
- `POST /api/v1/diagram/validate` - Validate diagram specification

Example request:
```bash
curl -X POST "http://localhost:8000/api/v1/diagram/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a web app with load balancer and database",
    "output_format": "base64"
  }'
```

## 🏗️ Architecture

The project follows a clean, modular architecture:

```
diagram-generator/
├── src/
│   ├── api/           # FastAPI endpoints
│   ├── agents/        # LLM agent implementations
│   ├── tools/         # Diagram tools wrapping diagrams package
│   │   ├── diagram_builder.py  # DiagramBuilder class for creating diagrams
│   │   └── validator.py        # Specification validator with repair suggestions
│   ├── llm/           # LLM client abstractions
│   │   ├── base.py            # Abstract base class for LLM clients
│   │   ├── gemini_client.py   # Gemini API integration
│   │   ├── mock_client.py     # Mock client for testing
│   │   └── prompt_manager.py  # Secure prompt management
│   ├── core/          # Config, logging, utilities
│   │   ├── config.py          # Pydantic settings management
│   │   └── logging.py         # Dual-tag logging system
│   └── utils/         # Helper functions
│       └── decorators.py      # Logging and error handling decorators
├── tests/             # Test suite
├── docker/            # Docker configuration
└── docs/              # Documentation
```

## 🔧 Configuration

All configuration is managed through environment variables. Copy `.env.example` to `.env` and customize as needed.

### Core Settings

| Variable | Description | Default | Options |
|----------|-------------|---------|----------|
| `LLM_PROVIDER` | LLM provider to use | `gemini` | `gemini`, `openai`, `mock` |
| `USE_MOCK_LLM` | Enable mock mode for testing | `false` | `true`, `false` |
| `LLM_API_KEY` | API key for the LLM provider | - | Your API key |
| `LLM_MODEL` | Model to use | `gemini-pro` | Provider-specific |

### API Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `API_TITLE` | API title for documentation | `Diagram Generator API` |
| `API_VERSION` | API version | `1.0.0` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `LOG_FORMAT` | Log output format | `json` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `ENVIRONMENT` | Deployment environment | `development` |

### Feature Flags

| Variable | Description | Default |
|----------|-------------|---------|
| `CLEANUP_TEMP_FILES` | Auto-cleanup temporary diagram files | `true` |
| `MAX_RETRY_ATTEMPTS` | Max retries for diagram generation | `3` |
| `SUPPORTED_NODES` | Available AWS components | `EC2,RDS,LoadBalancer,SQS,Lambda,S3` |

### Security Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `REQUIRE_API_KEY` | Enable API key authentication | `false` |
| `ALLOWED_API_KEYS` | Comma-separated list of valid API keys | - |

### Example Configurations

**Development Mode (with mock LLM)**:
```bash
USE_MOCK_LLM=true
LOG_LEVEL=DEBUG
LOG_FORMAT=text
ENVIRONMENT=development
```

**Production Mode**:
```bash
LLM_PROVIDER=gemini
LLM_API_KEY=your-actual-api-key
LOG_LEVEL=INFO
LOG_FORMAT=json
ENVIRONMENT=production
REQUIRE_API_KEY=true
ALLOWED_API_KEYS=key1,key2,key3
CORS_ORIGINS=https://yourdomain.com
```

## 📚 API Usage Examples

### Generate a Simple Web Application

```bash
curl -X POST "http://localhost:8000/api/v1/diagram/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a web app with load balancer, 2 EC2 instances, and RDS database",
    "output_format": "base64"
  }'
```

<details>
<summary>Response</summary>

```json
{
  "success": true,
  "diagram_data": "iVBORw0KGgoAAAANS...",
  "metadata": {
    "nodes_created": 4,
    "connections": 4,
    "clusters": 1
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-08T12:00:00Z"
}
```

</details>

### Using the Assistant for Complex Architectures

```python
import httpx
import asyncio

async def design_architecture():
    async with httpx.AsyncClient() as client:
        # Start conversation
        response = await client.post(
            "http://localhost:8000/api/v1/diagram/assistant",
            json={
                "message": "I need a serverless data processing pipeline"
            }
        )
        
        result = response.json()
        print(f"Assistant: {result['message']}")
        
        # Provide more details
        response = await client.post(
            "http://localhost:8000/api/v1/diagram/assistant",
            json={
                "message": "It should handle file uploads to S3, trigger Lambda for processing, and store results in RDS",
                "conversation_history": [
                    {"role": "user", "content": "I need a serverless data processing pipeline"},
                    {"role": "assistant", "content": result['message']}
                ]
            }
        )
        
        final_result = response.json()
        if final_result['diagram_data']:
            print("Diagram generated successfully!")
            # Save the diagram
            with open("pipeline.png", "wb") as f:
                f.write(base64.b64decode(final_result['diagram_data']))

asyncio.run(design_architecture())
```

### Validate a Specification

```bash
curl -X POST "http://localhost:8000/api/v1/diagram/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "specification": "{\"nodes\": [{\"type\": \"EC2\", \"name\": \"WebServer\"}], \"connections\": []}"
  }'
```

## 🎨 Example Architectures

### 1. Simple Web Application
**Description**: "Create a web application with a load balancer and database"

```json
{
  "nodes": [
    {"type": "LoadBalancer", "name": "ALB"},
    {"type": "EC2", "name": "WebServer"},
    {"type": "RDS", "name": "Database"}
  ],
  "connections": [
    {"from": "ALB", "to": "WebServer"},
    {"from": "WebServer", "to": "Database"}
  ]
}
```

### 2. Serverless Event Processing
**Description**: "Build a serverless system that processes files uploaded to S3"

```json
{
  "nodes": [
    {"type": "S3", "name": "InputBucket"},
    {"type": "Lambda", "name": "ProcessorFunction"},
    {"type": "SQS", "name": "ProcessingQueue"},
    {"type": "RDS", "name": "ResultsDB"}
  ],
  "connections": [
    {"from": "InputBucket", "to": "ProcessorFunction", "label": "trigger"},
    {"from": "ProcessorFunction", "to": "ProcessingQueue", "label": "queue"},
    {"from": "ProcessorFunction", "to": "ResultsDB", "label": "store"}
  ]
}
```

### 3. Microservices with Message Queue
**Description**: "Design a microservices architecture with load balancer, multiple services, message queue, and database"

```json
{
  "nodes": [
    {"type": "LoadBalancer", "name": "ALB"},
    {"type": "EC2", "name": "OrderService"},
    {"type": "EC2", "name": "PaymentService"},
    {"type": "EC2", "name": "NotificationService"},
    {"type": "SQS", "name": "EventQueue"},
    {"type": "RDS", "name": "OrderDB"},
    {"type": "RDS", "name": "PaymentDB"}
  ],
  "connections": [
    {"from": "ALB", "to": "OrderService"},
    {"from": "ALB", "to": "PaymentService"},
    {"from": "OrderService", "to": "EventQueue"},
    {"from": "PaymentService", "to": "EventQueue"},
    {"from": "EventQueue", "to": "NotificationService"},
    {"from": "OrderService", "to": "OrderDB"},
    {"from": "PaymentService", "to": "PaymentDB"}
  ],
  "clusters": [
    {"name": "Services", "nodes": ["OrderService", "PaymentService", "NotificationService"]},
    {"name": "Databases", "nodes": ["OrderDB", "PaymentDB"]}
  ]
}
```

## 🏛️ Architecture Overview

The diagram generator uses a modular, agent-based architecture:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FastAPI App   │────▶│  Agent Layer    │────▶│   LLM Layer     │
│                 │     │                 │     │                 │
│ • Endpoints     │     │ • DiagramAgent  │     │ • Gemini        │
│ • Middleware    │     │ • AssistantAgent│     │ • OpenAI        │
│ • Health Checks │     │                 │     │ • Mock          │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Core Layer    │     │   Tools Layer   │     │  Utils Layer    │
│                 │     │                 │     │                 │
│ • Config        │     │ • DiagramBuilder│     │ • Decorators    │
│ • Logging       │     │ • Validator     │     │ • Helpers       │
│ • Settings      │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Key Components

#### 1. Agent Layer
- **DiagramAgent**: Orchestrates the diagram generation process, handling retries and validation
- **AssistantAgent**: Provides conversational interface for iterative design

#### 2. LLM Abstraction Layer
- **BaseLLMClient**: Abstract interface for all LLM providers
- **Provider Implementations**: Gemini, OpenAI, and Mock clients
- **PromptManager**: Secure prompt templating with injection protection

#### 3. Dual-Tag Logging System
- **Feature Tags**: Track functionality (API, AGENTS, TOOLS, LLM, etc.)
- **Module Tags**: Track code location (API_ENDPOINTS, AGENT_DIAGRAM, etc.)
- **Benefits**: Precise debugging, performance analysis, error tracking

```python
# Example: Analyzing logs by feature and module
from src.core.logging import logger

# Get all API-related errors
api_errors = logger.get_logs_by_feature(FeatureTag.API, level="ERROR")

# Get all diagram generation activities
diagram_logs = logger.get_logs_by_module(ModuleTag.AGENT_DIAGRAM)

# Get performance metrics
metrics = logger.get_performance_metrics()
print(f"Average API response time: {metrics['api']['avg_duration']}ms")
```

## 🧪 Testing

The project includes comprehensive unit and integration tests covering all components.

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── unit/                # Unit tests for individual components
│   ├── test_config.py   # Configuration and settings tests
│   ├── test_logging.py  # Logging system tests
│   ├── test_llm_clients.py  # LLM client tests
│   ├── test_tools.py    # Diagram tools tests
│   ├── test_agents.py   # Agent implementation tests
│   └── test_decorators.py   # Utility decorator tests
└── integration/         # Integration tests
    └── test_api.py      # API endpoint tests
```

### Running Tests

```bash
# Using the test runner script
python run_tests.py              # Run all tests
python run_tests.py unit         # Run only unit tests
python run_tests.py integration  # Run only integration tests
python run_tests.py coverage     # Run with coverage report

# Or using pytest directly
pytest                          # Run all tests
pytest tests/unit/              # Run unit tests
pytest tests/integration/       # Run integration tests
pytest -v                       # Verbose output
pytest --cov=src --cov-report=html  # With coverage
```

### Test Coverage

The test suite covers:
- ✅ Configuration management and environment variables
- ✅ Dual-tag logging system with analysis features
- ✅ LLM client abstraction and mock implementation
- ✅ Diagram builder and specification validator
- ✅ Agent orchestration and conversation handling
- ✅ All API endpoints and health checks
- ✅ Error handling and edge cases
- ✅ Async/await patterns

### Testing with Mock Mode

The mock LLM system allows testing without API keys:

```python
import os
os.environ['USE_MOCK_LLM'] = 'true'

from src.agents.diagram_agent import DiagramAgent

agent = DiagramAgent()
result = await agent.generate_diagram("Create a simple web app")
# Returns realistic mock response
```

## 🛠️ Development Guide

### Adding New Cloud Components

1. Import the component from the diagrams package:
```python
# In src/tools/diagram_builder.py
from diagrams.aws.compute import ECS  # Example: adding ECS support
```

2. Add to the NODE_TYPES mapping:
```python
NODE_TYPES = {
    "EC2": EC2,
    "ECS": ECS,  # New component
    # ... other components
}
```

3. Update the environment configuration:
```bash
SUPPORTED_NODES=EC2,RDS,LoadBalancer,SQS,Lambda,S3,ECS
```

### Adding New LLM Providers

1. Create a new client in `src/llm/`:
```python
from .base import BaseLLMClient, LLMResponse

class AnthropicClient(BaseLLMClient):
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        # Implementation here
        pass
```

2. Register in the factory (`src/llm/client.py`):
```python
class LLMProvider(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"  # New provider
    MOCK = "mock"
```

### Code Style Guidelines

- Use type hints for all function parameters and returns
- Follow PEP 8 with 100-character line limit
- Use descriptive variable names
- Add docstrings to all public functions and classes
- Use the dual-tag logging system for all log messages

## 🚨 Troubleshooting

### Common Issues

#### 1. "Module 'diagrams' not found"
**Solution**: Install system dependencies:
```bash
# Ubuntu/Debian
sudo apt-get install graphviz

# macOS
brew install graphviz
```

#### 2. "API key not found" in production
**Solution**: Ensure environment variables are set:
```bash
export LLM_API_KEY="your-api-key"
# Or use .env file
```

#### 3. "Connection refused" when accessing API
**Solution**: Check if the service is running:
```bash
curl http://localhost:8000/health
```

#### 4. Slow response times
**Solution**: Enable performance logging:
```bash
LOG_LEVEL=DEBUG
# Check logs for slow operations
```

### Debugging with Logs

```python
# Get recent errors
from src.core.logging import logger

errors = logger.get_error_summary()
for feature, count in errors.items():
    print(f"{feature}: {count} errors")

# Analyze specific request
logs = logger.get_logs_by_time(
    start_time=datetime.now() - timedelta(minutes=5)
)
```

## 🚀 Production Deployment

### Pre-deployment Checklist

- [ ] Set `USE_MOCK_LLM=false`
- [ ] Configure proper API keys
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure CORS origins
- [ ] Enable API key authentication
- [ ] Set up monitoring (logs, metrics)
- [ ] Configure rate limiting
- [ ] Set up SSL/TLS
- [ ] Configure backup strategy

### Monitoring & Observability

1. **Health Monitoring**:
```bash
# Kubernetes readiness probe
curl http://localhost:8000/health/ready

# Liveness probe
curl http://localhost:8000/health/live
```

2. **Log Analysis**:
```bash
# Stream logs
docker-compose logs -f diagram-generator | jq '.'

# Filter by feature
docker-compose logs diagram-generator | jq 'select(.feature == "API")'
```

3. **Performance Metrics**:
```python
# Built-in performance analysis
metrics = logger.get_performance_metrics()
print(json.dumps(metrics, indent=2))
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Areas for Contribution

- 🧪 Add more test coverage
- 📚 Improve documentation
- 🎨 Add support for more cloud providers (Azure, GCP)
- 🚀 Performance optimizations
- 🐛 Bug fixes
- ✨ New features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Diagrams](https://diagrams.mingrammer.com/) - The amazing library that powers our diagram generation
- [FastAPI](https://fastapi.tiangolo.com/) - For the high-performance web framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) - For robust data validation

---

<div align="center">

**Built with ❤️ by the AI Diagram Generator Team**

[Report Bug](https://github.com/yourusername/diagram-generator/issues) · [Request Feature](https://github.com/yourusername/diagram-generator/issues)

</div>