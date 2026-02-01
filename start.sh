#!/bin/bash

# SparthHack11 - Quick Start Flask Server
# Fast setup and launch the backend server

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create directories
mkdir -p frames uploads audio

# Setup virtual environment if needed
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# Install/update requirements silently
pip install -q -r python/requirements.txt

# Start Flask server
echo "Starting SparthHack11 Backend Server..."
echo "Server running at: http://localhost:5000"
python3 python/app.py
