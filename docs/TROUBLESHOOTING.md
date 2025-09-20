# secIRC Troubleshooting Guide

## Overview

This guide helps you diagnose and resolve common issues with secIRC. It covers installation problems, connection issues, security concerns, and performance problems.

## 🚀 Installation Issues

### Python Version Problems

#### Issue: Python version too old
```
Error: Python 3.8 or higher is required
```

**Solution:**
```bash
# Check current Python version
python --version

# Install Python 3.8+ (Ubuntu/Debian)
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-pip

# Install Python 3.8+ (macOS)
brew install python@3.8

# Install Python 3.8+ (Windows)
# Download from https://python.org
```

#### Issue: Virtual environment creation fails
```
Error: Failed to create virtual environment
```

**Solution:**
```bash
# Ensure python3-venv is installed
sudo apt install python3-venv

# Try creating venv with specific Python version
python3.8 -m venv venv

# Check available Python versions
ls /usr/bin/python*
```

### Dependency Installation Issues

#### Issue: Package installation fails
```
ERROR: Could not find a version that satisfies the requirement
```

**Solution:**
```bash
# Update pip
pip install --upgrade pip

# Clear pip cache
pip cache purge

# Install with no cache
pip install --no-cache-dir -r requirements.txt

# Install specific version
pip install package==version
```

#### Issue: Cryptographic library errors
```
Error: Failed to build cryptography
```

**Solution:**
```bash
# Install build dependencies
sudo apt install build-essential libssl-dev libffi-dev python3-dev

# Install cryptography separately
pip install cryptography

# Or use pre-compiled wheel
pip install --only-binary=cryptography cryptography
```

## 🌐 Connection Issues

### Network Connectivity

#### Issue: Cannot connect to relay servers
```
Error: Failed to connect to relay server
```

**Diagnosis:**
```bash
# Test network connectivity
ping relay1.secirc.net

# Test UDP connectivity
nc -u -v relay1.secirc.net 6667

# Check firewall
sudo ufw status
```

**Solutions:**
```bash
# Allow UDP port 6667
sudo ufw allow 6667/udp

# Check if port is in use
netstat -tlnp | grep 6667

# Try different relay
# Edit config/client.yaml with different bootstrap_relays
```

#### Issue: Connection timeout
```
Error: Connection timeout after 30 seconds
```

**Solutions:**
```bash
# Increase timeout in configuration
# config/client.yaml
network:
  connection_timeout: 60

# Check network speed
speedtest-cli

# Try different network
# Switch to different WiFi network or use mobile data
```

### Relay Discovery Issues

#### Issue: No relays discovered
```
Warning: No relay servers discovered
```

**Diagnosis:**
```bash
# Check DNS resolution
nslookup relay1.secirc.net

# Test web API
curl https://api.secirc.net/relays

# Check network connectivity
ping 8.8.8.8
```

**Solutions:**
```bash
# Use different DNS servers
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf

# Add manual relay configuration
# config/client.yaml
relay:
  bootstrap_relays:
    - host: "your.relay.server"
      port: 6667

# Check proxy settings
# Disable proxy if not needed
```

## 🔐 Security Issues

### Key Management Problems

#### Issue: Cannot decrypt messages
```
Error: Failed to decrypt message
```

**Diagnosis:**
```bash
# Check key files
ls -la data/keys/

# Verify key integrity
python -c "from src.protocol.encryption import EndToEndEncryption; print('Keys OK')"
```

**Solutions:**
```bash
# Regenerate keys
rm data/keys/user_identity.json
python src/client/main.py  # Will prompt for new identity

# Check password
# Ensure you're using the correct password

# Restore from backup
cp backup/keys/user_identity.json data/keys/
```

#### Issue: Key rotation fails
```
Error: Key rotation failed
```

**Solutions:**
```bash
# Check network connectivity
ping relay1.secirc.net

# Verify relay status
# Check if relays are online and responding

# Manual key rotation
# Restart client to force key rotation

# Check logs
tail -f logs/client.log
```

### Authentication Issues

#### Issue: Authentication failed
```
Error: Authentication failed
```

**Solutions:**
```bash
# Verify password
# Ensure you're using the correct password

# Check key files
ls -la data/keys/

# Regenerate identity
rm data/keys/user_identity.json
python src/client/main.py
```

## 📱 Client Issues

### Message Problems

#### Issue: Messages not sending
```
Error: Failed to send message
```

**Diagnosis:**
```bash
# Check connection status
# Look for connection indicators in client

# Check recipient hash
# Verify recipient hash is correct

# Check message size
# Ensure message is not too large
```

**Solutions:**
```bash
# Restart client
# Close and reopen secIRC client

# Check network
# Ensure internet connection is working

# Try different recipient
# Test with known working recipient
```

#### Issue: Messages not receiving
```
Warning: No messages received
```

**Solutions:**
```bash
# Check connection status
# Ensure client is connected to network

# Check message queue
# Look for queued messages

# Restart client
# Close and reopen secIRC client

# Check firewall
# Ensure UDP port 6667 is not blocked
```

### Group Issues

#### Issue: Cannot join group
```
Error: Failed to join group
```

**Solutions:**
```bash
# Verify group hash
# Ensure group hash is correct

# Check group status
# Ensure group is active and accepting members

# Try again later
# Group might be temporarily unavailable
```

#### Issue: Group messages not working
```
Error: Group message failed
```

**Solutions:**
```bash
# Check group membership
# Ensure you're a member of the group

# Verify group key
# Check if group key is valid

# Restart client
# Close and reopen secIRC client
```

## 🖥️ Server Issues

### Relay Server Problems

#### Issue: Server won't start
```
Error: Failed to start relay server
```

**Diagnosis:**
```bash
# Check port availability
netstat -tlnp | grep 6667

# Check permissions
ls -la src/server/main.py

# Check configuration
python -c "import yaml; print(yaml.safe_load(open('config/server.yaml')))"
```

**Solutions:**
```bash
# Kill process using port
sudo lsof -ti:6667 | xargs kill -9

# Check file permissions
chmod +x src/server/main.py

# Fix configuration
# Edit config/server.yaml to fix any errors
```

#### Issue: Server crashes
```
Error: Server crashed unexpectedly
```

**Solutions:**
```bash
# Check logs
tail -f logs/server.log

# Check system resources
free -h
df -h

# Restart server
python src/server/main.py

# Check for memory leaks
# Monitor memory usage over time
```

### Performance Issues

#### Issue: High CPU usage
```
Warning: High CPU usage detected
```

**Solutions:**
```bash
# Check running processes
top -p $(pgrep -f secIRC)

# Reduce message frequency
# Send fewer messages per second

# Check for infinite loops
# Look for code that might be running continuously

# Restart server
# Restart to clear any stuck processes
```

#### Issue: High memory usage
```
Warning: High memory usage detected
```

**Solutions:**
```bash
# Check memory usage
free -h

# Clear message cache
# Reduce message_cache_size in configuration

# Restart server
# Restart to clear memory

# Check for memory leaks
# Monitor memory usage over time
```

## 🔧 Configuration Issues

### Configuration File Problems

#### Issue: Invalid configuration
```
Error: Invalid configuration file
```

**Solutions:**
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/server.yaml'))"

# Check file permissions
ls -la config/

# Restore from backup
cp config/server.yaml.backup config/server.yaml

# Use default configuration
cp config/server.yaml.example config/server.yaml
```

#### Issue: Configuration not loading
```
Warning: Using default configuration
```

**Solutions:**
```bash
# Check file path
ls -la config/server.yaml

# Check file permissions
chmod 644 config/server.yaml

# Check file format
file config/server.yaml

# Recreate configuration
rm config/server.yaml
cp config/server.yaml.example config/server.yaml
```

## 📊 Monitoring and Diagnostics

### Log Analysis

#### Check Log Files
```bash
# Server logs
tail -f logs/server.log

# Client logs
tail -f logs/client.log

# System logs
journalctl -u secirc -f

# Search for errors
grep -i error logs/server.log
grep -i warning logs/server.log
```

#### Log Levels
```bash
# Increase log verbosity
# config/server.yaml
logging:
  level: "DEBUG"

# Restart server
python src/server/main.py
```

### Network Diagnostics

#### Network Testing
```bash
# Test connectivity
ping relay1.secirc.net

# Test UDP
nc -u -v relay1.secirc.net 6667

# Check routing
traceroute relay1.secirc.net

# Check DNS
nslookup relay1.secirc.net
```

#### Port Testing
```bash
# Check if port is open
netstat -tlnp | grep 6667

# Test port connectivity
telnet relay1.secirc.net 6667

# Check firewall
sudo ufw status
```

### Performance Monitoring

#### System Resources
```bash
# CPU usage
top -p $(pgrep -f secIRC)

# Memory usage
free -h

# Disk usage
df -h

# Network usage
iftop
```

#### Application Metrics
```bash
# Check server stats
curl http://localhost:8080/stats

# Check client stats
# Look in client interface

# Monitor message throughput
# Check logs for message counts
```

## 🆘 Getting Help

### Self-Help Resources

1. **Check Documentation**: Read the comprehensive documentation
2. **Search Issues**: Look for similar issues on GitHub
3. **Check Logs**: Analyze log files for error messages
4. **Test Configuration**: Validate your configuration files

### Community Support

1. **GitHub Issues**: Report bugs and ask questions
2. **Discussions**: Join community discussions
3. **Discord/Slack**: Join community chat channels
4. **Forum**: Participate in community forums

### Professional Support

1. **Commercial Support**: Contact for commercial support
2. **Consulting**: Hire consultants for deployment help
3. **Training**: Attend training sessions
4. **Custom Development**: Request custom features

## 📋 Common Solutions Summary

### Quick Fixes

```bash
# Restart everything
sudo systemctl restart secirc
python src/client/main.py

# Clear cache and restart
rm -rf data/cache/*
python src/server/main.py

# Reset configuration
cp config/server.yaml.example config/server.yaml
python src/server/main.py

# Regenerate keys
rm data/keys/*
python src/client/main.py
```

### Emergency Recovery

```bash
# Stop all processes
sudo pkill -f secIRC

# Clear all data
rm -rf data/*
rm -rf logs/*

# Restore from backup
cp -r backup/* .

# Restart services
python src/server/main.py
```

---

This troubleshooting guide covers the most common issues and their solutions. For issues not covered here, please check the documentation or contact the community for help.
