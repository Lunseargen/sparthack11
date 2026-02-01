#!/bin/bash

echo "Setting up conda environment 'hack'..."

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Error: conda is not installed or not in PATH"
    exit 1
fi

echo "Removing old hack environment (if exists)..."
conda remove -n hack --all -y 2>/dev/null

echo "Creating new hack environment with Python 3.12..."
conda create -n hack python=3.12 -y

if [ $? -ne 0 ]; then
    echo "Error: Could not create 'hack' environment"
    exit 1
fi

echo "Installing required packages to 'hack' environment..."

# Install packages using conda
conda install -n hack -y flask opencv pillow numpy

if [ $? -eq 0 ]; then
    echo "✓ All packages installed successfully!"
    echo "To activate: conda activate hack"
    echo "To start the server, run: python python/camera.py"
else
    echo "✗ Error installing packages"
    exit 1
fi
