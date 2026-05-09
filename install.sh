#!/bin/bash
set -e
#
# This script automates the installation of the reality-router project.
# It can be run directly from a URL via curl:
# curl -fsSL https://your-url-to-this-script/install.sh | bash
#

# --- Helper Functions ---
# Checks if a command exists.
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# --- Configuration ---
# IMPORTANT: Replace this with the actual raw content URL of your repository.
# For GitHub, it would look like: https://raw.githubusercontent.com/user/repo/main
REPO_URL="http://spark-a0d3.tailcd6737.ts.net:3000/lc/RealityRouter"
TARGET_DIR="$HOME/.reality-router"


# --- Pre-flight Checks ---
echo "Starting reality-router installation..."

# Check for required dependencies
echo "Checking for required dependencies (git, python3, curl)..."
for cmd in git python3 curl; do
    if ! command_exists "$cmd"; then
        echo "Error: Required command '$cmd' is not installed." >&2
        echo "Please install it and try again." >&2
        exit 1
    fi
done
echo "All dependencies are satisfied."


# --- Installation ---
if [ -d "$TARGET_DIR" ]; then
    echo "Found an existing installation in $TARGET_DIR."
    echo "Pulling latest changes from the repository..."
    cd "$TARGET_DIR"
    git pull
else
    echo "Cloning repository to $TARGET_DIR..."
    git clone "$REPO_URL" "$TARGET_DIR"
    cd "$TARGET_DIR"
fi

# --- Virtual Environment Setup ---
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Re-using it."
else
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
# shellcheck source=/dev/null
source venv/bin/activate

echo "Installing project dependencies from requirements.txt..."
# Assuming the requirements file is inside the reality-router sub-directory
pip install -r "reality-router/requirements.txt"

echo "Installation of dependencies complete."

# Deactivate the virtual environment for now. The alias will handle activation.
deactivate

# --- Alias Setup ---
SHELL_PROFILE=""
detected_shell=$(basename "$SHELL")

if [ "$detected_shell" = "bash" ]; then
    SHELL_PROFILE="$HOME/.bashrc"
elif [ "$detected_shell" = "zsh" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
else
    echo "Warning: Unsupported shell '$detected_shell'. Could not configure an alias."
    echo "You can run the application manually from the installation directory:"
    echo "  cd $TARGET_DIR && source venv/bin/activate && python3 start_router.py"
fi

if [ -n "$SHELL_PROFILE" ]; then
    ALIAS_CMD="alias reality-router='source $TARGET_DIR/venv/bin/activate && python3 $TARGET_DIR/start_router.py'"
    
    echo "Attempting to add 'reality-router' alias to your shell profile ($SHELL_PROFILE)..."
    
    # Remove any existing reality-router alias to prevent duplicates
    if grep -q "alias reality-router=" "$SHELL_PROFILE" 2>/dev/null; then
        echo "Removing existing reality-router alias..."
        sed -i.bak "/alias reality-router=/d" "$SHELL_PROFILE"
    fi
    
    # Add the new alias
    echo "Adding new alias..."
    echo "" >> "$SHELL_PROFILE"
    echo "# reality-router alias" >> "$SHELL_PROFILE"
    echo "$ALIAS_CMD" >> "$SHELL_PROFILE"
    
    echo "Alias added to $SHELL_PROFILE."
    echo "Please run 'source $SHELL_PROFILE' or restart your terminal to use the 'reality-router' command."
fi


# --- Completion ---
echo ""
echo "--------------------------------------------------------"
echo "✅ reality-router installation is complete!"
echo "--------------------------------------------------------"
echo ""
echo "To get started, run the following command in a new terminal:"
echo "  reality-router"
echo ""
echo "If the command is not found, you may need to source your shell profile:"
echo "  source $SHELL_PROFILE"
echo ""
echo "To update the installation in the future, just run the installer script again."
echo "The project is installed at: $TARGET_DIR"
echo ""

exit 0
