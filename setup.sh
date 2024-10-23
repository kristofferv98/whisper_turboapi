#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Default values
REQUIRED_PYTHON="3.12.3"
ASSUME_YES=false
FORCE=false

# Function to display usage instructions
usage() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -y, --yes               Run in headless mode (assume 'yes' to all prompts)"
    echo "  -p, --python-version    Specify the required Python version (default: $REQUIRED_PYTHON)"
    echo "  -f, --force             Force actions like recreating the virtual environment"
    echo "  -h, --help              Display this help message and exit"
    exit 1
}

# Function to check if a command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    else
        return 0
    fi
}

# Function to prompt the user for confirmation
prompt_continue() {
    local message="$1"
    local allow_cancel="${2:-true}"  # Controls whether 'No' is allowed

    if [ "$ASSUME_YES" = true ]; then
        echo "$message (auto-accepted due to --yes flag)"
        return 0
    fi

    while true; do
        read -p "$message Continue? (Y/n) " REPLY
        REPLY=${REPLY:-Y}  # Default to 'Y' if empty
        case $REPLY in
            [Yy]* ) return 0;;
            [Nn]* )
                if [ "$allow_cancel" = true ]; then
                    echo
                    echo "⚠️  Setup cancelled by user."
                    exit 1
                else
                    echo "This step cannot be skipped. Please choose 'Y' to continue."
                fi
                ;;
            * ) echo "Please answer Y or n.";;
        esac
    done
}

# Function to print step headers
print_step() {
    echo
    echo "📍 Step $1: $2"
    echo "-------------------"
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -y|--yes)
            ASSUME_YES=true
            shift
            ;;
        -p|--python-version)
            if [[ -n "$2" ]]; then
                REQUIRED_PYTHON="$2"
                shift 2
            else
                echo "Error: '--python-version' requires a value"
                exit 1
            fi
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

echo "🚀 WhisperTurboAPI Setup Script"
echo "==============================="

# Step 1: System and Environment Check
print_step "1" "Checking Environment"

# Check if the script is being run from the project directory by looking for requirements.txt
if [[ ! -f "requirements.txt" ]]; then
    echo "❌ requirements.txt not found. Please ensure you're running the script from the project root directory."
    exit 1
fi

# Check for pyenv
PYENV_AVAILABLE=false
if check_command "pyenv"; then
    PYENV_AVAILABLE=true
    eval "$(pyenv init -)"
    export PATH="$(pyenv root)/shims:$PATH"
fi

# Function to find the appropriate Python interpreter
find_python() {
    if $PYENV_AVAILABLE; then
        # Use pyenv to find the Python version
        if pyenv versions --bare | grep -q "^$REQUIRED_PYTHON\$"; then
            echo "$(pyenv root)/versions/$REQUIRED_PYTHON/bin/python"
        else
            echo ""
        fi
    else
        # Check system Python versions
        PYTHON_PATH=$(command -v python3 || command -v python)
        if [[ -n "$PYTHON_PATH" ]]; then
            PYTHON_VERSION=$($PYTHON_PATH --version 2>&1 | awk '{print $2}')
            if [[ "$PYTHON_VERSION" == "$REQUIRED_PYTHON" ]]; then
                echo "$PYTHON_PATH"
            else
                echo ""
            fi
        else
            echo ""
        fi
    fi
}

PYTHON_PATH=$(find_python)

if [[ -z "$PYTHON_PATH" ]]; then
    echo "❌ Required Python version $REQUIRED_PYTHON not found."
    if $PYENV_AVAILABLE; then
        prompt_continue "Would you like to install Python $REQUIRED_PYTHON using pyenv?" false
        pyenv install "$REQUIRED_PYTHON"
        PYTHON_PATH="$(pyenv root)/versions/$REQUIRED_PYTHON/bin/python"
    else
        echo "Please install Python $REQUIRED_PYTHON and ensure it's available in your PATH."
        exit 1
    fi
fi

echo "✅ Using Python interpreter: $PYTHON_PATH"

# Ensure that the correct Python is being used
CURRENT_PYTHON_VERSION=$($PYTHON_PATH --version 2>&1 | awk '{print $2}')
if [[ "$CURRENT_PYTHON_VERSION" == "$REQUIRED_PYTHON" ]]; then
    echo "✅ Python version $CURRENT_PYTHON_VERSION is correct."
else
    echo "❌ Error: Python version mismatch."
    exit 1
fi

# Step 2: Project Setup
print_step "2" "Project Setup"

# Check if virtual environment exists
if [[ -d ".venv" ]]; then
    VENV_PYTHON_VERSION=$(./.venv/bin/python --version 2>&1 | awk '{print $2}')
    echo "✅ Found existing virtual environment with Python $VENV_PYTHON_VERSION"
    if [[ "$VENV_PYTHON_VERSION" != "$REQUIRED_PYTHON" ]]; then
        echo "⚠️  Virtual environment uses Python $VENV_PYTHON_VERSION instead of required $REQUIRED_PYTHON"
        if [ "$FORCE" = true ]; then
            echo "🔄 Force flag detected. Recreating the virtual environment."
            rm -rf ".venv"
        else
            prompt_continue "Would you like to recreate the virtual environment with the correct Python version?" false
            rm -rf ".venv"
        fi
        echo "Creating virtual environment with Python interpreter: $PYTHON_PATH"
        "$PYTHON_PATH" -m venv .venv
    else
        echo "Virtual environment Python version matches the required version."
    fi
else
    echo "No virtual environment found."
    if [ "$FORCE" = true ]; then
        echo "🔄 Force flag detected. Creating a new virtual environment."
    else
        prompt_continue "Would you like to create a new virtual environment?" false
    fi
    echo "Creating virtual environment with Python interpreter: $PYTHON_PATH"
    "$PYTHON_PATH" -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Verify that the virtual environment uses the correct Python version
VENV_PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
if [[ "$VENV_PYTHON_VERSION" != "$REQUIRED_PYTHON" ]]; then
    echo "❌ Error: Virtual environment is using Python $VENV_PYTHON_VERSION instead of required $REQUIRED_PYTHON."
    echo "Please ensure that the virtual environment is created with the correct Python version."
    exit 1
fi

# Step 3: Install Dependencies
print_step "3" "Installing Dependencies"

echo "Installing project dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# Step 4: Verify Installation
print_step "4" "Verifying Installation"

echo "Checking required packages..."
MISSING_PACKAGES=false
# List of all required packages
REQUIRED_PACKAGES=("fastapi" "uvicorn" "aiohttp" "requests" "mlx" "numpy" "librosa" "tiktoken" "huggingface_hub" "fire")

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python -c "import $package" 2>/dev/null; then
        echo "❌ Package '$package' is not properly installed"
        MISSING_PACKAGES=true
    else
        echo "✅ Package '$package' is installed"
    fi
done

if [ "$MISSING_PACKAGES" = true ]; then
    echo "⚠️  Some required packages are missing."
    prompt_continue "Would you like to continue anyway?" true
fi

# Step 5: Final Setup
print_step "5" "Finalizing Setup"

# Ensure that start_server.sh is executable
chmod +x start_server.sh

echo
echo "✨ Setup Complete! ✨"
echo
echo "To start the server, run:"
echo "   ./start_server.sh"
echo
echo "The server will be available at http://localhost:8000"

# Ask about starting server
if [ "$ASSUME_YES" = true ]; then
    echo "Starting server automatically due to --yes flag."
    ./start_server.sh
else
    read -p "Would you like to start the server now? (Y/n) " REPLY
    REPLY=${REPLY:-Y}
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting server..."
        ./start_server.sh
    else
        echo "You can start the server later by running './start_server.sh'"
    fi
fi