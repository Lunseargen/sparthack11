#!/bin/bash

# SparthHack11 - Main Runner Script
# This script sets up the environment and runs all necessary Python components

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     SparthHack11 - Project Runner     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}\n"

# Check if Python is installed
echo -e "${YELLOW}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found: $(python3 --version)${NC}\n"

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p frames
mkdir -p uploads
mkdir -p audio
echo -e "${GREEN}✓ Directories created${NC}\n"

# Check if virtual environment exists, if not create one
echo -e "${YELLOW}Checking Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}\n"

# Install requirements
echo -e "${YELLOW}Installing Python dependencies...${NC}"
if [ -f "python/requirements.txt" ]; then
    pip install -q -r python/requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}\n"
else
    echo -e "${RED}✗ requirements.txt not found${NC}"
    exit 1
fi

# Display menu
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}Select what to run:${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo "1) Run Flask Backend Server (main application)"
echo "2) View recorded video frames"
echo "3) Run backend server in background and view frames"
echo "4) Display help and available commands"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo -e "\n${GREEN}Starting Flask Backend Server...${NC}\n"
        python3 python/app.py
        ;;
    2)
        echo -e "\n${GREEN}Starting Video Stream Viewer...${NC}\n"
        echo "Options:"
        echo "  --monitor    Monitor directory for new frames in real-time"
        echo "  --fps <num>  Playback speed in FPS (default: 30)"
        echo ""
        python3 python/frame_viewer_demo.py "$@"
        ;;
    3)
        echo -e "\n${GREEN}Starting Flask Backend Server in background...${NC}"
        python3 python/app.py > /dev/null 2>&1 &
        FLASK_PID=$!
        echo -e "${GREEN}✓ Flask server running (PID: $FLASK_PID)${NC}\n"
        sleep 2
        echo -e "${GREEN}Starting Video Stream Viewer...${NC}\n"
        python3 python/frame_viewer_demo.py "$@"
        ;;
    4)
        echo -e "\n${BLUE}SparthHack11 - Available Commands${NC}\n"
        echo -e "${YELLOW}Running the Flask Backend Server:${NC}"
        echo "  ./run.sh"
        echo "  # Then select option 1\n"
        echo -e "${YELLOW}Viewing recorded frames:${NC}"
        echo "  python3 python/frame_viewer_demo.py"
        echo "  python3 python/frame_viewer_demo.py --monitor"
        echo "  python3 python/frame_viewer_demo.py --fps 15\n"
        echo -e "${YELLOW}To manually activate the virtual environment:${NC}"
        echo "  source venv/bin/activate\n"
        echo -e "${YELLOW}Project Structure:${NC}"
        echo "  frames/              - Captured video frames"
        echo "  uploads/             - Uploaded files"
        echo "  audio/               - Audio files"
        echo "  python/app.py        - Flask backend server"
        echo "  python/frame_viewer_demo.py  - Frame viewer utility"
        echo "  index.html           - Main website"
        echo ""
        ;;
    *)
        echo -e "${RED}Invalid choice. Please select 1-4.${NC}"
        exit 1
        ;;
esac
