#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# DigitalOcean configuration
DO_CONFIG="do.config"

echo -e "${YELLOW}DigitalOcean Deployment Setup${NC}"

# Check for doctl installation
if ! command -v doctl &> /dev/null; then
    echo "Installing doctl..."
    # For Linux
    snap install doctl
    # Authenticate doctl
    echo "Please authenticate with DigitalOcean:"
    doctl auth init
fi

# Get or create configuration
if [ ! -f "$DO_CONFIG" ]; then
    echo "First time setup..."
    
    # Get DigitalOcean configuration
    read -p "Enter Droplet name (default: trading-agents): " droplet_name
    droplet_name=${droplet_name:-trading-agents}
    
    read -p "Enter region (default: nyc1): " region
    region=${region:-nyc1}
    
    read -p "Enter size (default: s-2vcpu-4gb): " size
    size=${size:-s-2vcpu-4gb}
    
    # Save configuration
    cat > "$DO_CONFIG" << EOF
DROPLET_NAME="$droplet_name"
REGION="$region"
SIZE="$size"
EOF
fi

# Load configuration
source "$DO_CONFIG"

# Create Droplet
echo -e "${GREEN}Creating DigitalOcean Droplet...${NC}"
droplet_id=$(doctl compute droplet create \
    --image docker-20-04 \
    --size $SIZE \
    --region $REGION \
    --wait \
    $DROPLET_NAME \
    --format ID \
    --no-header)

# Wait for Droplet to be ready
echo "Waiting for Droplet to be ready..."
sleep 60

# Get Droplet IP
droplet_ip=$(doctl compute droplet get $droplet_id --format PublicIPv4 --no-header)

# Setup Docker and dependencies
echo -e "${GREEN}Setting up Docker and dependencies...${NC}"
ssh -o StrictHostKeyChecking=no root@$droplet_ip << 'EOF'
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh

    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    # Create directories
    mkdir -p /root/trading-agents/data
    mkdir -p /root/trading-agents/logs
EOF

# Copy files to Droplet
echo -e "${GREEN}Copying configuration files...${NC}"
scp -o StrictHostKeyChecking=no docker-compose.yml root@$droplet_ip:/root/trading-agents/
scp -o StrictHostKeyChecking=no .env root@$droplet_ip:/root/trading-agents/

# Start services
echo -e "${GREEN}Starting services...${NC}"
ssh -o StrictHostKeyChecking=no root@$droplet_ip << 'EOF'
    cd /root/trading-agents
    docker-compose pull
    docker-compose up -d
EOF

echo -e "
${GREEN}Deployment Complete!${NC}

📊 Access your agents:
   - Dashboard: http://$droplet_ip:5000
   - API: http://$droplet_ip:8080

💻 SSH Access:
   ssh root@$droplet_ip

📝 View Logs:
   ssh root@$droplet_ip 'cd trading-agents && docker-compose logs -f'

🔄 Update Services:
   ./deploy.sh --update

❌ Cleanup:
   doctl compute droplet delete $droplet_id
"

# Save deployment info
cat > "deployment.info" << EOF
DROPLET_ID=$droplet_id
DROPLET_IP=$droplet_ip
EOF 