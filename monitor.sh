#!/bin/bash

echo "🔍 Crypto Trading Agents Monitor"

# Function to show agent status
show_agent_status() {
    echo "📊 Agent Status:"
    docker-compose ps
    echo ""
}

# Function to show resource usage
show_resource_usage() {
    echo "💻 Resource Usage:"
    docker stats --no-stream
    echo ""
}

# Function to check health endpoint
check_health() {
    echo "❤️ Health Check:"
    curl -s http://localhost:5000/health | jq .
    echo ""
}

# Main monitoring loop
while true; do
    clear
    show_agent_status
    show_resource_usage
    check_health
    
    echo "🔄 Refreshing in 10 seconds... (Ctrl+C to exit)"
    sleep 10
done 