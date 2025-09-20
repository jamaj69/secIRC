# secIRC Installation Guide

## Overview

This guide provides step-by-step instructions for installing and setting up the secIRC anonymous messaging system. The installation process is designed to be simple and automated.

## 🚀 Quick Start

### Automatic Installation (Recommended)

The easiest way to install secIRC is using the automated setup script:

```bash
# Clone the repository
git clone https://github.com/your-repo/secIRC.git
cd secIRC

# Run the setup script
./scripts/setup.sh
```

The setup script will:
- Check Python version requirements
- Create a virtual environment
- Install all dependencies
- Create necessary directories
- Set up configuration files
- Generate security keys

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows
- **Python**: Version 3.8 or higher
- **Memory**: Minimum 512MB RAM
- **Storage**: Minimum 100MB free space
- **Network**: Internet connection for initial setup

### Required Software
- **Python 3.8+**: Core runtime environment
- **pip**: Python package manager
- **git**: Version control system
- **OpenSSL**: Cryptographic library (usually pre-installed)

### Optional Software
- **Docker**: For containerized deployment
- **systemd**: For service management on Linux
- **nginx**: For web interface (if using web client)

## 🔧 Manual Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/your-repo/secIRC.git
cd secIRC
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate     # On Windows
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Create Directories

```bash
# Create necessary directories
mkdir -p logs
mkdir -p data
mkdir -p temp
mkdir -p uploads
mkdir -p config/ssl
```

### Step 5: Set Permissions

```bash
# Set script permissions
chmod +x scripts/*.sh

# Set configuration permissions
chmod 644 config/*.yaml
```

### Step 6: Generate Configuration

```bash
# Create .env file
cp .env.example .env

# Edit configuration as needed
nano .env
```

## 🐳 Docker Installation

### Using Docker Compose

```bash
# Clone repository
git clone https://github.com/your-repo/secIRC.git
cd secIRC

# Build and start services
docker-compose up -d
```

### Using Docker

```bash
# Build image
docker build -t secirc .

# Run container
docker run -d \
  --name secirc-server \
  -p 6667:6667 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/app/config \
  secirc
```

## 🔐 Security Setup

### Generate SSL Certificates

```bash
# Create SSL directory
mkdir -p config/ssl

# Generate self-signed certificate
openssl req -x509 -newkey rsa:2048 -keyout config/ssl/server.key -out config/ssl/server.crt -days 365 -nodes
```

### Generate Secret Keys

```bash
# Generate secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate encryption key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Set Environment Variables

```bash
# Add to .env file
SECIRC_SECRET_KEY=your_secret_key_here
SECIRC_ENCRYPTION_KEY=your_encryption_key_here
```

## ⚙️ Configuration

### Basic Configuration

Edit the configuration files in the `config/` directory:

#### Server Configuration (`config/server.yaml`)

```yaml
server:
  host: "0.0.0.0"
  port: 6667
  ssl_port: 6697

network:
  udp_port: 6667
  max_packet_size: 1400

relay:
  discovery_interval: 300
  sync_interval: 60
  max_relay_hops: 5
  bootstrap_relays:
    - host: "relay1.secirc.net"
      port: 6667
    - host: "relay2.secirc.net"
      port: 6667

first_ring:
  members: []
  consensus_threshold: 0.6
  challenge_interval: 3600

ring_expansion:
  interval: 1800
  candidates: 5
  consensus_threshold: 0.7
```

#### Client Configuration (`config/client.yaml`)

```yaml
client:
  nickname: "anonymous_user"
  auto_connect: true
  message_cache_size: 1000

network:
  udp_port: 6667
  relay_discovery_interval: 300
  max_relay_hops: 5
  bootstrap_relays:
    - host: "relay1.secirc.net"
      port: 6667

security:
  key_storage_path: "data/keys"
  password_protection: true
  auto_key_rotation: true
```

#### Security Configuration (`config/security.yaml`)

```yaml
encryption:
  algorithm: "RSA-2048"
  hash_algorithm: "SHA-256"
  key_length: 2048
  password_hash_algorithm: "Argon2"

session:
  key_rotation_interval: 86400
  max_session_age: 172800

traffic:
  obfuscation_level: "high"
  dummy_traffic_ratio: 0.1
  message_padding: true
```

### Environment Variables

Create a `.env` file with the following variables:

```bash
# secIRC Environment Configuration
SECIRC_ENV=development
SECIRC_DEBUG=true
SECIRC_LOG_LEVEL=INFO

# Server Configuration
SECIRC_SERVER_HOST=0.0.0.0
SECIRC_SERVER_PORT=6667
SECIRC_SSL_PORT=6697

# Security
SECIRC_SECRET_KEY=your_secret_key_here
SECIRC_ENCRYPTION_KEY=your_encryption_key_here

# Database
SECIRC_DATABASE_URL=sqlite:///data/secirc.db

# SSL/TLS
SECIRC_SSL_CERT=config/ssl/server.crt
SECIRC_SSL_KEY=config/ssl/server.key
```

## 🚀 Running secIRC

### Start Relay Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start relay server
python src/server/main.py
```

### Start Client

```bash
# Activate virtual environment
source venv/bin/activate

# Start client
python src/client/main.py
```

### Using the Setup Script

```bash
# Activate environment and start server
./scripts/activate.sh
python src/server/main.py
```

## 🔧 Service Installation

### Linux (systemd)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/secirc.service
```

Add the following content:

```ini
[Unit]
Description=secIRC Relay Server
After=network.target

[Service]
Type=simple
User=secirc
WorkingDirectory=/home/secirc/secIRC
ExecStart=/home/secirc/secIRC/venv/bin/python src/server/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable secirc
sudo systemctl start secirc
sudo systemctl status secirc
```

### macOS (launchd)

Create a launchd plist file:

```bash
nano ~/Library/LaunchAgents/com.secirc.server.plist
```

Add the following content:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.secirc.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/secIRC/venv/bin/python</string>
        <string>src/server/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/secIRC</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load and start the service:

```bash
launchctl load ~/Library/LaunchAgents/com.secirc.server.plist
launchctl start com.secirc.server
```

## 🧪 Testing Installation

### Run Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_server.py

# Run with coverage
pytest --cov=src tests/
```

### Verify Installation

```bash
# Check Python version
python --version

# Check installed packages
pip list

# Check configuration
python -c "import yaml; print(yaml.safe_load(open('config/server.yaml')))"

# Check SSL certificates
openssl x509 -in config/ssl/server.crt -text -noout
```

## 🔍 Troubleshooting

### Common Issues

#### Python Version Issues
```bash
# Check Python version
python --version

# If version is too old, install Python 3.8+
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-pip
```

#### Permission Issues
```bash
# Fix script permissions
chmod +x scripts/*.sh

# Fix directory permissions
chmod 755 data logs temp uploads
```

#### Dependency Issues
```bash
# Update pip
pip install --upgrade pip

# Reinstall dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

#### SSL Certificate Issues
```bash
# Regenerate SSL certificates
rm config/ssl/server.crt config/ssl/server.key
openssl req -x509 -newkey rsa:2048 -keyout config/ssl/server.key -out config/ssl/server.crt -days 365 -nodes
```

### Log Files

Check log files for errors:

```bash
# Server logs
tail -f logs/server.log

# Client logs
tail -f logs/client.log

# System logs
journalctl -u secirc -f
```

### Network Issues

```bash
# Check if ports are open
netstat -tlnp | grep 6667

# Test UDP connectivity
nc -u -v relay1.secirc.net 6667

# Check firewall
sudo ufw status
```

## 📚 Next Steps

After successful installation:

1. **Read the Configuration Guide**: Learn about configuration options
2. **Read the User Manual**: Learn how to use secIRC
3. **Read the Administrator Guide**: Learn about system administration
4. **Join the Community**: Get help and contribute to the project

## 🆘 Getting Help

If you encounter issues:

1. **Check the Troubleshooting Guide**: Common issues and solutions
2. **Search GitHub Issues**: Look for similar issues
3. **Create a GitHub Issue**: Report bugs or ask questions
4. **Join Discussions**: Get help from the community

---

This installation guide provides comprehensive instructions for setting up secIRC. The automated setup script makes installation simple, while manual installation gives you full control over the process.
