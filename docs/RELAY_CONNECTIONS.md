# secIRC Relay Connection System

## Overview

The secIRC relay connection system enables relay servers to connect to each other using multiple protocols, ensuring robust and censorship-resistant communication. Each relay server maintains a configurable number of connections to other relays using TCP, Tor protocol, and WebSocket connections.

## Features

### Multi-Protocol Support
- **TCP Connections**: Direct server-to-server communication
- **Tor Protocol**: Anonymous connections through Tor network
- **WebSocket**: Web-based relay connections with real-time communication

### Connection Management
- **Configurable Limits**: Set minimum and maximum number of connections
- **Automatic Reconnection**: Failed connections are automatically retried
- **Load Balancing**: Distribute traffic across available connections
- **Health Monitoring**: Continuous monitoring of connection health and performance

### Security Features
- **SSL/TLS Encryption**: All connections can be encrypted
- **Authentication**: Mutual authentication between relay servers
- **Connection Verification**: Verify connection integrity and authenticity
- **Key Rotation**: Periodic rotation of connection keys

## Architecture

### Core Components

#### RelayConnectionManager
The main class that manages all relay connections:

```python
from protocol.relay_connections import RelayConnectionManager, ConnectionConfig

# Create configuration
config = ConnectionConfig(
    max_connections=10,
    min_connections=3,
    enable_tcp=True,
    enable_tor=True,
    enable_websocket=True
)

# Create connection manager
connection_manager = RelayConnectionManager(config, encryption)
```

#### Connection Types

**TCP Connections**
- Direct server-to-server communication
- Low latency, high bandwidth
- Requires direct network access
- Port: 6667 (configurable)

**Tor Connections**
- Anonymous connections through Tor network
- High privacy, medium latency
- Requires Tor daemon running
- SOCKS proxy on port 9050

**WebSocket Connections**
- Real-time bidirectional communication
- Works through firewalls and proxies
- HTTP/HTTPS compatible
- Port: 8080 (configurable)

### Connection Lifecycle

1. **Connection Initiation**
   - Add relay connection with specific protocol
   - Connection manager attempts to establish connection
   - Authentication process begins

2. **Authentication**
   - Exchange public keys
   - Verify relay identity
   - Establish encrypted channel

3. **Active Communication**
   - Send/receive messages
   - Heartbeat monitoring
   - Performance tracking

4. **Connection Maintenance**
   - Automatic reconnection on failure
   - Load balancing across connections
   - Health monitoring and reporting

## Configuration

### Connection Parameters

```yaml
connection_manager:
  # Connection limits
  max_connections: 10          # Maximum number of relay connections
  min_connections: 3           # Minimum number of relay connections
  connection_timeout: 30       # Connection timeout in seconds
  heartbeat_interval: 60       # Heartbeat interval in seconds
  reconnect_interval: 30       # Reconnect interval in seconds
  max_retry_attempts: 3        # Maximum retry attempts per connection
  retry_delay: 30              # Delay between retry attempts in seconds

  # Protocol settings
  enable_tcp: true             # Enable TCP connections
  enable_tor: true             # Enable Tor protocol connections
  enable_websocket: true       # Enable WebSocket connections

  # Port configurations
  tcp_port: 6667               # Default TCP port for relay connections
  websocket_port: 8080         # Default WebSocket port
  tor_socks_port: 9050         # Tor SOCKS proxy port

  # SSL/TLS settings
  ssl_enabled: true            # Enable SSL/TLS encryption
  ssl_cert_path: "config/ssl/relay.crt"
  ssl_key_path: "config/ssl/relay.key"
```

### Priority Levels

Connections are prioritized based on their type and reliability:

- **First Ring (10)**: Trusted first ring relay servers
- **Trusted Relays (8)**: Verified and trusted relays
- **Verified Relays (6)**: Relays that have passed verification
- **Discovered Relays (4)**: Newly discovered relays
- **Untrusted Relays (2)**: Relays with unknown reputation

## Usage Examples

### Basic Setup

```python
import asyncio
from protocol.relay_connections import RelayConnectionManager, ConnectionConfig, ConnectionType
from protocol.encryption import EndToEndEncryption

async def setup_relay_connections():
    # Initialize encryption
    encryption = EndToEndEncryption()
    
    # Configure connections
    config = ConnectionConfig(
        max_connections=10,
        min_connections=3,
        enable_tcp=True,
        enable_tor=True,
        enable_websocket=True
    )
    
    # Create connection manager
    connection_manager = RelayConnectionManager(config, encryption)
    
    # Start connection manager
    await connection_manager.start_connection_manager()
    
    # Add relay connections
    await connection_manager.add_relay_connection(
        relay_id=b"relay_1",
        connection_type=ConnectionType.TCP,
        host="relay1.secirc.net",
        port=6667,
        priority=8
    )
    
    return connection_manager
```

### Adding Different Connection Types

```python
# Add TCP connection
await connection_manager.add_relay_connection(
    relay_id=b"tcp_relay",
    connection_type=ConnectionType.TCP,
    host="relay.example.com",
    port=6667,
    priority=8
)

# Add WebSocket connection
await connection_manager.add_relay_connection(
    relay_id=b"ws_relay",
    connection_type=ConnectionType.WEBSOCKET,
    host="relay.example.com",
    port=8080,
    priority=7
)

# Add Tor connection
await connection_manager.add_relay_connection(
    relay_id=b"tor_relay",
    connection_type=ConnectionType.TOR,
    host="relay.onion",
    port=6667,
    priority=6
)
```

### Sending Messages

```python
# Send message to specific relay
message = {
    "type": "relay_message",
    "content": "Hello from relay",
    "timestamp": int(time.time())
}

success = await connection_manager.send_message_to_relay(
    relay_id=b"target_relay",
    message=message
)

# Broadcast message to all connected relays
sent_count = await connection_manager.broadcast_message(message)
print(f"Sent to {sent_count} relays")
```

### Monitoring Connections

```python
# Get connection status
status = connection_manager.get_connection_status()
print(f"Active connections: {status['active_connections']}")
print(f"Failed connections: {status['failed_connections']}")

# Get available connections
available = connection_manager.get_available_connections()
for conn in available:
    print(f"Relay {conn.relay_id.hex()}: {conn.connection_type.value}://{conn.host}:{conn.port}")
```

## Protocol Details

### TCP Protocol

TCP connections provide direct, low-latency communication between relay servers:

```
Client                    Server
  |                         |
  |---- TCP Connect ------->|
  |<--- Connection OK ------|
  |                         |
  |---- Auth Request ------>|
  |<--- Auth Challenge -----|
  |---- Auth Response ----->|
  |<--- Auth Success -------|
  |                         |
  |---- Messages ---------->|
  |<--- Messages -----------|
```

### Tor Protocol

Tor connections route traffic through the Tor network for anonymity:

```
Client                    Tor Network                    Server
  |                         |                             |
  |---- SOCKS Connect ----->|                             |
  |<--- SOCKS OK -----------|                             |
  |                         |                             |
  |---- Tor Circuit ------->|---- Tor Circuit ----------->|
  |                         |                             |
  |---- Auth Request ------>|---- Auth Request ---------->|
  |<--- Auth Challenge -----|<--- Auth Challenge ---------|
  |---- Auth Response ----->|---- Auth Response --------->|
  |<--- Auth Success -------|<--- Auth Success -----------|
  |                         |                             |
  |---- Messages ---------->|---- Messages -------------->|
  |<--- Messages -----------|<--- Messages ---------------|
```

### WebSocket Protocol

WebSocket connections provide real-time bidirectional communication:

```
Client                    Server
  |                         |
  |---- WS Connect -------->|
  |<--- Connection OK ------|
  |                         |
  |---- Auth Request ------>|
  |<--- Auth Challenge -----|
  |---- Auth Response ----->|
  |<--- Auth Success -------|
  |                         |
  |<==== WebSocket Messages ====>|
```

## Security Considerations

### Connection Security
- All connections support SSL/TLS encryption
- Mutual authentication between relay servers
- Connection integrity verification
- Protection against man-in-the-middle attacks

### Privacy Protection
- Tor connections provide anonymity
- No metadata storage on relay servers
- Encrypted message routing
- Traffic analysis resistance

### Network Resilience
- Multiple connection protocols
- Automatic failover and reconnection
- Load balancing across connections
- Distributed network topology

## Performance Optimization

### Connection Pooling
- Maintain optimal number of connections
- Automatic connection scaling
- Load balancing across available connections
- Priority-based connection selection

### Latency Optimization
- TCP for low-latency requirements
- WebSocket for real-time communication
- Tor for privacy-critical scenarios
- Connection quality monitoring

### Bandwidth Management
- Bandwidth-aware connection selection
- Traffic shaping and prioritization
- Compression for WebSocket connections
- Efficient message routing

## Monitoring and Debugging

### Connection Monitoring
```python
# Get detailed connection status
status = connection_manager.get_connection_status()
print(f"Connection Statistics:")
print(f"  Total: {status['total_connections']}")
print(f"  Active: {status['active_connections']}")
print(f"  Failed: {status['failed_connections']}")
print(f"  Messages Sent: {status['stats']['total_messages_sent']}")
print(f"  Messages Received: {status['stats']['total_messages_received']}")
```

### Logging
The system provides comprehensive logging for debugging:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Connection events are logged automatically
# - Connection attempts
# - Authentication results
# - Message transmission
# - Error conditions
```

### Health Checks
```python
# Check connection health
for connection in connection_manager.get_available_connections():
    print(f"Relay {connection.relay_id.hex()}:")
    print(f"  Status: {connection.status}")
    print(f"  Latency: {connection.latency}ms")
    print(f"  Last Seen: {connection.last_seen}")
    print(f"  Authenticated: {connection.is_authenticated}")
```

## Troubleshooting

### Common Issues

**Connection Failures**
- Check network connectivity
- Verify relay server availability
- Check firewall settings
- Verify SSL certificates

**Tor Connection Issues**
- Ensure Tor daemon is running
- Check SOCKS proxy configuration
- Verify .onion addresses
- Check Tor circuit status

**WebSocket Connection Issues**
- Check WebSocket server availability
- Verify SSL/TLS configuration
- Check proxy settings
- Verify WebSocket protocol version

### Debug Commands

```bash
# Test TCP connection
telnet relay.example.com 6667

# Test WebSocket connection
wscat -c ws://relay.example.com:8080/relay

# Test Tor connection
curl --socks5 127.0.0.1:9050 http://relay.onion:6667
```

## Best Practices

### Configuration
- Set appropriate connection limits based on server capacity
- Enable SSL/TLS for all connections
- Use priority levels to manage connection quality
- Configure appropriate timeouts and retry limits

### Security
- Regularly rotate connection keys
- Monitor connection authentication
- Use Tor for privacy-critical connections
- Implement connection verification

### Performance
- Monitor connection latency and bandwidth
- Balance connections across protocols
- Use connection pooling effectively
- Implement proper error handling

### Maintenance
- Regular health checks
- Monitor connection statistics
- Update relay server lists
- Maintain SSL certificates

## Integration

### With Relay Server
```python
from server.relay_server import RelayServer

# The relay server automatically uses the connection manager
server = RelayServer("config/relay_connections.yaml")
await server.start_server()
```

### With Client Applications
```python
# Clients can connect to relay servers using any supported protocol
# The connection manager handles protocol selection automatically
```

## Future Enhancements

- **QUIC Protocol Support**: For improved performance and security
- **Connection Multiplexing**: Multiple streams over single connection
- **Advanced Load Balancing**: ML-based connection selection
- **Connection Analytics**: Detailed performance metrics
- **Auto-scaling**: Dynamic connection management based on load

---

The relay connection system provides a robust foundation for building a distributed, censorship-resistant messaging network with multiple communication protocols and comprehensive security features.
