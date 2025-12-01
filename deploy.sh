#!/bin/bash

# HR Tracker Bot - VPS Deployment Script

set -e

echo "🚀 Starting HR Tracker Bot deployment..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
APP_DIR="/home/ubuntu/HR-tracker"
SERVICE_NAME="hr-tracker-bot"
USER="ubuntu"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root (use sudo)${NC}"
    exit 1
fi

# 1. Update system packages
echo -e  "${YELLOW}📦 Updating system packages...${NC}"
apt-get update
apt-get install -y python3 python3-pip python3-venv git

# 2. Create app directory if doesn't exist
if [ ! -d "$APP_DIR" ]; then
    echo -e "${YELLOW}📂 Cloning repository...${NC}"
    git clone https://github.com/Lakodros-dev/HR-tracker.git $APP_DIR
    chown -R $USER:$USER $APP_DIR
fi

cd $APP_DIR

# 3. Pull latest changes
echo -e "${YELLOW}🔄 Pulling latest changes...${NC}"
sudo -u $USER git pull

# 4. Setup virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🐍 Creating virtual environment...${NC}"
    sudo -u $USER python3 -m venv venv
fi

# 5. Install dependencies
echo -e "${YELLOW}📥 Installing dependencies...${NC}"
sudo -u $USER ./venv/bin/pip install --upgrade pip
sudo -u $USER ./venv/bin/pip install -r requirements.txt

# 6. Check .env file
if [ ! -f "$APP_DIR/.env" ]; then
    echo -e "${YELLOW}⚙️  Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${RED}⚠️  WARNING: Please edit .env file and add your credentials!${NC}"
    echo -e "${YELLOW}Run: nano $APP_DIR/.env${NC}"
fi

# 7. Setup systemd service
echo -e "${YELLOW}🔧 Setting up systemd service...${NC}"
cp hr-tracker-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable $SERVICE_NAME

# 8. Create log files
touch /var/log/hr-tracker-bot.log
touch /var/log/hr-tracker-bot-error.log
chown $USER:$USER /var/log/hr-tracker-bot.log
chown $USER:$USER /var/log/hr-tracker-bot-error.log

# 9. Start/Restart service
echo -e "${YELLOW}▶️  Starting bot service...${NC}"
systemctl restart $SERVICE_NAME

# 10. Show status
sleep 2
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
systemctl status $SERVICE_NAME --no-pager

echo ""
echo -e "${GREEN}📝 Useful commands:${NC}"
echo "  Check status:  sudo systemctl status $SERVICE_NAME"
echo "  View logs:     sudo journalctl -u $SERVICE_NAME -f"
echo "  Restart:       sudo systemctl restart $SERVICE_NAME"
echo "  Stop:          sudo systemctl stop $SERVICE_NAME"
echo ""
echo -e "${YELLOW}⚠️  Don't forget to configure .env file if you haven't already!${NC}"
