# secIRC Developer Guide

## Overview

This guide provides comprehensive information for developers who want to contribute to secIRC, extend its functionality, or integrate it into other applications.

## 🏗️ Development Environment Setup

### Prerequisites

- **Python 3.8+**: Core development environment
- **Git**: Version control system
- **Virtual Environment**: Isolated Python environment
- **Code Editor**: VS Code, PyCharm, or similar
- **Testing Framework**: pytest for testing

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/secIRC.git
cd secIRC

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests to verify setup
pytest
```

### VS Code Configuration

The project includes VS Code configuration for optimal development:

- **Python Interpreter**: Automatically set to project virtual environment
- **Debugging**: Pre-configured launch configurations
- **Tasks**: Built-in tasks for common operations
- **Extensions**: Recommended extensions for development

## 📁 Project Structure

```
secIRC/
├── src/                    # Source code
│   ├── protocol/          # Core protocol implementation
│   │   ├── anonymous_protocol.py    # Main protocol handler
│   │   ├── encryption.py            # End-to-end encryption
│   │   ├── relay_discovery.py       # Relay discovery
│   │   ├── mesh_network.py          # Mesh networking
│   │   ├── key_rotation.py          # Key rotation system
│   │   ├── salt_protection.py       # Salt-based protection
│   │   ├── group_management.py      # Group management
│   │   ├── hash_identity_system.py  # Hash-based identities
│   │   ├── ring_management.py       # First ring management
│   │   ├── ring_expansion.py        # Ring expansion
│   │   └── message_types.py         # Message structures
│   ├── server/            # Relay server implementation
│   │   ├── relay_server.py          # Main server
│   │   └── main.py                  # Server entry point
│   ├── client/            # Client implementation
│   │   └── main.py                  # Client entry point
│   └── security/          # Security modules
│       ├── key_management.py        # Key management
│       └── authentication.py        # Authentication
├── config/                # Configuration files
│   ├── server.yaml        # Server configuration
│   ├── client.yaml        # Client configuration
│   └── security.yaml      # Security settings
├── tests/                 # Test files
│   ├── test_protocol.py   # Protocol tests
│   ├── test_server.py     # Server tests
│   ├── test_client.py     # Client tests
│   └── test_security.py   # Security tests
├── docs/                  # Documentation
├── scripts/               # Setup and utility scripts
└── web/                   # Web interface (if applicable)
```

## 🔧 Development Workflow

### Code Style

The project follows strict coding standards:

- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **PEP 8**: Python style guide

### Running Code Quality Checks

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type check
mypy src/

# Run all checks
./scripts/check_code.sh
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_protocol.py

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_protocol.py::test_message_encryption
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push branch
git push origin feature/new-feature

# Create pull request
# (via GitHub web interface)
```

## 🧩 Core Components

### Protocol Layer

The protocol layer handles the core anonymous messaging functionality:

#### AnonymousProtocol

```python
class AnonymousProtocol:
    """Main protocol handler for anonymous messaging."""
    
    def __init__(self, config: ProtocolConfig, identity_system: HashIdentitySystem, group_manager: GroupManager):
        self.config = config
        self.identity_system = identity_system
        self.group_manager = group_manager
        self.encryption = EndToEndEncryption()
        self.salt_protection = SaltProtectionSystem()
    
    async def send_message(self, recipient_hash: bytes, message: bytes, message_type: MessageType) -> bool:
        """Send an anonymous message to a recipient."""
        # Implementation details...
    
    async def receive_message(self, message_data: bytes) -> Optional[Message]:
        """Receive and process an incoming message."""
        # Implementation details...
```

#### Message Types

```python
class MessageType(Enum):
    """Types of messages in the anonymous protocol."""
    
    # User messages
    TEXT_MESSAGE = 0x01
    FILE_MESSAGE = 0x02
    VOICE_MESSAGE = 0x03
    
    # Group messages
    GROUP_TEXT_MESSAGE = 0x04
    GROUP_FILE_MESSAGE = 0x05
    GROUP_VOICE_MESSAGE = 0x06
    
    # Protocol messages
    HANDSHAKE = 0x10
    KEY_EXCHANGE = 0x11
    HEARTBEAT = 0x12
    
    # Error messages
    ERROR = 0xF0
    INVALID_MESSAGE = 0xF1
```

### Security Layer

The security layer provides cryptographic protection:

#### EndToEndEncryption

```python
class EndToEndEncryption:
    """Handles end-to-end encryption for messages."""
    
    @staticmethod
    def generate_keypair() -> Tuple[bytes, bytes]:
        """Generate a new RSA-2048 keypair."""
        # Implementation details...
    
    @staticmethod
    def encrypt_message(message: bytes, public_key: bytes) -> bytes:
        """Encrypt a message with a public key."""
        # Implementation details...
    
    @staticmethod
    def decrypt_message(encrypted_message: bytes, private_key: bytes) -> bytes:
        """Decrypt a message with a private key."""
        # Implementation details...
```

#### SaltProtectionSystem

```python
class SaltProtectionSystem:
    """Provides salt-based message integrity protection."""
    
    def create_salted_message(self, message_type: str, payload: bytes, salt_type: SaltType) -> SaltedMessage:
        """Create a salted message with integrity protection."""
        # Implementation details...
    
    def verify_salted_message(self, message: SaltedMessage) -> bool:
        """Verify the integrity of a salted message."""
        # Implementation details...
```

### Network Layer

The network layer handles communication:

#### MeshNetwork

```python
class MeshNetwork:
    """Manages the mesh network of relay servers."""
    
    def __init__(self, node_id: bytes, private_key: bytes, public_key: bytes):
        self.node_id = node_id
        self.private_key = private_key
        self.public_key = public_key
        self.known_nodes: Dict[bytes, RelayNode] = {}
        self.first_ring: Set[bytes] = set()
    
    async def start_mesh_network(self, bootstrap_nodes: List[Tuple[str, int]]) -> None:
        """Start the mesh network."""
        # Implementation details...
    
    async def send_message(self, target_id: bytes, message: bytes) -> bool:
        """Send a message through the mesh network."""
        # Implementation details...
```

## 🧪 Testing

### Test Structure

```
tests/
├── test_protocol.py       # Protocol layer tests
├── test_server.py         # Server tests
├── test_client.py         # Client tests
├── test_security.py       # Security tests
├── test_network.py        # Network tests
├── test_integration.py    # Integration tests
└── fixtures/              # Test fixtures
    ├── sample_messages.py
    ├── test_keys.py
    └── mock_network.py
```

### Writing Tests

#### Unit Tests

```python
import pytest
from src.protocol.encryption import EndToEndEncryption

class TestEndToEndEncryption:
    """Test end-to-end encryption functionality."""
    
    def test_generate_keypair(self):
        """Test keypair generation."""
        private_key, public_key = EndToEndEncryption.generate_keypair()
        
        assert len(private_key) > 0
        assert len(public_key) > 0
        assert private_key != public_key
    
    def test_encrypt_decrypt(self):
        """Test message encryption and decryption."""
        private_key, public_key = EndToEndEncryption.generate_keypair()
        message = b"Hello, World!"
        
        encrypted = EndToEndEncryption.encrypt_message(message, public_key)
        decrypted = EndToEndEncryption.decrypt_message(encrypted, private_key)
        
        assert decrypted == message
        assert encrypted != message
```

#### Integration Tests

```python
import pytest
import asyncio
from src.protocol import AnonymousProtocol, HashIdentitySystem, GroupManager

class TestAnonymousProtocol:
    """Test anonymous protocol integration."""
    
    @pytest.fixture
    async def protocol(self):
        """Create protocol instance for testing."""
        identity_system = HashIdentitySystem()
        group_manager = GroupManager()
        config = ProtocolConfig(
            server_id=b"test_server",
            private_key=b"test_private_key",
            public_key=b"test_public_key",
            udp_port=6667,
            max_packet_size=1400
        )
        
        protocol = AnonymousProtocol(config, identity_system, group_manager)
        await protocol.start()
        yield protocol
        await protocol.stop()
    
    async def test_send_receive_message(self, protocol):
        """Test sending and receiving messages."""
        recipient_hash = b"test_recipient"
        message_content = b"Test message"
        
        # Send message
        success = await protocol.send_message(recipient_hash, message_content, MessageType.TEXT_MESSAGE)
        assert success
        
        # Receive message (simulated)
        message_data = b"simulated_message_data"
        received_message = await protocol.receive_message(message_data)
        assert received_message is not None
```

### Test Fixtures

```python
# tests/fixtures/sample_messages.py
import pytest
from src.protocol.message_types import Message, MessageType

@pytest.fixture
def sample_message():
    """Create a sample message for testing."""
    return Message(
        message_type=MessageType.TEXT_MESSAGE,
        sender_hash=b"sender_hash",
        recipient_hash=b"recipient_hash",
        content=b"Hello, World!",
        timestamp=1234567890,
        sequence_number=1,
        signature=b"signature"
    )

@pytest.fixture
def sample_encrypted_message():
    """Create a sample encrypted message for testing."""
    return b"encrypted_message_data"
```

## 🔧 Extending secIRC

### Adding New Message Types

1. **Define Message Type**:

```python
# In src/protocol/message_types.py
class MessageType(Enum):
    # Existing types...
    CUSTOM_MESSAGE = 0x50  # New message type
```

2. **Implement Handler**:

```python
# In src/protocol/anonymous_protocol.py
async def _handle_custom_message(self, message: Message) -> None:
    """Handle custom message type."""
    # Implementation details...
```

3. **Add Tests**:

```python
# In tests/test_protocol.py
def test_custom_message():
    """Test custom message handling."""
    # Test implementation...
```

### Adding New Security Features

1. **Create Security Module**:

```python
# src/security/new_security_feature.py
class NewSecurityFeature:
    """New security feature implementation."""
    
    def __init__(self):
        # Initialization...
    
    def apply_security(self, data: bytes) -> bytes:
        """Apply security feature to data."""
        # Implementation...
```

2. **Integrate with Protocol**:

```python
# In src/protocol/anonymous_protocol.py
from ..security.new_security_feature import NewSecurityFeature

class AnonymousProtocol:
    def __init__(self, ...):
        # Existing initialization...
        self.new_security = NewSecurityFeature()
```

3. **Add Configuration**:

```yaml
# config/security.yaml
new_security:
  enabled: true
  parameters:
    param1: value1
    param2: value2
```

### Adding New Network Features

1. **Create Network Module**:

```python
# src/network/new_network_feature.py
class NewNetworkFeature:
    """New network feature implementation."""
    
    async def start(self) -> None:
        """Start the network feature."""
        # Implementation...
    
    async def stop(self) -> None:
        """Stop the network feature."""
        # Implementation...
```

2. **Integrate with Server**:

```python
# In src/server/relay_server.py
from ..network.new_network_feature import NewNetworkFeature

class RelayServer:
    def __init__(self):
        # Existing initialization...
        self.new_network = NewNetworkFeature()
    
    async def start(self):
        # Existing startup...
        await self.new_network.start()
```

## 📊 Performance Optimization

### Profiling

```bash
# Install profiling tools
pip install line_profiler memory_profiler

# Profile code
python -m line_profiler src/protocol/anonymous_protocol.py

# Memory profiling
python -m memory_profiler src/protocol/anonymous_protocol.py
```

### Optimization Techniques

1. **Async/Await**: Use async/await for I/O operations
2. **Connection Pooling**: Reuse connections when possible
3. **Caching**: Cache frequently accessed data
4. **Batch Operations**: Batch multiple operations together
5. **Lazy Loading**: Load data only when needed

### Performance Testing

```python
import time
import asyncio
from src.protocol import AnonymousProtocol

async def performance_test():
    """Test protocol performance."""
    protocol = AnonymousProtocol(...)
    await protocol.start()
    
    # Test message sending performance
    start_time = time.time()
    for i in range(1000):
        await protocol.send_message(recipient_hash, f"Message {i}".encode(), MessageType.TEXT_MESSAGE)
    end_time = time.time()
    
    print(f"Sent 1000 messages in {end_time - start_time:.2f} seconds")
    print(f"Average: {(end_time - start_time) / 1000 * 1000:.2f} ms per message")
```

## 🔍 Debugging

### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Get logger
logger = logging.getLogger('secIRC')

# Log messages
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Debugging Tools

```bash
# Install debugging tools
pip install ipdb pudb

# Use debugger
import ipdb; ipdb.set_trace()

# Or use pudb
import pudb; pudb.set_trace()
```

### Common Debugging Scenarios

1. **Message Not Sending**: Check network connectivity and relay status
2. **Encryption Errors**: Verify key generation and exchange
3. **Performance Issues**: Profile code and identify bottlenecks
4. **Memory Leaks**: Use memory profiler to identify leaks

## 📚 Documentation

### Code Documentation

```python
def send_message(self, recipient_hash: bytes, message: bytes, message_type: MessageType) -> bool:
    """
    Send an anonymous message to a recipient.
    
    Args:
        recipient_hash: Hash identifier of the recipient
        message: Message content to send
        message_type: Type of message being sent
        
    Returns:
        bool: True if message was sent successfully, False otherwise
        
    Raises:
        EncryptionError: If message encryption fails
        NetworkError: If network communication fails
        
    Example:
        >>> success = await protocol.send_message(
        ...     recipient_hash=b"recipient_hash",
        ...     message=b"Hello, World!",
        ...     message_type=MessageType.TEXT_MESSAGE
        ... )
        >>> print(success)
        True
    """
    # Implementation...
```

### API Documentation

Use docstrings and type hints for comprehensive API documentation:

```python
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class Message:
    """Represents an anonymous message."""
    
    message_type: MessageType
    sender_hash: bytes
    recipient_hash: bytes
    content: bytes
    timestamp: int
    sequence_number: int
    signature: bytes
    
    def to_bytes(self) -> bytes:
        """Serialize message to bytes."""
        # Implementation...
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "Message":
        """Deserialize message from bytes."""
        # Implementation...
```

## 🚀 Contributing

### Contribution Guidelines

1. **Fork Repository**: Fork the repository on GitHub
2. **Create Branch**: Create a feature branch
3. **Make Changes**: Implement your changes
4. **Add Tests**: Add tests for your changes
5. **Run Checks**: Run all code quality checks
6. **Submit PR**: Submit a pull request

### Code Review Process

1. **Automated Checks**: All PRs must pass automated checks
2. **Code Review**: At least one reviewer must approve
3. **Testing**: All tests must pass
4. **Documentation**: Update documentation if needed
5. **Merge**: Merge after approval

### Issue Reporting

When reporting issues:

1. **Check Existing Issues**: Search for similar issues
2. **Provide Details**: Include system info, error messages, steps to reproduce
3. **Add Labels**: Use appropriate labels
4. **Follow Template**: Use the issue template

---

This developer guide provides comprehensive information for contributing to secIRC. For more specific information, refer to the individual module documentation and the API reference.
