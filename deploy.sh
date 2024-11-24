#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}DigitalOcean Basic Deployment (Cheapest Option)${NC}"

# Configuration
CONFIG_FILE="config.env"

# Check for jq
if ! command -v jq &> /dev/null; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install jq
    else
        sudo apt-get update && sudo apt-get install -y jq
    fi
fi

# First time setup
if [ ! -f "$CONFIG_FILE" ]; then
    echo "First time setup..."
    
    # Get API Token
    echo "Create your API token at: https://cloud.digitalocean.com/account/api/tokens"
    read -sp "Enter your DigitalOcean API Token: " do_token
    echo

    # Create config.env file
    cat > "$CONFIG_FILE" << EOF
# DigitalOcean Configuration
DO_API_TOKEN=$do_token

# Agent Configuration
AGENT_TYPE=strategy_manager
TRADING_MODE=DRY_RUN
INITIAL_BALANCE=10000
LOG_LEVEL=INFO

# Resource Configuration
MEMORY_LIMIT=512m
CPU_LIMIT=0.5
EOF

    echo "Configuration saved to $CONFIG_FILE"
fi

# Load configuration
source "$CONFIG_FILE"

# Verify API token
echo -e "${GREEN}Verifying API token...${NC}"
account_response=$(curl -s \
    -H "Authorization: Bearer $DO_API_TOKEN" \
    "https://api.digitalocean.com/v2/account")

if [ -z "$account_response" ]; then
    echo -e "${RED}Failed to get response from DigitalOcean API${NC}"
    exit 1
fi

account_status=$(echo $account_response | jq -r '.account.status' 2>/dev/null)
if [ "$account_status" != "active" ]; then
    echo -e "${RED}Invalid API token or account not active${NC}"
    echo "API Response: $account_response"
    exit 1
fi

# Create Droplet with basic resources
echo -e "${GREEN}Creating Basic Droplet...${NC}"
create_response=$(curl -s -X POST \
    -H "Authorization: Bearer $DO_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "trading-agents-basic",
        "region": "sgp1",
        "size": "s-1vcpu-1gb",
        "image": "docker-20-04",
        "monitoring": true,
        "tags": ["trading-agents"],
        "user_data": "#cloud-config\npackage_update: true\npackages:\n- docker.io\n- docker-compose\n- sqlite3"
    }' \
    "https://api.digitalocean.com/v2/droplets")

DROPLET_ID=$(echo $create_response | jq -r '.droplet.id')

# Wait for droplet to be active
echo "Waiting for droplet to be ready..."
while true; do
    status=$(curl -s \
        -H "Authorization: Bearer $DO_API_TOKEN" \
        "https://api.digitalocean.com/v2/droplets/$DROPLET_ID" \
        | jq -r '.droplet.status')
    
    if [ "$status" == "active" ]; then
        break
    fi
    echo -n "."
    sleep 5
done

# Get droplet IP
DROPLET_IP=$(curl -s \
    -H "Authorization: Bearer $DO_API_TOKEN" \
    "https://api.digitalocean.com/v2/droplets/$DROPLET_ID" \
    | jq -r '.droplet.networks.v4[0].ip_address')

echo -e "\nDroplet IP: $DROPLET_IP"

# Save deployment info
cat > "deployment.info" << EOF
DROPLET_ID=$DROPLET_ID
DROPLET_IP=$DROPLET_IP
EOF

# Copy files to droplet
echo -e "${GREEN}Copying files to droplet...${NC}"
scp -o StrictHostKeyChecking=no -r \
    src \
    scripts \
    config.env \
    docker-compose.yml \
    Dockerfile \
    Dockerfile.dashboard \
    requirements.txt \
    requirements.dashboard.txt \
    root@$DROPLET_IP:/root/trading-agents/

# Initialize and start services
echo -e "${GREEN}Initializing services...${NC}"
ssh -o StrictHostKeyChecking=no root@$DROPLET_IP << EOF
    cd /root/trading-agents
    mkdir -p data logs
    docker-compose pull
    docker-compose up -d
EOF

echo -e "
${GREEN}Deployment Complete!${NC}

📊 Access your services:
   - Dashboard: http://$DROPLET_IP:5000
   - API: http://$DROPLET_IP:8080

💾 Database:
   - SQLite: /root/trading-agents/data/trading.db

📝 Logs:
   - Directory: /root/trading-agents/logs

🔍 Monitor:
   ./do_monitor.sh

❌ Cleanup:
   curl -X DELETE -H \"Authorization: Bearer \$DO_API_TOKEN\" \"https://api.digitalocean.com/v2/droplets/$DROPLET_ID\"
" 