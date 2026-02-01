#!/bin/bash
# Usage: ./clear_dir.sh /path/to/target_directory

TARGET_DIR="$1"

# Check if directory exists and is not empty
if [ -d "$TARGET_DIR" ]; then
    echo "Clearing files in $TARGET_DIR..."
    rm -rf "${TARGET_DIR:?}"/*
    echo "Done."
else
    echo "Error: Directory $TARGET_DIR not found."
fi
