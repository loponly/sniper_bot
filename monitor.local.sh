#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}Local Trading Agents Monitor${NC}"

# Function to check container status
check_container_status() {
    local container=$1
    local status=$(docker inspect --format='{{.State.Status}}' $container 2>/dev/null)
    if [ "$status" == "running" ]; then
        echo -e "${GREEN}running${NC}"
    else
        echo -e "${RED}$status${NC}"
    fi
}

# Function to get database stats
get_db_stats() {
    echo "Active Strategies:"
    sqlite3 data/trading.db "SELECT COUNT(*) as count, status FROM strategies GROUP BY status;"
    echo
    echo "Recent Executions:"
    sqlite3 data/trading.db "SELECT * FROM code_executions ORDER BY created_at DESC LIMIT 5;"
}

while true; do
    clear
    echo "Time: $(date)"
    echo "----------------------------------------"

    # Container Status
    echo -e "${BLUE}Container Status:${NC}"
    docker-compose ps
    echo "----------------------------------------"

    # Resource Usage
    echo -e "${BLUE}Resource Usage:${NC}"
    docker stats --no-stream
    echo "----------------------------------------"

    # Database Stats
    echo -e "${BLUE}Database Stats:${NC}"
    get_db_stats
    echo "----------------------------------------"

    # Recent Logs
    echo -e "${BLUE}Recent Logs:${NC}"
    tail -n 10 logs/trading.log
    echo "----------------------------------------"

    echo -e "${YELLOW}Refreshing in 10 seconds... (Ctrl+C to exit)${NC}"
    sleep 10
done 