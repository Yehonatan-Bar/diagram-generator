# Docker Deployment Guide

This directory contains Docker configuration files for containerizing and deploying the AI Diagram Generator.

## Files Overview

- `Dockerfile` - Multi-stage build for optimized production image (pip-based)
- `Dockerfile.uv` - Multi-stage build using UV package manager (recommended)
- `docker-compose.yml` - Production deployment configuration
- `docker-compose.dev.yml` - Development environment with hot reload
- `docker-compose.uv.yml` - Production deployment with UV-based build
- `.dockerignore` - Files to exclude from Docker build context
- `.env.docker.example` - Example environment configuration
- `nginx/nginx.conf` - Nginx reverse proxy configuration
- `build.sh` - Build script for Docker images
- `deploy.sh` - Deployment script
- `healthcheck.py` - Health check script for container

## Quick Start

### 1. Build the Image

```bash
# Build production image
./docker/build.sh production

# Build development image
./docker/build.sh development
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.docker.example .env

# Edit with your API keys
nano .env
```

### 3. Deploy

```bash
# Deploy production
./docker/deploy.sh production

# Deploy development
./docker/deploy.sh development
```

## Docker Compose Commands

### Production (with pip)

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f diagram-generator

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View status
docker-compose ps
```

### Production (with UV - Recommended)

```bash
# Start services with UV-based build
docker-compose -f docker-compose.uv.yml up -d

# View logs
docker-compose -f docker-compose.uv.yml logs -f diagram-generator-uv

# Stop services
docker-compose -f docker-compose.uv.yml down

# Restart services
docker-compose -f docker-compose.uv.yml restart

# View status
docker-compose -f docker-compose.uv.yml ps
```

### Development

```bash
# Start with hot reload
docker-compose -f docker-compose.dev.yml up

# Run in background
docker-compose -f docker-compose.dev.yml up -d

# Execute commands in container
docker-compose -f docker-compose.dev.yml exec diagram-generator bash
```

## Multi-Stage Build

The Dockerfile uses a multi-stage build for optimization:

1. **Builder Stage**: Installs build dependencies and Python packages
2. **Runtime Stage**: Minimal image with only runtime dependencies

Benefits:
- Smaller final image size (~300MB vs ~800MB)
- Reduced attack surface
- Faster deployment

## Security Features

- Non-root user (`appuser`) for running the application
- Read-only file system where possible
- Health checks for container monitoring
- Environment variable based configuration
- No hardcoded secrets

## Volumes

- `/app/logs` - Application logs (mounted to `./logs`)
- `/app/temp` - Temporary files for diagram generation

## Networking

- Port 8000: FastAPI application
- Port 80: Nginx reverse proxy (optional, production profile)
- Port 443: HTTPS (requires SSL configuration)

## Health Checks

The container includes health checks that:
- Run every 30 seconds
- Timeout after 10 seconds
- Retry 3 times before marking unhealthy
- Check the `/health` endpoint

## Environment Variables

Key environment variables:

- `LLM_PROVIDER` - LLM provider (gemini, openai, mock)
- `GEMINI_API_KEY` - Gemini API key
- `OPENAI_API_KEY` - OpenAI API key
- `USE_MOCK_LLM` - Enable mock mode
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `ENVIRONMENT` - Environment (development, production)
- `CORS_ORIGINS` - Allowed CORS origins

## Nginx Configuration

The optional Nginx reverse proxy provides:
- Rate limiting (10 requests/second per IP)
- Security headers
- Request routing
- SSL termination (when configured)
- Static file serving (future enhancement)

To enable Nginx:
```bash
docker-compose --profile production up -d
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs diagram-generator

# Check health
curl http://localhost:8000/health
```

### Permission issues
```bash
# Fix permissions
sudo chown -R 1000:1000 ./logs ./temp
```

### Build failures
```bash
# Clean build
docker-compose build --no-cache
```

### Memory issues
```bash
# Increase Docker memory limit
# Docker Desktop: Preferences > Resources > Memory
```

## Production Deployment

For production deployment:

1. Use proper SSL certificates
2. Configure domain name in nginx.conf
3. Set restrictive CORS origins
4. Use secrets management for API keys
5. Enable monitoring and logging
6. Set up backup for generated diagrams
7. Configure rate limiting based on load

## Monitoring

Monitor the application using:
- Docker stats: `docker stats diagram-generator`
- Health endpoint: `http://localhost:8000/health/ready`
- Application logs: `docker-compose logs -f`
- Prometheus metrics (future enhancement)