#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}Trading Agent Monitor${NC}"

# Function to check agent health
check_agent_health() {
    local agent=$1
    local status=$(curl -s http://localhost:8080/health | jq -r ".$agent")
    if [ "$status" == "healthy" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
}

# Function to get agent metrics
get_agent_metrics() {
    local agent=$1
    local metrics=$(curl -s http://localhost:8080/metrics/$agent)
    echo "$metrics" | jq '.'
}

while true; do
    clear
    
    # Agent Status
    echo -e "${BLUE}Agent Status:${NC}"
    echo -e "Strategy Manager: $(check_agent_health strategy_manager)"
    echo -e "Strategy Optimizer: $(check_agent_health strategy_optimizer)"
    echo -e "Code Executor: $(check_agent_health code_executor)"
    echo -e "Redis: $(check_agent_health redis)"
    echo
    
    # Container Status
    echo -e "${BLUE}Container Status:${NC}"
    docker-compose ps
    echo
    
    # Resource Usage
    echo -e "${BLUE}Resource Usage:${NC}"
    docker stats --no-stream
    echo
    
    # Agent Metrics
    echo -e "${BLUE}Agent Metrics:${NC}"
    echo -e "${YELLOW}Strategy Manager:${NC}"
    get_agent_metrics strategy_manager
    echo -e "${YELLOW}Strategy Optimizer:${NC}"
    get_agent_metrics strategy_optimizer
    echo -e "${YELLOW}Code Executor:${NC}"
    get_agent_metrics code_executor
    echo
    
    # Latest Logs
    echo -e "${BLUE}Recent Logs:${NC}"
    tail -n 10 ./logs/trading_agent.log
    echo
    
    echo -e "${YELLOW}🔄 Refreshing in 30 seconds... (Ctrl+C to exit)${NC}"
    sleep 30
done 