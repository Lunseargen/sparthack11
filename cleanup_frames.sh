#!/bin/bash

set -e

FRAMES_DIR="frames"
MAX_FRAMES=2000

echo "=== Frame Cleanup Script ==="
echo "Max frames allowed: $MAX_FRAMES"
echo "Frames directory: $FRAMES_DIR"
echo ""

# Check if frames directory exists
if [ ! -d "$FRAMES_DIR" ]; then
    echo "❌ Error: $FRAMES_DIR directory not found"
    exit 1
fi

# Count current frames
FRAME_COUNT=$(ls -1 "$FRAMES_DIR"/*.jpg 2>/dev/null | wc -l)
echo "Current frames: $FRAME_COUNT"

if [ $FRAME_COUNT -le $MAX_FRAMES ]; then
    echo "✓ Within limit, no cleanup needed"
    exit 0
fi

# Calculate how many to delete
TO_DELETE=$((FRAME_COUNT - MAX_FRAMES))
echo "⚠ Over limit, deleting $TO_DELETE oldest frames..."

# Sort by modification time and delete oldest
ls -1t "$FRAMES_DIR"/*.jpg 2>/dev/null | tail -n $TO_DELETE | xargs rm -f

# Verify
NEW_COUNT=$(ls -1 "$FRAMES_DIR"/*.jpg 2>/dev/null | wc -l)
echo "✓ Cleanup complete - Remaining frames: $NEW_COUNT"
