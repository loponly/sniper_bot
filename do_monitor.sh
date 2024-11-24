#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Load deployment info
if [ ! -f "deployment.info" ]; then
    echo "No deployment information found. Please run deploy.sh first."
    exit 1
fi

source deployment.info

echo -e "${YELLOW}Minimal Resource Monitor${NC}"

# Function to format bytes to human readable
format_bytes() {
    numfmt --to=iec-i --suffix=B "$1"
}

# Function to check resource usage
check_resources() {
    local container=$1
    local stats=$(ssh -o StrictHostKeyChecking=no root@$DROPLET_IP "docker stats --no-stream $container")
    echo "$stats" | tail -n 1
}

while true; do
    clear
    echo "Time: $(date)"
    echo "----------------------------------------"

    # System Resources
    echo -e "${BLUE}System Resources:${NC}"
    ssh -o StrictHostKeyChecking=no root@$DROPLET_IP "free -h && echo && df -h /root/trading-agents/data"
    echo "----------------------------------------"

    # Container Status
    echo -e "${BLUE}Container Status:${NC}"
    ssh -o StrictHostKeyChecking=no root@$DROPLET_IP "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Size}}'"
    echo "----------------------------------------"

    # Resource Usage
    echo -e "${BLUE}Resource Usage:${NC}"
    check_resources trading-agents-strategy_manager-1
    check_resources trading-agents-dashboard-1
    echo "----------------------------------------"

    # Database Size
    echo -e "${BLUE}Database Size:${NC}"
    ssh -o StrictHostKeyChecking=no root@$DROPLET_IP "ls -lh /root/trading-agents/data/trading.db"
    echo "----------------------------------------"

    # Recent Logs (last 5 lines only)
    echo -e "${BLUE}Recent Logs:${NC}"
    ssh -o StrictHostKeyChecking=no root@$DROPLET_IP "tail -n 5 /root/trading-agents/logs/trading.log"
    echo "----------------------------------------"

    echo -e "${YELLOW}Refreshing in 30 seconds... (Ctrl+C to exit)${NC}"
    sleep 30
done 