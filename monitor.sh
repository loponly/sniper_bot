#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Load configuration
source config.env

# Function to get trading mode and balance
get_trading_info() {
    local mode=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT get trading_mode)
    local balance=""
    if [ "$mode" == "DRY_RUN" ]; then
        balance=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT get simulated_balance)
        echo -e "Mode: ${RED}DRY RUN${NC}"
        echo -e "Simulated Balance: ${GREEN}$balance USDT${NC}"
    else
        echo -e "Mode: ${GREEN}LIVE TRADING${NC}"
    fi
}

# Function to get backtest results
get_backtest_results() {
    local results=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT --raw keys "backtest_results:*" | tail -n 5)
    for key in $results; do
        echo "Result: $key"
        redis-cli -h $REDIS_HOST -p $REDIS_PORT hgetall "$key"
    done
}

while true; do
    clear
    echo -e "${YELLOW}Trading Agents Monitor${NC}"
    echo "----------------------------------------"
    
    # Show trading mode and balance
    get_trading_info
    echo "----------------------------------------"
    
    # Show agent status
    echo -e "${BLUE}Agent Status:${NC}"
    docker-compose ps
    echo "----------------------------------------"
    
    # Show resource usage
    echo -e "${BLUE}Resource Usage:${NC}"
    docker stats --no-stream
    echo "----------------------------------------"
    
    # Show recent backtest results
    echo -e "${BLUE}Recent Backtest Results:${NC}"
    get_backtest_results
    echo "----------------------------------------"
    
    # Show logs
    echo -e "${BLUE}Recent Logs:${NC}"
    docker-compose logs --tail=5
    echo "----------------------------------------"
    
    echo -e "${YELLOW}Refreshing in 30 seconds... (Ctrl+C to exit)${NC}"
    sleep 30
done 