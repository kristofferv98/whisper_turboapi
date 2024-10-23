#!/bin/bash

# Default values
HOST="0.0.0.0"
PORT="8000"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host=*)
            HOST="${1#*=}"
            shift
            ;;
        --port=*)
            PORT="${1#*=}"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--host=HOST] [--port=PORT]"
            echo "Default host: 0.0.0.0"
            echo "Default port: 8000"
            exit 0
            ;;
        *)
            echo "Unknown parameter: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Activate virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    if [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
        echo "✅ Virtual environment activated: $VIRTUAL_ENV"
    else
        echo "❌ Virtual environment not found. Please run ./setup.sh first"
        exit 1
    fi
else
    echo "✅ Virtual environment already active: $VIRTUAL_ENV"
fi

# Quick environment check
MISSING_PACKAGES=false
REQUIRED_PACKAGES=("fastapi" "uvicorn" "aiohttp" "requests" "mlx" "numpy" "librosa" "tiktoken" "huggingface_hub" "fire" 
)

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python -c "import $package" &>/dev/null; then
        echo "❌ Required package '$package' is missing."
        MISSING_PACKAGES=true
    fi
done

if [ "$MISSING_PACKAGES" = true ]; then
    echo "❌ Required packages missing. Please run ./setup.sh first"
    exit 1
else
    echo "✅ All required packages are installed."
fi

# Start the server
echo "🚀 Starting WhisperTurboAPI server..."
python -m uvicorn scripts.main:app --host "$HOST" --port "$PORT"
