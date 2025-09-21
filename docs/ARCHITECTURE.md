# secIRC Architecture Documentation

## Overview

secIRC is a completely anonymous, censorship-resistant messaging system with a separated client-server architecture. The system features multi-challenge authentication, transparent Tor integration, and a distributed relay network.

## System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   secIRC Client │    │   secIRC Server │    │  Relay Network  │
│                 │    │                 │    │                 │
│ • Authentication│◄──►│ • User Status   │◄──►│ • Message Relay │
│ • Message Send  │    │ • Message Queue │    │ • Tor Support   │
│ • Contact Mgmt  │    │ • Relay Sync    │    │ • Multi-Protocol│
│ • Key Storage   │    │ • Auth Verify   │    │ • DHT Discovery │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Overview

#### 1. Client Components (`src/client/`)
- **`secirc_client.py`**: Main client implementation
  - User authentication and session management
  - Message composition and encryption
  - Contact management and public key exchange
  - Status management (online, away, busy, invisible)
  - Background task management

#### 2. Server Components (`src/server/`)
- **`secirc_server.py`**: Main server implementation
  - User authentication and session verification
  - User status tracking and presence management
  - Message delivery coordination
  - Relay network integration
  - Statistics and monitoring

#### 3. Shared Protocol Components (`src/protocol/`)
- **`authentication.py`**: Multi-challenge authentication system
- **`user_status.py`**: User presence and message delivery
- **`relay_connections.py`**: Multi-protocol relay connections
- **`tor_integration.py`**: Transparent Tor proxy integration
- **`encryption.py`**: End-to-end encryption
- **`message_types.py`**: Message structures and types

## Authentication System

### Multi-Challenge Authentication Flow

```
Client                    Server
  |                         |
  |---- Auth Request ------>|
  |<--- Auth Challenges ----|
  |---- Auth Responses ---->|
  |<--- Auth Success -------|
  |                         |
  |---- User Online ------->|
  |<--- Status Confirmed ---|
```

### Challenge Types

1. **Cryptographic Challenge**: Verify user's private key ownership
2. **Proof of Work Challenge**: Prevent brute force attacks
3. **Timestamp Challenge**: Prevent replay attacks
4. **Nonce Challenge**: Ensure session uniqueness

## User Status Management

### Status Types
- **Online**: User is active and available
- **Away**: User is inactive but reachable
- **Busy**: User is active but not available
- **Invisible**: User is online but appears offline
- **Offline**: User is not connected

### Message Delivery System
- **Online users**: Messages delivered immediately
- **Offline users**: Messages queued for later delivery
- **Retry mechanism**: Configurable attempts with expiration

## Relay Network Integration

### Multi-Protocol Support
1. **TCP Connections**: Standard TCP with SSL/TLS support
2. **Tor Integration**: Multiple Tor packages with automatic fallback
3. **WebSocket Connections**: Real-time bidirectional communication

### Relay Discovery
- **DHT (Distributed Hash Table)**: Kademlia-based peer discovery
- **Tracker Protocol**: HTTP/UDP tracker support
- **Peer Exchange (PEX)**: Direct peer information exchange
- **Bootstrap Nodes**: Initial relay discovery

## Security Features

### End-to-End Encryption
- Messages encrypted with recipient's public key
- Only recipient can decrypt with private key
- Perfect forward secrecy with key rotation

### Anti-MITM Protection
- Multi-layer authentication
- Relay verification
- Traffic analysis resistance
- No metadata storage

## Testing

### Test Scripts
- **Authentication Testing**: `python scripts/test_client_server_auth.py`
- **Relay Connection Testing**: `python scripts/test_relay_connections.py`
- **Tor Integration Testing**: `python scripts/test_tor_integration.py`

## Deployment

### Server Deployment
```bash
python src/server/secirc_server.py
```

### Client Deployment
```bash
python src/client/secirc_client.py
```

### Mobile Clients
- **Android**: Kotlin + Jetpack Compose
- **iOS**: Swift + SwiftUI

## Security Considerations

### Threat Model
- Man-in-the-middle attacks
- Traffic analysis
- Relay server compromise
- Client device compromise
- Network censorship

### Mitigation Strategies
- Multi-challenge authentication
- End-to-end encryption
- Tor integration
- Distributed relay network
- No metadata storage

## Conclusion

secIRC provides a robust, secure, and anonymous messaging system with a clear separation between client and server components. The multi-challenge authentication system ensures secure communication, while the distributed relay network provides censorship resistance.