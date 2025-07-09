#!/bin/bash
# Build script for AI Diagram Generator

set -e

echo "🔨 Building AI Diagram Generator Docker image..."

# Parse arguments
ENVIRONMENT=${1:-production}
VERSION=${2:-latest}

# Build based on environment
if [ "$ENVIRONMENT" = "development" ]; then
    echo "📦 Building development image..."
    docker build -t ai-diagram-generator:dev \
                 -t ai-diagram-generator:dev-${VERSION} \
                 --target builder \
                 -f Dockerfile .
    echo "✅ Development image built successfully!"
else
    echo "📦 Building production image..."
    docker build -t ai-diagram-generator:latest \
                 -t ai-diagram-generator:${VERSION} \
                 -f Dockerfile .
    echo "✅ Production image built successfully!"
fi

# Show image info
echo ""
echo "📊 Image Information:"
docker images | grep ai-diagram-generator | head -3

echo ""
echo "🚀 To run the container:"
if [ "$ENVIRONMENT" = "development" ]; then
    echo "   docker-compose -f docker-compose.dev.yml up"
else
    echo "   docker-compose up -d"
fi