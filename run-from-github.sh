#!/bin/bash

# 🐳 RAG Agent - GitHub Container Registry Runner
# This script pulls and runs the RAG Agent from GitHub Container Registry

set -e

echo "🐳 RAG Agent - GitHub Container Registry"
echo "========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="ghcr.io/michaelyuwh/rag-agent:latest"
CONTAINER_NAME="rag-agent"
PORT="8501"

echo -e "${BLUE}📦 Pulling latest RAG Agent image...${NC}"
if docker pull $IMAGE_NAME; then
    echo -e "${GREEN}✅ Image pulled successfully!${NC}"
else
    echo -e "${RED}❌ Failed to pull image. Make sure you're authenticated with GitHub Container Registry.${NC}"
    echo ""
    echo "To authenticate:"
    echo "  gh auth token | docker login ghcr.io -u $(gh api user --jq .login) --password-stdin"
    exit 1
fi

echo ""
echo -e "${BLUE}🚀 Starting RAG Agent container...${NC}"

# Stop existing container if running
if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
    echo "🛑 Stopping existing container..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

# Run the container
docker run -d \
    --name $CONTAINER_NAME \
    -p $PORT:8501 \
    -v "$(pwd)/data:/app/data" \
    --restart unless-stopped \
    $IMAGE_NAME

echo ""
echo -e "${GREEN}✅ RAG Agent is now running!${NC}"
echo ""
echo "🌐 Access your RAG Agent at:"
echo -e "   ${BLUE}http://localhost:$PORT${NC}"
echo ""
echo "📋 Container Management:"
echo "   docker logs $CONTAINER_NAME     # View logs"
echo "   docker stop $CONTAINER_NAME     # Stop container" 
echo "   docker start $CONTAINER_NAME    # Start container"
echo ""
echo "🔄 To update to latest version:"
echo "   docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME"
echo "   ./run-from-github.sh"
