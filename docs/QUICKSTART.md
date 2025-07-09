# Quick Start Guide

Get up and running with the AI Diagram Generator in 5 minutes!

## 🚀 Fastest Way to Start

### Option 1: Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/diagram-generator.git
cd diagram-generator

# Copy environment file
cp .env.docker.example .env

# Edit .env and add your API key (or use mock mode)
# For testing without API keys, set USE_MOCK_LLM=true

# Run with Docker Compose (UV-based build)
docker-compose -f docker-compose.uv.yml up -d

# Check if it's running
curl http://localhost:8000/health
```

### Option 2: Local Development with UV (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/diagram-generator.git
cd diagram-generator

# Install UV
pip install uv
# Or: curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Install Graphviz
# macOS: brew install graphviz
# Ubuntu: sudo apt-get install graphviz

# Copy environment file
cp .env.example .env

# For testing without API keys, edit .env:
# USE_MOCK_LLM=true

# Run the server
python run.py
```

### Option 3: Local Development with pip

```bash
# Clone the repository
git clone https://github.com/yourusername/diagram-generator.git
cd diagram-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Graphviz
# macOS: brew install graphviz
# Ubuntu: sudo apt-get install graphviz

# Copy environment file
cp .env.example .env

# For testing without API keys, edit .env:
# USE_MOCK_LLM=true

# Run the server
python run.py
```

## 🎯 Your First Diagram

### Using curl

```bash
curl -X POST "http://localhost:8000/api/v1/diagram/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a simple web app with load balancer and database"
  }'
```

### Using Python

```python
import httpx
import asyncio
import base64

async def generate_diagram():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/diagram/generate",
            json={
                "description": "Create a simple web app with load balancer and database"
            }
        )
        
        result = response.json()
        if result["success"]:
            # Save the diagram
            image_data = base64.b64decode(result["diagram_data"])
            with open("my_diagram.png", "wb") as f:
                f.write(image_data)
            print("Diagram saved as my_diagram.png!")

asyncio.run(generate_diagram())
```

### Using the Interactive Docs

Open http://localhost:8000/docs in your browser for the interactive API documentation.

## 🧪 Testing Without API Keys

Set `USE_MOCK_LLM=true` in your `.env` file to use mock mode:

```bash
# .env
USE_MOCK_LLM=true
LOG_LEVEL=DEBUG
```

This allows you to test the system without any API keys.

## 📚 Common Use Cases

### 1. Simple Web Application

```json
{
  "description": "Create a web app with 2 servers behind a load balancer connected to a database"
}
```

### 2. Serverless Architecture

```json
{
  "description": "Build a serverless system: S3 bucket triggers Lambda function that writes to DynamoDB"
}
```

### 3. Microservices

```json
{
  "description": "Design microservices: API Gateway, 3 services (order, payment, notification), each with own database, connected via SQS"
}
```

## 🔍 Debugging Tips

1. **Check Health Status**:
   ```bash
   curl http://localhost:8000/health/ready
   ```

2. **View Logs**:
   ```bash
   # Docker
   docker-compose logs -f diagram-generator
   
   # Local
   # Logs are printed to console
   ```

3. **Test with Mock Mode**:
   Set `USE_MOCK_LLM=true` to test without API keys

4. **Check API Documentation**:
   Visit http://localhost:8000/docs

## 🆘 Getting Help

- Check the [full documentation](../README.md)
- Look at [example scripts](../examples/)
- Review [troubleshooting guide](../README.md#-troubleshooting)
- Open an issue on GitHub

## 🎉 Next Steps

1. Try the [Python client examples](../examples/python_client_example.py)
2. Explore the [assistant mode](../README.md#using-the-assistant-for-complex-architectures)
3. Read about [adding new components](../README.md#adding-new-cloud-components)
4. Learn about the [architecture](../README.md#-architecture-overview)