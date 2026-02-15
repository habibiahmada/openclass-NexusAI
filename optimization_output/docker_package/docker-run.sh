#!/bin/bash
# Docker run script for OpenClass Nexus AI

echo "Starting OpenClass Nexus AI..."

# Create necessary directories
mkdir -p data models config logs

# Run with Docker Compose
docker-compose up -d

echo "OpenClass Nexus AI started successfully!"
echo "Access at: http://localhost:8000"
echo "View logs: docker-compose logs -f"
echo "Stop with: docker-compose down"
