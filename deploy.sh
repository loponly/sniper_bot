#!/bin/bash

echo "🚀 Deploying Crypto Trading Multi-Agent System..."

# Check Docker and Docker Compose
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker and Docker Compose are required but not installed."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/models logs

# Pull latest images
echo "🔄 Pulling latest images..."
docker-compose pull

# Build and start services
echo "🏗️ Building and starting services..."
docker-compose up -d --build

# Wait for services to be healthy
echo "🔍 Checking service health..."
sleep 10

# Check service status
echo "📊 Service Status:"
docker-compose ps

# Show dashboard access
echo "
🌐 Dashboard available at: http://localhost:5000

📝 Monitor logs with:
   docker-compose logs -f

🔍 Monitor specific agent:
   docker-compose logs -f strategy_finder
   docker-compose logs -f market_analyzer
   docker-compose logs -f strategy_executor

❤️ Health check:
   curl http://localhost:5000/health
" 