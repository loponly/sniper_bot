#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Local Development Deployment (Minimal Setup)${NC}"

# Configuration
CONFIG_FILE="config.local.env"

# Check if config exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating local configuration..."
    
    cat > "$CONFIG_FILE" << EOF
# Agent Configuration
AGENT_TYPE=strategy_manager
TRADING_MODE=DRY_RUN
INITIAL_BALANCE=10000
LOG_LEVEL=DEBUG

# Resource Configuration
MEMORY_LIMIT=256m
CPU_LIMIT=0.2

# Database Configuration
DB_PATH=/app/data/trading.db
EOF

    echo "Local configuration saved to $CONFIG_FILE"
fi

# Create necessary directories
mkdir -p data logs

# Start services with minimal resources
echo -e "${GREEN}Starting local services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

# Initialize database
echo -e "${GREEN}Initializing database...${NC}"
sqlite3 data/trading.db ".databases"

echo -e "
${GREEN}Local Deployment Complete!${NC}

📊 Access your services:
   - Dashboard: http://localhost:5000
   - API: http://localhost:8080

💾 Database:
   - SQLite: ./data/trading.db

📝 Logs: ./logs directory

🔍 Monitor:
   ./monitor.local.sh

❌ Cleanup:
   docker-compose down
" 