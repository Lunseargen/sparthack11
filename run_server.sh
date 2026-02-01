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

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $SERVER_PID $VIEWER_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Flask server in background
conda run -n hack python python/server.py &
SERVER_PID=$!
echo "✓ Flask server started (PID: $SERVER_PID)"

# Wait a moment for server to start
sleep 2

# Start frame viewer in background
conda run -n hack python python/frame_viewer.py &
VIEWER_PID=$!
echo "✓ Frame viewer started (PID: $VIEWER_PID)"

echo ""
echo "Both services running. Press Ctrl+C to stop."
echo ""

# Wait for both processes
wait
