# secIRC - Anonymous Censorship-Resistant Messaging System

A completely anonymous, censorship-resistant messaging system using UDP with relay servers. Messages are end-to-end encrypted and relay servers don't store metadata about origin or destination. The system can bypass any kind of censorship through its distributed relay network.

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
- **Start Relay Server**: `python src/server/main.py`
- **Start Anonymous Client**: `python src/client/main.py`
- **Run Tests**: `pytest`
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
│   ├── server/            # Relay server implementation
│   ├── client/            # Anonymous client implementation
│   ├── protocol/          # Anonymous messaging protocol
│   │   ├── anonymous_protocol.py    # Main protocol handler
│   │   ├── encryption.py            # End-to-end encryption
│   │   ├── relay_discovery.py       # Relay server discovery
│   │   ├── message_types.py         # Message structures
│   │   ├── pubsub_server.py         # Group messaging system
│   │   ├── group_encryption.py      # Group encryption/decryption
│   │   ├── decentralized_groups.py  # Decentralized group management
│   │   ├── torrent_discovery.py     # Torrent-inspired relay discovery
│   │   ├── relay_verification.py    # Relay verification system
│   │   ├── mesh_network.py          # Mesh network topology
│   │   ├── ring_management.py       # First ring management
│   │   ├── key_rotation.py          # Key rotation system
│   │   ├── salt_protection.py       # Message integrity protection
│   │   ├── anti_mitm.py             # Anti-MITM protection
│   │   ├── relay_authentication.py  # Relay authentication
│   │   ├── network_monitoring.py    # Network monitoring
│   │   └── trust_system.py          # Trust and reputation system
│   └── security/          # Security and encryption modules
├── clients/               # Mobile client implementations
│   ├── android/          # Android client (Kotlin + Jetpack Compose)
│   └── ios/              # iOS client (Swift + SwiftUI)
├── config/                # Configuration files
│   ├── server.yaml        # Relay server configuration
│   ├── client.yaml        # Client configuration
│   └── security.yaml      # Security settings
├── tests/                 # Test files
├── scripts/               # Setup and utility scripts
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
- **End-to-end encryption**: Messages encrypted with recipient's public key
- **Group messaging**: Secure group communication with shared keys
- **Anonymous routing**: Messages routed through random relay chains
- **No metadata storage**: Relay servers don't store origin/destination info
- **Password-protected keys**: Private keys encrypted with strong passwords
- **Perfect forward secrecy**: Session keys rotated regularly
- **Traffic analysis resistance**: Dummy traffic and message padding
- **Censorship resistance**: Distributed relay network
- **Anti-MITM protection**: Multi-layer protection against man-in-the-middle attacks
- **Relay verification**: Comprehensive verification of relay servers
- **Trust system**: Reputation-based trust management

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

### Security & Cryptography
- **Cryptography**: Cryptographic recipes and primitives
- **PyCryptodome**: Additional cryptographic functions
- **PyNaCl**: Modern cryptographic library
- **Argon2**: Memory-hard password hashing

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

### Anonymous Messaging Protocol
1. **User Identity**: Each user has a unique ID and cryptographic keypair
2. **Message Encryption**: Messages encrypted with recipient's public key
3. **Group Messaging**: Secure group communication with shared encryption keys
4. **Relay Discovery**: System discovers relay servers via torrent-inspired DHT and trackers
5. **Message Routing**: Messages routed through random chain of relay servers
6. **No Metadata**: Relay servers don't store origin/destination information
7. **Decryption**: Only recipient can decrypt messages with their private key
8. **Group Decryption**: Group members decrypt shared group key, then decrypt messages

### Censorship Resistance
- **Distributed Network**: No single point of failure
- **Relay Chains**: Messages pass through multiple servers
- **UDP Protocol**: Harder to block than TCP connections
- **Dynamic Discovery**: New relay servers can be added automatically
- **Traffic Obfuscation**: Dummy traffic and message padding
- **Mesh Network**: First ring of trusted relays with automatic expansion
- **Torrent Discovery**: DHT and tracker-based relay discovery

### Security Features
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