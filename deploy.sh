#!/bin/bash

# WorldWideCoin Docker Deployment Script

set -e

echo "🚀 Starting WorldWideCoin Docker Deployment"

# Create necessary directories
echo "📁 Creating data and config directories..."
mkdir -p data/{node1,node2,node3,miner}
mkdir -p config/{node1,node2,node3,miner}

# Build and start the services
echo "🐳 Building Docker images..."
docker-compose build

echo "🌐 Starting WorldWideCoin network..."
docker-compose up -d node1 api1 node2 api2 node3 api3

echo "⏳ Waiting for nodes to initialize..."
sleep 10

echo "✅ WorldWideCoin network is running!"
echo ""
echo "📊 Access points:"
echo "  Node 1 API: http://localhost:8001"
echo "  Node 2 API: http://localhost:8002"
echo "  Node 3 API: http://localhost:8003"
echo ""
echo "🔗 P2P Ports:"
echo "  Node 1: localhost:5001"
echo "  Node 2: localhost:5002"
echo "  Node 3: localhost:5003"
echo ""
echo "💡 To start mining: docker-compose --profile miner up -d miner"
echo "💡 To view logs: docker-compose logs -f [service_name]"
echo "💡 To stop: docker-compose down"