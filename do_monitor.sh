#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load deployment info
if [ ! -f "deployment.info" ]; then
    echo "No deployment information found. Please run deploy.sh first."
    exit 1
fi

source deployment.info

# Monitor function
monitor_droplet() {
    echo -e "${YELLOW}DigitalOcean Droplet Monitor${NC}"
    
    while true; do
        clear
        
        # Get Droplet status
        echo -e "${GREEN}Droplet Status:${NC}"
        doctl compute droplet get $DROPLET_ID --format Name,PublicIPv4,Status,Memory,Disk
        echo
        
        # Get container status
        echo -e "${GREEN}Container Status:${NC}"
        ssh -o StrictHostKeyChecking=no root@$DROPLET_IP 'cd trading-agents && docker-compose ps'
        echo
        
        # Get resource usage
        echo -e "${GREEN}Resource Usage:${NC}"
        ssh -o StrictHostKeyChecking=no root@$DROPLET_IP 'cd trading-agents && docker stats --no-stream'
        echo
        
        # Get recent logs
        echo -e "${GREEN}Recent Logs:${NC}"
        ssh -o StrictHostKeyChecking=no root@$DROPLET_IP 'cd trading-agents && docker-compose logs --tail=10'
        echo
        
        echo -e "${YELLOW}Refreshing in 30 seconds... (Ctrl+C to exit)${NC}"
        sleep 30
    done
}

# Start monitoring
monitor_droplet 