#!/bin/bash

# SmartCare Insight System Setup Script
# This script helps with the initial setup and deployment of the system

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print header
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  SmartCare Insight System              ${NC}"
echo -e "${GREEN}  Setup and Deployment Script           ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

# Check if Docker is installed
echo -e "${YELLOW}Checking prerequisites...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites satisfied${NC}"
echo ""

# Check for .env file and create if not exists
echo -e "${YELLOW}Checking environment configuration...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}No .env file found. Creating one...${NC}"
    echo -e "${YELLOW}Please enter your OpenAI API key (required for LLM service):${NC}"
    read -p "API Key: " api_key
    echo "OPENAI_API_KEY=$api_key" > .env
    echo -e "${GREEN}✓ .env file created${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi
echo ""

# Initialize Mosquitto password file if it doesn't exist
echo -e "${YELLOW}Setting up MQTT broker...${NC}"
if [ ! -f docker/mosquitto/password.file ]; then
    echo -e "${YELLOW}Initializing Mosquitto password file...${NC}"
    mkdir -p docker/mosquitto
    echo "healthcare:healthcarepassword" > docker/mosquitto/password.file
    echo -e "${GREEN}✓ Mosquitto password file created${NC}"
else
    echo -e "${GREEN}✓ Mosquitto password file already exists${NC}"
fi

# Create Mosquitto configuration if it doesn't exist
if [ ! -f docker/mosquitto/mosquitto.conf ]; then
    echo -e "${YELLOW}Creating Mosquitto configuration...${NC}"
    cat > docker/mosquitto/mosquitto.conf << EOF
# Mosquitto Configuration File
listener 1883
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
password_file /mosquitto/config/password.file
allow_anonymous false
acl_file /mosquitto/config/acl.file
EOF
    echo -e "${GREEN}✓ Mosquitto configuration created${NC}"
else
    echo -e "${GREEN}✓ Mosquitto configuration already exists${NC}"
fi

# Create Mosquitto ACL file if it doesn't exist
if [ ! -f docker/mosquitto/acl.file ]; then
    echo -e "${YELLOW}Creating Mosquitto ACL file...${NC}"
    cat > docker/mosquitto/acl.file << EOF
# ACL for Mosquitto
user healthcare
topic readwrite #
EOF
    echo -e "${GREEN}✓ Mosquitto ACL file created${NC}"
else
    echo -e "${GREEN}✓ Mosquitto ACL file already exists${NC}"
fi
echo ""

# Build and start the services
echo -e "${YELLOW}Building and starting services...${NC}"
docker-compose build
if [ $? -ne 0 ]; then
    echo -e "${RED}Error building Docker images. Please check the logs above.${NC}"
    exit 1
fi

docker-compose up -d
if [ $? -ne 0 ]; then
    echo -e "${RED}Error starting services. Please check the logs above.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Services started successfully${NC}"
echo ""

# Display service status
echo -e "${YELLOW}Service status:${NC}"
docker-compose ps
echo ""

# Display access information
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  SmartCare Insight System              ${NC}"
echo -e "${GREEN}  is now running!                       ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "Access the dashboard at: ${YELLOW}http://localhost:8501${NC}"
echo -e "Access the API at: ${YELLOW}http://localhost:8001${NC}"
echo ""
echo -e "Default credentials:"
echo -e "  Username: ${YELLOW}admin${NC}"
echo -e "  Password: ${YELLOW}password${NC}"
echo ""
echo -e "${YELLOW}To stop the services:${NC}"
echo -e "  docker-compose down"
echo ""
echo -e "${YELLOW}To view logs:${NC}"
echo -e "  docker-compose logs -f [service_name]"
echo ""
echo -e "${GREEN}Happy monitoring!${NC}"
