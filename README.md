# secIRC - Anonymous Censorship-Resistant Messaging System

A completely anonymous, censorship-resistant messaging system with separated client-server architecture. Features multi-challenge authentication, end-to-end encryption, and distributed relay network. Messages are encrypted and relay servers don't store metadata about origin or destination. The system can bypass any kind of censorship through its distributed relay network with transparent Tor integration.

## 🚀 Quick Start

### Automatic Setup (Recommended)
When opening this project in Cursor AI, the environment will be automatically configured. If you need to manually set up:

```bash
# Run the setup script
./scripts/setup.sh

# Activate the development environment
./scripts/activate.sh
```

### Manual Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Edit as needed
```

## 🛠️ Development

### Available Commands
- **Start secIRC Server**: `python src/server/secirc_server.py`
- **Start secIRC Client**: `python src/client/secirc_client.py`
- **Test Authentication Flow**: `python scripts/test_client_server_auth.py`
- **Test Relay Connections**: `python scripts/test_relay_connections.py`
- **Test Tor Integration**: `python scripts/test_tor_integration.py`
- **Run All Tests**: `pytest`
- **Format Code**: `black src/ tests/`
- **Lint Code**: `flake8 src/ tests/`
- **Type Check**: `mypy src/`

### VS Code/Cursor Integration
The project includes comprehensive VS Code/Cursor configuration:
- **Python Interpreter**: Automatically set to project virtual environment
- **Debugging**: Pre-configured launch configurations for server and client
- **Tasks**: Built-in tasks for common development operations
- **Extensions**: Recommended extensions for optimal development experience

### Project Structure
```
secIRC/
├── src/                    # Source code
│   ├── server/            # secIRC server implementation
│   │   └── secirc_server.py        # Main server with authentication
│   ├── client/            # secIRC client implementation
│   │   └── secirc_client.py        # Main client with authentication
│   ├── protocol/          # Shared protocol implementations
│   │   ├── authentication.py       # Multi-challenge authentication
│   │   ├── user_status.py          # User status and message delivery
│   │   ├── relay_connections.py    # Multi-protocol relay connections
│   │   ├── tor_integration.py      # Transparent Tor proxy integration
│   │   ├── encryption.py           # End-to-end encryption
│   │   ├── message_types.py        # Message structures
│   │   ├── pubsub_server.py        # Group messaging system
│   │   ├── decentralized_groups.py # Decentralized group management
│   │   ├── torrent_discovery.py    # Torrent-inspired relay discovery
│   │   ├── relay_verification.py   # Relay verification system
│   │   ├── mesh_network.py         # Mesh network topology
│   │   ├── ring_management.py      # First ring management
│   │   ├── key_rotation.py         # Key rotation system
│   │   ├── salt_protection.py      # Message integrity protection
│   │   ├── anti_mitm.py            # Anti-MITM protection
│   │   ├── relay_authentication.py # Relay authentication
│   │   ├── network_monitoring.py   # Network monitoring
│   │   └── trust_system.py         # Trust and reputation system
│   └── security/          # Security and encryption modules
├── clients/               # Mobile client implementations
│   ├── android/          # Android client (Kotlin + Jetpack Compose)
│   └── ios/              # iOS client (Swift + SwiftUI)
├── config/                # Configuration files
│   ├── relay_connections.yaml      # Relay connection configuration
│   ├── server.yaml        # Server configuration
│   ├── client.yaml        # Client configuration
│   └── security.yaml      # Security settings
├── tests/                 # Test files
├── scripts/               # Setup and utility scripts
│   ├── test_client_server_auth.py  # Authentication flow tests
│   ├── test_relay_connections.py   # Relay connection tests
│   └── test_tor_integration.py     # Tor integration tests
└── .vscode/              # VS Code/Cursor configuration
```

## 🔧 Configuration

### Environment Variables
Key environment variables (see `.env` file):
- `SECIRC_ENV`: Environment (development/production)
- `SECIRC_DEBUG`: Enable debug mode
- `SECIRC_UDP_PORT`: UDP port for anonymous messaging (default: 6667)
- `SECIRC_MAX_PACKET_SIZE`: Maximum UDP packet size (default: 1400)
- `SECIRC_SECRET_KEY`: Secret key for encryption
- `SECIRC_ENCRYPTION_KEY`: Encryption key for private keys

### Security Features
- **Multi-challenge authentication**: Cryptographic, proof-of-work, timestamp, and nonce challenges
- **End-to-end encryption**: Messages encrypted with recipient's public key
- **Transparent Tor integration**: Multiple Tor packages with automatic fallback
- **Group messaging**: Secure group communication with decentralized management
- **Anonymous routing**: Messages routed through random relay chains
- **No metadata storage**: Relay servers don't store origin/destination info
- **Password-protected keys**: Private keys encrypted with strong passwords
- **Perfect forward secrecy**: Session keys rotated regularly
- **Traffic analysis resistance**: Dummy traffic and message padding
- **Censorship resistance**: Distributed relay network with Tor support
- **Anti-MITM protection**: Multi-layer protection against man-in-the-middle attacks
- **Relay verification**: Comprehensive verification of relay servers
- **Trust system**: Reputation-based trust management
- **User status management**: Real-time presence tracking and message delivery

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_server.py
```

## 📦 Dependencies

### Core Framework
- **Pydantic**: Data validation and settings management
- **Asyncio**: Asynchronous programming support

### Network & Communication
- **asyncio-dgram**: Asynchronous UDP communication
- **aiohttp**: Asynchronous HTTP client for relay discovery
- **dnspython**: DNS-based relay discovery
- **websockets**: WebSocket support for relay connections

### Security & Cryptography
- **Cryptography**: Cryptographic recipes and primitives
- **PyCryptodome**: Additional cryptographic functions
- **PyNaCl**: Modern cryptographic library
- **Argon2**: Memory-hard password hashing

### Tor Integration
- **PySocks**: SOCKS5 proxy support for Tor connections
- **tor-proxy**: Transparent Tor proxy integration
- **torpy**: Pure Python Tor protocol implementation
- **stem**: Tor controller library for advanced management

### Anonymous Network
- **requests**: HTTP requests for web discovery
- **beautifulsoup4**: Web scraping for relay discovery
- **scapy**: Network packet analysis
- **bencodepy**: BitTorrent protocol support for relay discovery

### Development Tools
- **Pytest**: Testing framework
- **Black**: Code formatter
- **Flake8**: Linter
- **MyPy**: Static type checker

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **[🌐 Official Website](https://www.secirc.org)** - Main project page
- [Complete Documentation](docs/README.md)
- [System Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Security Model](docs/SECURITY_MODEL.md)
- [Installation Guide](docs/INSTALLATION.md)
- [User Manual](docs/USER_MANUAL.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Key Rotation System](docs/KEY_ROTATION.md)
- [PubSub Group Messaging](docs/PUBSUB_GROUP_MESSAGING.md)
- [Torrent Discovery System](docs/TORRENT_DISCOVERY.md)
- [Relay Verification System](docs/RELAY_VERIFICATION.md)
- [Security Protection](docs/SECURITY_PROTECTION.md)
- [Decentralized Groups](docs/DECENTRALIZED_GROUPS.md)

## 📱 Mobile Clients

- [Android Client](clients/android/README.md) - Android 5.0+ with Kotlin and Jetpack Compose
- [iOS Client](clients/ios/README.md) - iOS 15.0+ with Swift and SwiftUI
- [Mobile Clients Overview](clients/README.md) - Cross-platform mobile client documentation

## 🛡️ How It Works

### Client-Server Architecture
1. **Client Authentication**: Multi-challenge authentication with cryptographic verification
2. **Server Management**: User status tracking and message delivery coordination
3. **Shared Protocols**: Common authentication and communication protocols
4. **Relay Integration**: Server connects to relay network for message distribution

### Anonymous Messaging Protocol
1. **User Identity**: Each user has a unique ID and cryptographic keypair
2. **Authentication**: Multi-challenge authentication (cryptographic, proof-of-work, timestamp, nonce)
3. **Message Encryption**: Messages encrypted with recipient's public key
4. **Group Messaging**: Secure group communication with decentralized management
5. **Relay Discovery**: System discovers relay servers via torrent-inspired DHT and trackers
6. **Message Routing**: Messages routed through random chain of relay servers
7. **No Metadata**: Relay servers don't store origin/destination information
8. **Decryption**: Only recipient can decrypt messages with their private key
9. **User Status**: Real-time presence tracking and message delivery

### Censorship Resistance
- **Distributed Network**: No single point of failure
- **Relay Chains**: Messages pass through multiple servers
- **Multi-Protocol Support**: TCP, Tor, and WebSocket connections
- **Transparent Tor Integration**: Multiple Tor packages with automatic fallback
- **Dynamic Discovery**: New relay servers can be added automatically
- **Traffic Obfuscation**: Dummy traffic and message padding
- **Mesh Network**: First ring of trusted relays with automatic expansion
- **Torrent Discovery**: DHT and tracker-based relay discovery

### Security Features
- **Multi-Challenge Authentication**: Cryptographic, proof-of-work, timestamp, and nonce challenges
- **End-to-End Encryption**: Only sender and recipient can read messages
- **Group Encryption**: Shared group keys encrypted with each member's public key
- **Perfect Forward Secrecy**: Compromised keys don't affect past messages
- **Anonymous Routing**: No server knows both sender and recipient
- **Password Protection**: Private keys encrypted with strong passwords
- **Traffic Analysis Resistance**: Multiple layers of protection
- **Message Integrity**: Salt-based protection against tampering
- **Key Rotation**: Automatic key rotation for groups and relays
- **Relay Verification**: Comprehensive verification of relay servers
- **Anti-MITM Protection**: Multi-layer protection against attacks
- **User Status Management**: Real-time presence tracking and secure message delivery

## 📨 Group Messaging System

### How Group Messaging Works

The secIRC group messaging system solves the complex challenge of **group encryption** while maintaining end-to-end encryption:

#### **1. Group Key Management**
- **Shared Group Key**: Each group has a unique 256-bit encryption key
- **Individual Encryption**: Group key is encrypted separately with each member's public key
- **Key Distribution**: All members receive their own encrypted copy of the group key
- **Automatic Rotation**: Keys rotate when members join/leave or after 24 hours

#### **2. Message Flow**
```
1. User sends message to group
2. Server encrypts message with shared group key
3. Server distributes same encrypted message to all members
4. Each member receives:
   - Encrypted message (same for everyone)
   - Their encrypted copy of group key
5. Members decrypt group key with their private key
6. Members decrypt message with group key
```

#### **3. Security Benefits**
- **End-to-End Encryption**: Messages remain encrypted on servers
- **Perfect Forward Secrecy**: Old messages can't be decrypted with new keys
- **Access Control**: Only group members can decrypt messages
- **Message Integrity**: All messages are signed and verified
- **Automatic Cleanup**: Messages are deleted after delivery

#### **4. Group Operations**
- **Create Group**: Generate initial group key and add creator
- **Join Group**: Receive encrypted group key and participate
- **Leave Group**: Trigger key rotation to exclude user
- **Send Message**: Encrypt with group key and distribute
- **Receive Message**: Decrypt group key, then decrypt message

### Example Usage

```python
# Create a group
group_id = await pubsub_server.create_group(creator_id, {
    "name": "My Secure Group",
    "description": "Private group for secure communication"
})

# Join the group
await pubsub_server.join_group(group_id, user_id)

# Send a message
message_id = await pubsub_server.publish_message(
    group_id, sender_id, "Hello everyone!".encode()
)

# Messages are automatically:
# - Encrypted with group key
# - Distributed to all members
# - Decrypted by each member
# - Cleaned up after delivery
```

For detailed information, see [PubSub Group Messaging Documentation](docs/PUBSUB_GROUP_MESSAGING.md).

## 🔐 Authentication System

### Multi-Challenge Authentication

secIRC implements a robust multi-challenge authentication system that ensures secure client-server communication:

#### **Challenge Types**
1. **Cryptographic Challenge**: Requires user's private key to sign challenge data
2. **Proof of Work Challenge**: Requires computational work to solve (configurable difficulty)
3. **Timestamp Challenge**: Prevents replay attacks with time validation
4. **Nonce Challenge**: Ensures session uniqueness with random values

#### **Authentication Flow**
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

#### **Security Benefits**
- **Multi-layer verification**: Multiple independent challenges
- **Replay attack prevention**: Timestamp and nonce validation
- **Computational security**: Proof of work requirements
- **Cryptographic security**: Digital signature verification
- **Session management**: Automatic cleanup and expiration

### User Status Management

The system provides comprehensive user status management:

#### **Status Types**
- **Online**: User is active and available
- **Away**: User is inactive but reachable
- **Busy**: User is active but not available
- **Invisible**: User is online but appears offline
- **Offline**: User is not connected

#### **Message Delivery**
- **Online users**: Immediate message delivery
- **Offline users**: Message queuing with retry mechanism
- **Status updates**: Real-time presence broadcasting
- **Auto-away**: Automatic status changes based on activity

For detailed information, see [Authentication Documentation](docs/AUTHENTICATION.md).