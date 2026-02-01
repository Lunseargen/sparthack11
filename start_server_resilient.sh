#!/bin/bash

# Resilient server starter - restarts server if it crashes

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate hack

# Max restart attempts to prevent infinite loops
MAX_RESTARTS=10
RESTART_DELAY=2
RESTART_COUNT=0

echo "======================================================"
echo "Starting Flask Server (with auto-restart on crash)"
echo "======================================================"
echo ""

while [ $RESTART_COUNT -lt $MAX_RESTARTS ]; do
    echo "[$(date '+%H:%M:%S')] Attempting to start server... (attempt $((RESTART_COUNT + 1))/$MAX_RESTARTS)"
    
    # Run the server
    python python/server.py
    
    EXIT_CODE=$?
    echo ""
    echo "[$(date '+%H:%M:%S')] Server exited with code: $EXIT_CODE"
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Server stopped gracefully."
        break
    else
        RESTART_COUNT=$((RESTART_COUNT + 1))
        if [ $RESTART_COUNT -lt $MAX_RESTARTS ]; then
            echo "Server crashed! Restarting in ${RESTART_DELAY} seconds..."
            sleep $RESTART_DELAY
        else
            echo "Max restart attempts ($MAX_RESTARTS) reached. Giving up."
        fi
    fi
    echo ""
done

echo "======================================================"
echo "Server stopped"
echo "======================================================"
