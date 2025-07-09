#!/bin/bash
# Deployment script for AI Diagram Generator

set -e

echo "🚀 Deploying AI Diagram Generator..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Creating from .env.docker.example..."
    cp .env.docker.example .env
    echo "   Please edit .env with your API keys before continuing."
    exit 1
fi

# Parse arguments
ENVIRONMENT=${1:-production}

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose pull

# Start services based on environment
if [ "$ENVIRONMENT" = "development" ]; then
    echo "🔧 Starting development environment..."
    docker-compose -f docker-compose.dev.yml up -d
    echo "✅ Development environment started!"
    echo "   API: http://localhost:8000"
    echo "   Docs: http://localhost:8000/docs"
else
    echo "🏭 Starting production environment..."
    docker-compose up -d
    echo "✅ Production environment started!"
    echo "   API: http://localhost:8000"
    echo "   Nginx (optional): http://localhost:80"
fi

# Show container status
echo ""
echo "📊 Container Status:"
docker-compose ps

# Show logs command
echo ""
echo "📋 To view logs:"
echo "   docker-compose logs -f diagram-generator"