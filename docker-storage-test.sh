#!/bin/bash

# Docker Storage Test Script
echo "🐳 Running Grade Storage Test in Docker Environment"
echo "=================================================="

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t grade-phoenix-bot .

# Run the storage test in a temporary container
echo "🧪 Running storage test..."
docker run --rm \
  -e DATABASE_URL=sqlite:///./data/bot.db \
  -e BOT_VERSION=v2.1.0 \
  -v $(pwd)/data:/app/data \
  grade-phoenix-bot \
  python test_storage_docker.py

echo "✅ Test completed!"