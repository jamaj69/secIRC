#!/bin/bash

# secIRC Setup Script
# This script sets up the development environment for secIRC

set -e

echo "🚀 Setting up secIRC development environment..."

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $RETHON_VERSION is installed, but Python $REQUIRED_VERSION or higher is required."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data
mkdir -p temp
mkdir -p uploads

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 scripts/*.sh
chmod 644 config/*.yaml

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file..."
    cat > .env << EOF
# secIRC Environment Configuration
SECIRC_ENV=development
SECIRC_DEBUG=true
SECIRC_LOG_LEVEL=INFO

# Server Configuration
SECIRC_SERVER_HOST=0.0.0.0
SECIRC_SERVER_PORT=6667
SECIRC_SSL_PORT=6697

# Security
SECIRC_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
SECIRC_ENCRYPTION_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')

# Database
SECIRC_DATABASE_URL=sqlite:///data/secirc.db

# SSL/TLS
SECIRC_SSL_CERT=config/ssl/server.crt
SECIRC_SSL_KEY=config/ssl/server.key
EOF
    echo "✅ .env file created"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start development:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run the server: python src/server/main.py"
echo "3. Or run tests: pytest"
echo ""
echo "For web interface development:"
echo "1. cd web"
echo "2. npm install"
echo "3. npm start"
