# 📚 Comprehensive Deployment & Testing Guide

This guide provides detailed instructions for running and testing the AI-Powered Diagram Generator in various environments.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 minutes)](#quick-start-5-minutes)
3. [Development Setup](#development-setup)
4. [Production Deployment](#production-deployment)
5. [Testing the Application](#testing-the-application)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Configuration](#advanced-configuration)

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Python**: 3.12 or higher
- **Memory**: Minimum 2GB RAM
- **Disk Space**: 1GB free space
- **Network**: Internet connection for LLM API calls

### Required Software
- **Git**: For cloning the repository
- **Docker & Docker Compose**: For containerized deployment (optional)
- **UV**: Python package manager (or pip as alternative)
- **Graphviz**: System dependency for diagram generation

## 🚀 Quick Start (5 minutes)

### Option 1: Docker (Fastest)

```bash
# 1. Clone and navigate to the project
git clone https://github.com/yourusername/diagram-generator.git
cd diagram-generator

# 2. Set up environment
cp .env.docker.example .env
echo "USE_MOCK_LLM=true" >> .env  # Start with mock mode

# 3. Launch the application
docker-compose -f docker-compose.uv.yml up -d

# 4. Verify it's running
curl http://localhost:8000/health

# 5. Generate your first diagram
curl -X POST http://localhost:8000/api/v1/diagram/generate \
  -H "Content-Type: application/json" \
  -d '{"description": "Create a simple web app with database"}' \
  --output my-first-diagram.png

# 6. Open the generated diagram
open my-first-diagram.png  # macOS
# xdg-open my-first-diagram.png  # Linux
# start my-first-diagram.png  # Windows
```

### Option 2: Local Development (10 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/diagram-generator.git
cd diagram-generator

# 2. Install UV (if not installed)
pip install uv

# 3. Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# 4. Install Graphviz
# macOS
brew install graphviz

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y graphviz

# Windows
# Download from: https://graphviz.org/download/
# Add to PATH after installation

# 5. Configure environment
cp .env.example .env
echo "USE_MOCK_LLM=true" >> .env  # Start with mock mode

# 6. Run the application
python run.py

# 7. Test in another terminal
curl http://localhost:8000/health
```

## 🛠️ Development Setup

### 1. Complete Local Setup with Real LLM

```bash
# Clone and setup
git clone https://github.com/yourusername/diagram-generator.git
cd diagram-generator

# Install UV
pip install uv

# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install all dependencies including dev tools
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Install Graphviz (required)
# See platform-specific instructions above
```

### 2. Configure API Keys

#### For Gemini (Recommended - Free)
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to your `.env` file:

```bash
LLM_PROVIDER=gemini
LLM_API_KEY=your-gemini-api-key-here
LLM_MODEL=gemini-pro
USE_MOCK_LLM=false
```

#### For OpenAI
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to your `.env` file:

```bash
LLM_PROVIDER=openai
LLM_API_KEY=your-openai-api-key-here
LLM_MODEL=gpt-4
USE_MOCK_LLM=false
```

### 3. Run in Development Mode

```bash
# With auto-reload
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Or use the run script
python run.py
```

### 4. Access Development Tools

- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/health/ready

## 🚢 Production Deployment

### 1. Docker Production Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/diagram-generator.git
cd diagram-generator

# 2. Create production environment file
cp .env.docker.example .env.prod

# 3. Edit .env.prod with production values
cat > .env.prod << EOF
# API Configuration
LLM_PROVIDER=gemini
LLM_API_KEY=your-production-api-key
LLM_MODEL=gemini-pro
USE_MOCK_LLM=false

# Security
REQUIRE_API_KEY=true
ALLOWED_API_KEYS=key1,key2,key3

# Performance
MAX_RETRY_ATTEMPTS=3
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS (adjust for your domain)
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
EOF

# 4. Build and deploy
docker-compose -f docker-compose.uv.yml --env-file .env.prod up -d

# 5. Check logs
docker-compose logs -f diagram-generator-uv
```

### 2. Docker with Nginx Reverse Proxy

```bash
# Use the production compose file with Nginx
docker-compose -f docker-compose.prod.yml up -d

# This includes:
# - Nginx reverse proxy with rate limiting
# - SSL termination (configure certificates)
# - Health monitoring
# - Log aggregation
```

### 3. Kubernetes Deployment

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: diagram-generator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: diagram-generator
  template:
    metadata:
      labels:
        app: diagram-generator
    spec:
      containers:
      - name: api
        image: diagram-generator:latest
        ports:
        - containerPort: 8000
        env:
        - name: LLM_API_KEY
          valueFrom:
            secretKeyRef:
              name: diagram-generator-secrets
              key: llm-api-key
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 🧪 Testing the Application

### 1. Run Unit Tests

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py unit         # Unit tests only
python run_tests.py integration  # Integration tests only
python run_tests.py coverage     # With coverage report

# Run specific test file
pytest tests/unit/test_tools.py -v

# Run with specific markers
pytest -m "not slow" -v  # Skip slow tests
```

### 2. Manual API Testing

#### Test Health Endpoints
```bash
# Basic health check
curl http://localhost:8000/health

# Readiness check (includes dependency status)
curl http://localhost:8000/health/ready

# Liveness check
curl http://localhost:8000/health/live
```

#### Test Diagram Generation
```bash
# Simple diagram
curl -X POST http://localhost:8000/api/v1/diagram/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a web app with load balancer and database"
  }' \
  --output simple-diagram.png

# Complex microservices architecture
curl -X POST http://localhost:8000/api/v1/diagram/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Design a microservices architecture with API Gateway, three Lambda functions (auth, payment, order), SQS queue for messaging, and shared RDS database. Group the Lambdas in a Microservices cluster."
  }' \
  --output microservices-diagram.png

# Serverless architecture
curl -X POST http://localhost:8000/api/v1/diagram/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Build a serverless data pipeline: S3 bucket triggers Lambda function which processes data and stores results in RDS, with SQS for error handling"
  }' \
  --output serverless-diagram.png
```

#### Test Assistant Mode
```bash
# Initial conversation
curl -X POST http://localhost:8000/api/v1/diagram/assistant \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need help designing a scalable web application",
    "conversation_history": []
  }' | jq .

# Follow-up with context
curl -X POST http://localhost:8000/api/v1/diagram/assistant \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Add a caching layer and message queue",
    "conversation_history": [
      {"role": "user", "content": "I need help designing a scalable web application"},
      {"role": "assistant", "content": "I can help you design a scalable web application. Could you tell me more about your requirements? For example:\n- Expected traffic volume\n- Type of application (e-commerce, social media, etc.)\n- Database requirements\n- Any specific AWS services you want to use?"}
    ]
  }' | jq .
```

#### Test Specification Validation
```bash
# Valid specification
curl -X POST http://localhost:8000/api/v1/diagram/validate \
  -H "Content-Type: application/json" \
  -d '{
    "specification": "{\"nodes\": [{\"type\": \"EC2\", \"name\": \"WebServer\"}, {\"type\": \"RDS\", \"name\": \"Database\"}], \"connections\": [{\"from\": \"WebServer\", \"to\": \"Database\"}], \"clusters\": []}"
  }' | jq .

# Invalid specification (will return suggestions)
curl -X POST http://localhost:8000/api/v1/diagram/validate \
  -H "Content-Type: application/json" \
  -d '{
    "specification": "{\"nodes\": [{\"type\": \"InvalidType\", \"name\": \"Server\"}], \"connections\": []}"
  }' | jq .
```

### 3. Load Testing

```bash
# Install Apache Bench (ab)
# macOS: already installed
# Ubuntu: sudo apt-get install apache2-utils

# Simple load test
ab -n 100 -c 10 -p request.json -T application/json \
  http://localhost:8000/api/v1/diagram/generate

# Create request.json first
echo '{"description": "Simple web app with database"}' > request.json
```

### 4. Using the Python Client Example

```bash
# Run the comprehensive example client
python examples/python_client_example.py

# This will test:
# - Simple diagram generation
# - Complex architectures
# - Assistant conversations
# - Error handling
# - Iterative design
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. "Module 'diagrams' not found"
```bash
# Solution: Install Graphviz system dependency
# macOS
brew install graphviz

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y graphviz

# Verify installation
dot -V  # Should show version
```

#### 2. "LLM API key not found"
```bash
# Solution 1: Use mock mode for testing
echo "USE_MOCK_LLM=true" >> .env

# Solution 2: Add your API key
echo "LLM_API_KEY=your-actual-api-key" >> .env
```

#### 3. "Port 8000 already in use"
```bash
# Find and kill the process
lsof -i :8000  # Find process
kill -9 <PID>  # Kill it

# Or use a different port
uvicorn src.api.main:app --port 8001
```

#### 4. "Cannot import 'python-json-logger'"
```bash
# Reinstall dependencies
uv pip install -e . --force-reinstall
```

#### 5. Docker issues
```bash
# Clean up and rebuild
docker-compose down -v
docker system prune -f
docker-compose build --no-cache
docker-compose up
```

### Viewing Logs

#### Local Development
```bash
# Logs are printed to console
# Set log level in .env
LOG_LEVEL=DEBUG
LOG_FORMAT=text  # or json
```

#### Docker Logs
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f diagram-generator-uv

# Filter by feature tag (requires jq)
docker-compose logs diagram-generator-uv | jq 'select(.tags.feature == "diagram_generation")'

# Filter by time
docker-compose logs --since 5m diagram-generator-uv
```

## 🔧 Advanced Configuration

### Environment Variables

```bash
# Core Settings
API_TITLE="My Diagram Service"
API_VERSION="2.0.0"
ENVIRONMENT=production

# LLM Configuration
LLM_PROVIDER=gemini              # gemini, openai, mock
LLM_API_KEY=your-key-here
LLM_MODEL=gemini-pro            # or gpt-4, gpt-3.5-turbo
LLM_TEMPERATURE=0.7             # 0.0-1.0
LLM_MAX_TOKENS=2000
MAX_RETRY_ATTEMPTS=3

# Security
REQUIRE_API_KEY=true
ALLOWED_API_KEYS=key1,key2,key3
CORS_ORIGINS=https://app1.com,https://app2.com

# Performance
WORKER_COUNT=4                   # For production
TIMEOUT=30                       # Request timeout
CLEANUP_TEMP_FILES=true
TEMP_DIR=/tmp/diagrams

# Logging
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json                 # json or text
ENABLE_ACCESS_LOGS=true

# Feature Flags
ENABLE_ASSISTANT=true
ENABLE_VALIDATION_ENDPOINT=true
MOCK_ERROR_RATE=0.1            # For testing error handling
```

### Performance Tuning

```bash
# For high load production
uvicorn src.api.main:app \
  --workers 4 \
  --loop uvloop \
  --host 0.0.0.0 \
  --port 8000 \
  --limit-concurrency 1000 \
  --timeout-keep-alive 5
```

### Monitoring Setup

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  loki:
    image: grafana/loki
    ports:
      - "3100:3100"
```

## 📊 Monitoring & Observability

### 1. Check Application Metrics
```bash
# Get performance metrics
curl http://localhost:8000/health/ready | jq .

# Sample output:
{
  "status": "ready",
  "timestamp": "2025-01-08T20:00:00Z",
  "checks": {
    "llm_client": {
      "status": "healthy",
      "response_time_ms": 45
    },
    "diagram_builder": {
      "status": "healthy",
      "temp_files": 0
    }
  },
  "metrics": {
    "requests_total": 1523,
    "requests_per_minute": 12.5,
    "average_response_time_ms": 234,
    "error_rate": 0.02
  }
}
```

### 2. Analyze Logs by Feature
```python
# analyze_logs.py
import json
import sys

feature_counts = {}
module_counts = {}
errors = []

for line in sys.stdin:
    try:
        log = json.loads(line)
        if 'tags' in log:
            feature = log['tags'].get('feature', 'unknown')
            module = log['tags'].get('module', 'unknown')
            
            feature_counts[feature] = feature_counts.get(feature, 0) + 1
            module_counts[module] = module_counts.get(module, 0) + 1
            
            if log.get('level') == 'ERROR':
                errors.append(log)
    except:
        pass

print(f"Feature breakdown: {feature_counts}")
print(f"Module breakdown: {module_counts}")
print(f"Total errors: {len(errors)}")
```

Usage:
```bash
docker-compose logs diagram-generator-uv | python analyze_logs.py
```

## 🎉 Success Indicators

Your setup is working correctly when:

1. ✅ Health check returns `{"status": "healthy"}`
2. ✅ You can access API docs at http://localhost:8000/docs
3. ✅ Diagram generation returns a PNG image
4. ✅ Assistant mode provides helpful responses
5. ✅ All tests pass with `python run_tests.py`
6. ✅ No errors in logs: `docker-compose logs | grep ERROR`

## 📚 Next Steps

1. **Explore the API Documentation**: http://localhost:8000/docs
2. **Try Different Architectures**: See examples in README.md
3. **Customize Node Types**: Add support for Azure, GCP components
4. **Integrate with Your App**: Use the Python client example as a starting point
5. **Set Up Monitoring**: Deploy the monitoring stack for production

## 🆘 Getting Help

- **Documentation**: Check the README.md and API docs
- **Logs**: Always check logs first with appropriate filters
- **Issues**: Create an issue on GitHub with:
  - Error message
  - Steps to reproduce
  - Environment details
  - Relevant logs

---

Happy diagramming! 🎨🏗️