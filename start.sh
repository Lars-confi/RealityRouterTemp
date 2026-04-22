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

# Define App Home
export LLM_REROUTER_HOME="${LLM_REROUTER_HOME:-$HOME/.llm_rerouter}"
mkdir -p "$LLM_REROUTER_HOME"
mkdir -p "$LLM_REROUTER_HOME/config"
mkdir -p "$LLM_REROUTER_HOME/logs"

# Optional: Migrate existing files if they exist in the current directory and not in LLM_REROUTER_HOME
for file in .env disabled_models.json user_models.json llm_router.db; do
    if [ -f "$file" ]; then
        if [ ! -f "$LLM_REROUTER_HOME/$file" ]; then
            echo -e "${YELLOW}Migrating $file to $LLM_REROUTER_HOME...${NC}"
            cp "$file" "$LLM_REROUTER_HOME/"
        fi
        rm "$file"
    fi
done

if [ -d "llm-router/config" ]; then
    for file in llm-router/config/*.json; do
        if [ -f "$file" ]; then
            if [ ! -f "$LLM_REROUTER_HOME/config/$(basename "$file")" ]; then
                echo -e "${YELLOW}Migrating $(basename "$file") to $LLM_REROUTER_HOME/config...${NC}"
                cp "$file" "$LLM_REROUTER_HOME/config/"
            fi
        fi
    done
    rm -rf "llm-router/config"
fi

if [ -d "logs" ]; then
    for file in logs/*.log; do
        if [ -f "$file" ]; then
            if [ ! -f "$LLM_REROUTER_HOME/logs/$(basename "$file")" ]; then
                cp "$file" "$LLM_REROUTER_HOME/logs/"
            fi
            rm "$file"
        fi
    done
    rmdir logs 2>/dev/null || true
fi

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
if [ -f "venv/bin/activate" ]; then
    # Mac/Linux
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    # Windows (Git Bash/MSYS2/WSL)
    source venv/Scripts/activate
else
    echo -e "${YELLOW}Warning: Could not find virtual environment activation script.${NC}"
fi

# 4. Install Dependencies
echo -e "${GREEN}Checking and installing dependencies...${NC}"
cd llm-router
# Upgrade pip to prevent older pip issues
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
cd ..

# 5. Launch the Python TUI
echo -e "${GREEN}Launching LLM Rerouter Setup Wizard...${NC}"
export LOG_DIR="$LLM_REROUTER_HOME/logs"
python3 start_router.py

# Deactivate venv upon exit
deactivate
