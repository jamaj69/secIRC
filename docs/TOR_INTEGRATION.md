# secIRC Tor Integration

## Overview

The secIRC Tor integration provides transparent proxy support for anonymous relay connections using multiple Tor packages. This allows relay servers to connect to each other through the Tor network for enhanced privacy and censorship resistance.

## Features

### Multiple Tor Packages Support
- **PySocks**: SOCKS5 proxy support for Tor connections
- **tor-proxy**: Transparent Tor proxy package
- **Torpy**: Pure Python Tor protocol implementation
- **Stem**: Tor controller library for advanced management

### Transparent Integration
- **Automatic Detection**: Automatically detects available Tor packages
- **Fallback Support**: Falls back to available methods if preferred method fails
- **Connection Verification**: Verifies that connections are actually using Tor
- **IP Rotation**: Supports automatic IP address rotation

### Advanced Features
- **Circuit Management**: Manages Tor circuits and exit nodes
- **Connection Monitoring**: Monitors Tor connection health and performance
- **Security Verification**: Verifies Tor network usage
- **Configuration Flexibility**: Extensive configuration options

## Available Tor Packages

### 1. PySocks (Recommended)
**Package**: `PySocks>=1.7.1`

**Features**:
- SOCKS5 proxy support
- Works with existing Tor daemon
- Most reliable and widely supported
- Low resource usage

**Usage**:
```python
from protocol.tor_integration import TorIntegration, TorConfig, TorMethod

config = TorConfig(
    method=TorMethod.PYSOCKS,
    socks_host="127.0.0.1",
    socks_port=9050
)

tor_integration = TorIntegration(config)
await tor_integration.initialize()
```

### 2. tor-proxy
**Package**: `tor-proxy>=0.1.0`

**Features**:
- Transparent Tor proxy
- Multiple instances support
- No root permissions required
- Automatic Tor daemon management

**Usage**:
```python
config = TorConfig(
    method=TorMethod.TOR_PROXY,
    enable_ip_rotation=True
)

tor_integration = TorIntegration(config)
await tor_integration.initialize()
```

### 3. Torpy (Pure Python)
**Package**: `torpy>=1.1.0`

**Features**:
- Pure Python implementation
- No external Tor daemon required
- Built-in circuit management
- Cross-platform compatibility

**Usage**:
```python
config = TorConfig(
    method=TorMethod.TORPY,
    enable_circuit_verification=True,
    circuit_timeout=60
)

tor_integration = TorIntegration(config)
await tor_integration.initialize()
```

### 4. Stem (Tor Controller)
**Package**: `stem>=1.8.0`

**Features**:
- Advanced Tor control
- Circuit management
- IP rotation support
- Detailed monitoring

**Usage**:
```python
config = TorConfig(
    method=TorMethod.STEM,
    control_host="127.0.0.1",
    control_port=9051,
    enable_ip_rotation=True,
    ip_rotation_interval=300
)

tor_integration = TorIntegration(config)
await tor_integration.initialize()
```

## Configuration

### Basic Configuration

```python
from protocol.tor_integration import TorConfig, TorMethod

# Basic PySocks configuration
config = TorConfig(
    method=TorMethod.PYSOCKS,
    socks_host="127.0.0.1",
    socks_port=9050
)
```

### Advanced Configuration

```python
# Advanced configuration with all options
config = TorConfig(
    method=TorMethod.STEM,
    socks_host="127.0.0.1",
    socks_port=9050,
    control_host="127.0.0.1",
    control_port=9051,
    control_password="your_password",  # Optional
    circuit_timeout=60,
    max_circuit_dirtiness=600,
    enable_ip_rotation=True,
    ip_rotation_interval=300,
    enable_circuit_verification=True,
    custom_tor_binary="/usr/bin/tor",
    tor_data_dir="/var/lib/tor",
    log_level="INFO"
)
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `method` | TorMethod | PYSOCKS | Tor connection method |
| `socks_host` | str | "127.0.0.1" | SOCKS proxy host |
| `socks_port` | int | 9050 | SOCKS proxy port |
| `control_host` | str | "127.0.0.1" | Tor control host |
| `control_port` | int | 9051 | Tor control port |
| `control_password` | str | None | Tor control password |
| `circuit_timeout` | int | 60 | Circuit timeout in seconds |
| `max_circuit_dirtiness` | int | 600 | Max circuit dirtiness |
| `enable_ip_rotation` | bool | True | Enable IP rotation |
| `ip_rotation_interval` | int | 300 | IP rotation interval |
| `enable_circuit_verification` | bool | True | Enable circuit verification |
| `custom_tor_binary` | str | None | Custom Tor binary path |
| `tor_data_dir` | str | None | Tor data directory |
| `log_level` | str | "INFO" | Logging level |

## Usage Examples

### Basic Tor Connection

```python
import asyncio
from protocol.tor_integration import TorIntegration, TorConfig, TorMethod

async def basic_tor_connection():
    # Create configuration
    config = TorConfig(
        method=TorMethod.PYSOCKS,
        socks_host="127.0.0.1",
        socks_port=9050
    )
    
    # Create Tor integration
    tor_integration = TorIntegration(config)
    
    # Initialize
    success = await tor_integration.initialize()
    if not success:
        print("Failed to initialize Tor integration")
        return
    
    # Create connection
    connection_id = "test_connection"
    connection = await tor_integration.create_connection(connection_id)
    if not connection:
        print("Failed to create Tor connection")
        return
    
    # Connect to a target through Tor
    sock = await tor_integration.connect_through_tor(
        connection_id, "example.onion", 6667
    )
    if sock:
        print("Successfully connected through Tor")
        sock.close()
    
    # Cleanup
    await tor_integration.close_connection(connection_id)
    await tor_integration.cleanup()

# Run the example
asyncio.run(basic_tor_connection())
```

### Tor Connection Verification

```python
async def verify_tor_connection():
    config = TorConfig(
        method=TorMethod.PYSOCKS,
        enable_circuit_verification=True
    )
    
    tor_integration = TorIntegration(config)
    await tor_integration.initialize()
    
    connection_id = "verification_test"
    await tor_integration.create_connection(connection_id)
    
    # Verify Tor connection
    is_tor = await tor_integration.verify_tor_connection(connection_id)
    if is_tor:
        print("✅ Using Tor network")
    else:
        print("❌ Not using Tor network")
    
    # Get exit node
    exit_node = await tor_integration.get_exit_node(connection_id)
    if exit_node:
        print(f"Exit node: {exit_node}")
    
    await tor_integration.cleanup()
```

### IP Rotation

```python
async def ip_rotation_example():
    config = TorConfig(
        method=TorMethod.STEM,
        enable_ip_rotation=True,
        ip_rotation_interval=300
    )
    
    tor_integration = TorIntegration(config)
    await tor_integration.initialize()
    
    connection_id = "rotation_test"
    await tor_integration.create_connection(connection_id)
    
    # Get initial exit node
    initial_exit = await tor_integration.get_exit_node(connection_id)
    print(f"Initial exit node: {initial_exit}")
    
    # Rotate IP
    success = await tor_integration.rotate_ip(connection_id)
    if success:
        print("IP rotation successful")
        
        # Get new exit node
        new_exit = await tor_integration.get_exit_node(connection_id)
        print(f"New exit node: {new_exit}")
    
    await tor_integration.cleanup()
```

### Integration with Relay Connections

```python
from protocol.relay_connections import RelayConnectionManager, ConnectionConfig, ConnectionType
from protocol.encryption import EndToEndEncryption

async def relay_with_tor():
    # Initialize encryption
    encryption = EndToEndEncryption()
    
    # Configure relay connections with Tor support
    config = ConnectionConfig(
        max_connections=10,
        min_connections=3,
        enable_tcp=True,
        enable_tor=True,  # Enable Tor support
        enable_websocket=True,
        tor_port=9050
    )
    
    # Create connection manager
    connection_manager = RelayConnectionManager(config, encryption)
    
    # Start connection manager (initializes Tor integration)
    await connection_manager.start_connection_manager()
    
    # Add Tor relay connection
    await connection_manager.add_relay_connection(
        relay_id=b"tor_relay",
        connection_type=ConnectionType.TOR,
        host="relay.onion",
        port=6667,
        priority=8
    )
    
    # Monitor connections
    status = connection_manager.get_connection_status()
    print(f"Active connections: {status['active_connections']}")
    
    # Cleanup
    await connection_manager.stop_connection_manager()
```

## Installation

### Install Tor Dependencies

```bash
# Install all Tor packages
pip install PySocks tor-proxy torpy stem

# Or install specific packages
pip install PySocks  # For SOCKS5 proxy support
pip install tor-proxy  # For transparent proxy
pip install torpy  # For pure Python Tor
pip install stem  # For Tor controller
```

### Install Tor Daemon

**Ubuntu/Debian**:
```bash
sudo apt-get install tor
sudo systemctl start tor
sudo systemctl enable tor
```

**CentOS/RHEL**:
```bash
sudo yum install tor
sudo systemctl start tor
sudo systemctl enable tor
```

**macOS**:
```bash
brew install tor
brew services start tor
```

**Windows**:
Download and install Tor Browser or Tor Expert Bundle.

## Configuration Files

### Tor Configuration (torrc)

```bash
# /etc/tor/torrc

# SOCKS proxy
SocksPort 9050
SocksPolicy accept 127.0.0.1
SocksPolicy reject *

# Control port
ControlPort 9051
HashedControlPassword 16:872860B76453A77D60CA2BB8C1A7042072093276A3D701AD684053EC4C

# Logging
Log notice file /var/log/tor/notices.log
Log info file /var/log/tor/debug.log

# Circuit management
MaxCircuitDirtiness 600
NewCircuitPeriod 30
```

### secIRC Configuration

```yaml
# config/relay_connections.yaml
connection_manager:
  enable_tor: true
  tor_port: 9050

tor:
  enabled: true
  socks_host: "127.0.0.1"
  socks_port: 9050
  control_host: "127.0.0.1"
  control_port: 9051
  enable_ip_rotation: true
  ip_rotation_interval: 300
  enable_circuit_verification: true
```

## Monitoring and Debugging

### Connection Status

```python
# Get Tor integration status
status = tor_integration.get_status()
print(f"Method: {status['method']}")
print(f"Active connections: {status['active_connections']}")
print(f"Available methods: {status['available_methods']}")
```

### Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Tor integration logs will show:
# - Connection attempts
# - Circuit creation
# - IP rotations
# - Verification results
```

### Health Checks

```python
async def health_check():
    # Check if Tor is working
    is_tor = await tor_integration.verify_tor_connection(connection_id)
    
    # Check exit node
    exit_node = await tor_integration.get_exit_node(connection_id)
    
    # Check connection status
    status = tor_integration.get_status()
    
    return {
        "tor_working": is_tor,
        "exit_node": exit_node,
        "active_connections": status["active_connections"]
    }
```

## Security Considerations

### Connection Security
- All Tor connections are encrypted through the Tor network
- Circuit verification ensures actual Tor usage
- IP rotation prevents correlation attacks
- Exit node monitoring for security

### Privacy Protection
- No direct IP exposure
- Traffic analysis resistance
- Anonymous communication
- Circuit isolation

### Best Practices
- Use circuit verification
- Enable IP rotation
- Monitor exit nodes
- Regular health checks
- Keep Tor daemon updated

## Troubleshooting

### Common Issues

**Tor daemon not running**:
```bash
# Check Tor status
sudo systemctl status tor

# Start Tor
sudo systemctl start tor

# Check Tor logs
sudo tail -f /var/log/tor/notices.log
```

**SOCKS proxy connection failed**:
```bash
# Test SOCKS connection
curl --socks5 127.0.0.1:9050 http://check.torproject.org

# Check SOCKS port
netstat -tlnp | grep 9050
```

**Control port authentication failed**:
```bash
# Generate new password hash
tor --hash-password "your_password"

# Update torrc with new hash
echo "HashedControlPassword 16:NEW_HASH" >> /etc/tor/torrc
sudo systemctl restart tor
```

**Circuit creation failed**:
- Check internet connectivity
- Verify Tor daemon is running
- Check firewall settings
- Review Tor logs for errors

### Debug Commands

```bash
# Test Tor connectivity
curl --socks5 127.0.0.1:9050 http://check.torproject.org

# Check Tor circuits
echo "GETINFO circuit-status" | nc 127.0.0.1 9051

# Monitor Tor traffic
sudo tcpdump -i lo port 9050

# Check Tor configuration
tor --verify-config
```

## Performance Optimization

### Connection Pooling
- Reuse Tor connections when possible
- Implement connection pooling
- Monitor connection health
- Automatic reconnection

### Circuit Management
- Optimize circuit creation
- Monitor circuit health
- Automatic circuit refresh
- Exit node selection

### Resource Usage
- Monitor memory usage
- Optimize connection limits
- Regular cleanup
- Resource monitoring

## Future Enhancements

- **QUIC over Tor**: Support for QUIC protocol over Tor
- **Tor v3**: Support for next-generation Tor protocol
- **Advanced Circuit Management**: ML-based circuit selection
- **Performance Analytics**: Detailed performance metrics
- **Multi-hop Support**: Custom multi-hop configurations

---

The Tor integration provides a robust foundation for anonymous relay connections with multiple package support, transparent integration, and comprehensive security features.
