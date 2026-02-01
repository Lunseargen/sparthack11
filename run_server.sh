#!/bin/bash

set -e

echo "=== Sparthack11 Server Setup ==="
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Error: conda is not installed or not in PATH"
    exit 1
fi

echo "✓ Conda found"

# Check if hack environment exists
if ! conda env list | grep -q "hack"; then
    echo "❌ Error: 'hack' conda environment not found"
    echo "Run ./setup_env.sh first to create it"
    exit 1
fi

echo "✓ 'hack' environment found"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✓ Environment variables loaded from .env"
else
    echo "⚠ .env file not found, using defaults"
    FLASK_HOST="localhost"
    FLASK_PORT="5000"
fi

# Check if frames directory exists
if [ ! -d "$FRAMES_DIR" ]; then
    mkdir -p "$FRAMES_DIR"
    echo "✓ Created frames directory"
fi

echo ""
echo "Starting Flask server..."
echo "  Host: $FLASK_HOST"
echo "  Port: $FLASK_PORT"
echo "  Frames directory: $(pwd)/$FRAMES_DIR"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
conda run -n hack python python/camera.py
