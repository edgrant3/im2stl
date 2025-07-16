#!/bin/bash
echo "HERE"
# Exit immediately if a command exits with a non-zero status
set -e

# Define environment directory name
VENV_DIR="venv"

# Check if virtual environment already exists
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment '$VENV_DIR' already exists. Skipping creation."
else
    echo "Creating virtual environment in '$VENV_DIR'..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "Dependencies installed."
else
    echo "requirements.txt not found. Skipping dependency installation."
fi

echo "Setup complete."
