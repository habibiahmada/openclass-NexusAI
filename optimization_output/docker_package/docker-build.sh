#!/bin/bash
# Docker build script for OpenClass Nexus AI

echo "Building OpenClass Nexus AI Docker image..."

# Build the image
docker build -t openclass-nexus-ai:latest .

# Tag for different environments
docker tag openclass-nexus-ai:latest openclass-nexus-ai:production
docker tag openclass-nexus-ai:latest openclass-nexus-ai:$(date +%Y%m%d)

echo "Docker image built successfully!"
echo "Run with: ./docker-run.sh"
