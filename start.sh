#!/usr/bin/env bash

# Exit on error
set -e

# Define colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}       LLM Rerouter Initialization      ${NC}"
echo -e "${BLUE}========================================${NC}"

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python 3 is not installed. Please install Python 3 to continue.${NC}"
    exit 1
fi

# 2. Check/Create Virtual Environment
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating Python virtual environment...${NC}"
    python3 -m venv venv
else
    echo -e "${GREEN}Virtual environment found.${NC}"
fi

# 3. Activate Virtual Environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# 4. Install Dependencies
echo -e "${GREEN}Checking and installing dependencies...${NC}"
cd llm-router
# Upgrade pip to prevent older pip issues
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
cd ..

# 5. Launch the Python TUI
echo -e "${GREEN}Launching LLM Rerouter Setup Wizard...${NC}"
python3 start_router.py

# Deactivate venv upon exit
deactivate
