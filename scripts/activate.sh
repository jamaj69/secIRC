#!/bin/bash

# secIRC Development Environment Activation Script
# This script activates the virtual environment and sets up the development environment

echo "🔧 Activating secIRC development environment..."

# Check if we're in the project root
if [ ! -f "requirements.txt" ] || [ ! -d "src" ]; then
    echo "❌ Please run this script from the secIRC project root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./scripts/setup.sh first"
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
source venv/bin/activate

# Set environment variables
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
export SECIRC_ENV="development"
export SECIRC_DEBUG="true"

# Load .env file if it exists
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env..."
    set -a
    source .env
    set +a
fi

echo "✅ Environment activated successfully!"
echo ""
echo "Available commands:"
echo "  python src/server/main.py    - Start the IRC server"
echo "  python src/client/main.py    - Start the IRC client"
echo "  pytest                      - Run tests"
echo "  black src/                  - Format code"
echo "  flake8 src/                 - Lint code"
echo "  mypy src/                   - Type check"
echo ""
echo "Python path: $PYTHONPATH"
echo "Virtual env: $VIRTUAL_ENV"
echo ""

