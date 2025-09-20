# secIRC API Reference

## Overview

This document provides comprehensive API documentation for the secIRC anonymous messaging system.

## 🔧 Core API Classes

### AnonymousProtocol

The main protocol handler for anonymous messaging.

```python
class AnonymousProtocol:
    def __init__(self, config: ProtocolConfig, identity_system: HashIdentitySystem, group_manager: GroupManager):
        """Initialize the anonymous protocol handler."""
    
    async def start(self) -> None:
        """Start the protocol handler."""
    
    async def stop(self) -> None:
        """Stop the protocol handler."""
    
    async def send_message(self, recipient_hash: bytes, message: bytes, message_type: MessageType) -> bool:
        """Send an anonymous message to a recipient."""
    
    async def receive_message(self, message_data: bytes) -> Optional[Message]:
        """Receive and process an incoming message."""
```

### EndToEndEncryption

Handles end-to-end encryption for messages.

```python
class EndToEndEncryption:
    @staticmethod
    def generate_keypair() -> Tuple[bytes, bytes]:
        """Generate a new RSA-2048 keypair."""
    
    @staticmethod
    def encrypt_message(message: bytes, public_key: bytes) -> bytes:
        """Encrypt a message with a public key."""
    
    @staticmethod
    def decrypt_message(encrypted_message: bytes, private_key: bytes) -> bytes:
        """Decrypt a message with a private key."""
    
    @staticmethod
    def sign_message(message: bytes, private_key: bytes) -> bytes:
        """Sign a message with a private key."""
    
    @staticmethod
    def verify_signature(message: bytes, signature: bytes, public_key: bytes) -> bool:
        """Verify a message signature."""
```

### MeshNetwork

Manages the mesh network of relay servers.

```python
class MeshNetwork:
    def __init__(self, node_id: bytes, private_key: bytes, public_key: bytes):
        """Initialize mesh network."""
    
    async def start_mesh_network(self, bootstrap_nodes: List[Tuple[str, int]]) -> None:
        """Start the mesh network."""
    
    async def stop_mesh_network(self) -> None:
        """Stop the mesh network."""
    
    async def add_node(self, node_id: bytes, public_key: bytes, address: Tuple[str, int]) -> bool:
        """Add a new node to the mesh."""
    
    async def send_message(self, target_id: bytes, message: bytes) -> bool:
        """Send a message through the mesh network."""
    
    def get_network_stats(self) -> Dict:
        """Get network statistics."""
```

### KeyRotationManager

Manages key rotation for the first ring.

```python
class KeyRotationManager:
    def __init__(self, mesh_network: MeshNetwork):
        """Initialize key rotation manager."""
    
    async def start_key_rotation_service(self) -> None:
        """Start the key rotation service."""
    
    async def initiate_key_rotation(self) -> bool:
        """Initiate a key rotation process."""
    
    async def process_key_change_message(self, message_data: bytes) -> bool:
        """Process incoming key change message."""
    
    def get_rotation_status(self) -> Dict:
        """Get current rotation status."""
```

### SaltProtectionSystem

Provides salt-based message integrity protection.

```python
class SaltProtectionSystem:
    def __init__(self):
        """Initialize salt protection system."""
    
    def create_salted_message(self, message_type: str, payload: bytes, salt_type: SaltType) -> SaltedMessage:
        """Create a salted message with integrity protection."""
    
    def verify_salted_message(self, message: SaltedMessage) -> bool:
        """Verify the integrity of a salted message."""
    
    def create_udp_datagram_salt(self, payload: bytes) -> Tuple[bytes, bytes]:
        """Create salt and integrity hash for UDP datagram."""
    
    def verify_udp_datagram(self, payload: bytes, salt: bytes, integrity_hash: bytes) -> bool:
        """Verify UDP datagram integrity."""
```

## 📡 Message Types

### MessageType Enum

```python
class MessageType(Enum):
    # User messages
    TEXT_MESSAGE = 0x01
    FILE_MESSAGE = 0x02
    VOICE_MESSAGE = 0x03
    
    # Group messages
    GROUP_TEXT_MESSAGE = 0x04
    GROUP_FILE_MESSAGE = 0x05
    GROUP_VOICE_MESSAGE = 0x06
    GROUP_INVITATION = 0x07
    GROUP_JOIN_REQUEST = 0x08
    GROUP_LEAVE = 0x09
    
    # Protocol messages
    HANDSHAKE = 0x10
    KEY_EXCHANGE = 0x11
    HEARTBEAT = 0x12
    RELAY_REQUEST = 0x13
    RELAY_RESPONSE = 0x14
    
    # Relay synchronization messages
    RELAY_DISCOVERY = 0x20
    RELAY_ADVERTISEMENT = 0x21
    RELAY_SYNC = 0x22
    RELAY_HEARTBEAT = 0x23
    GROUP_SYNC = 0x24
    GROUP_UPDATE = 0x25
    
    # Identity and hash messages
    IDENTITY_ANNOUNCEMENT = 0x30
    PUBLIC_KEY_EXCHANGE = 0x31
    HASH_VERIFICATION = 0x32
    
    # Error messages
    ERROR = 0xF0
    INVALID_MESSAGE = 0xF1
    ENCRYPTION_ERROR = 0xF2
    PERMISSION_DENIED = 0xF3
    GROUP_NOT_FOUND = 0xF4
```

### Message Structure

```python
@dataclass
class Message:
    message_type: MessageType
    sender_hash: bytes
    recipient_hash: bytes
    content: bytes
    timestamp: int
    sequence_number: int
    signature: bytes
    
    def to_bytes(self) -> bytes:
        """Serialize message to bytes."""
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "Message":
        """Deserialize message from bytes."""
```

### UserIdentity Structure

```python
@dataclass
class UserIdentity:
    user_hash: bytes  # 16-byte hash of public key
    public_key: bytes
    private_key: bytes  # Encrypted with user password
    nickname: Optional[str] = None
    created_at: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserIdentity":
        """Create from dictionary."""
```

## 🔐 Security API

### HashIdentitySystem

```python
class HashIdentitySystem:
    def __init__(self):
        """Initialize hash identity system."""
    
    def create_user_identity(self, nickname: str, password: str) -> UserIdentity:
        """Create a new user identity."""
    
    def load_user_identity(self, identity_data: Dict) -> UserIdentity:
        """Load user identity from data."""
    
    def set_local_identity(self, identity_hash: bytes, public_key: bytes, private_key: bytes, identity_type: str) -> None:
        """Set local identity."""
    
    def get_identity(self, identity_hash: bytes) -> Optional[HashIdentity]:
        """Get identity by hash."""
    
    def get_all_user_identities(self) -> List[HashIdentity]:
        """Get all user identities."""
    
    def get_all_relay_identities(self) -> List[HashIdentity]:
        """Get all relay identities."""
```

### GroupManager

```python
class GroupManager:
    def __init__(self):
        """Initialize group manager."""
    
    async def create_group(self, group_name: str, owner_hash: bytes, members: List[bytes]) -> bytes:
        """Create a new group."""
    
    async def join_group(self, group_hash: bytes, user_hash: bytes) -> bool:
        """Join a group."""
    
    async def leave_group(self, group_hash: bytes, user_hash: bytes) -> bool:
        """Leave a group."""
    
    async def send_group_message(self, group_hash: bytes, sender_hash: bytes, message: bytes) -> bool:
        """Send a message to a group."""
    
    def get_group_info(self, group_hash: bytes) -> Optional[GroupInfo]:
        """Get group information."""
    
    def get_user_groups(self, user_hash: bytes) -> List[GroupInfo]:
        """Get groups for a user."""
```

## 🌐 Network API

### RelayServer

```python
class RelayServer:
    def __init__(self):
        """Initialize relay server."""
    
    async def start(self) -> None:
        """Start the relay server."""
    
    async def stop(self) -> None:
        """Stop the relay server."""
    
    async def relay_message(self, message_data: bytes, source_address: Tuple[str, int]) -> None:
        """Relay a message to its destination."""
    
    def get_server_info(self) -> Dict:
        """Get server information."""
    
    def get_server_stats(self) -> Dict:
        """Get server statistics."""
```

## 📊 Configuration API

### ProtocolConfig

```python
@dataclass
class ProtocolConfig:
    server_id: bytes
    private_key: bytes
    public_key: bytes
    udp_port: int
    max_packet_size: int
    relay_discovery_interval: int = 300
    relay_sync_interval: int = 60
    max_relay_hops: int = 5
```

### Server Configuration

```yaml
# config/server.yaml
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

## 🔧 Usage Examples

### Basic Client Setup

```python
import asyncio
from src.protocol import AnonymousProtocol, EndToEndEncryption, HashIdentitySystem, GroupManager
from src.protocol.message_types import MessageType

async def main():
    # Create identity system
    identity_system = HashIdentitySystem()
    
    # Create user identity
    user_identity = identity_system.create_user_identity("alice", "strong_password")
    
    # Create group manager
    group_manager = GroupManager()
    
    # Create protocol configuration
    config = ProtocolConfig(
        server_id=user_identity.user_hash,
        private_key=user_identity.private_key,
        public_key=user_identity.public_key,
        udp_port=6667,
        max_packet_size=1400
    )
    
    # Create protocol handler
    protocol = AnonymousProtocol(config, identity_system, group_manager)
    
    # Start protocol
    await protocol.start()
    
    # Send a message
    recipient_hash = b"recipient_hash_here"
    message_content = b"Hello, this is an anonymous message!"
    
    success = await protocol.send_message(
        recipient_hash, 
        message_content, 
        MessageType.TEXT_MESSAGE
    )
    
    if success:
        print("Message sent successfully!")
    
    # Stop protocol
    await protocol.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Relay Server Setup

```python
import asyncio
from src.server.relay_server import RelayServer

async def main():
    # Create relay server
    server = RelayServer()
    
    # Start server
    await server.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped by user.")
```

### Group Management

```python
async def create_and_manage_group():
    # Create group
    group_hash = await protocol.create_group(
        "My Anonymous Group",
        [user_identity.user_hash, other_user_hash]
    )
    
    # Join group
    success = await protocol.join_group(group_hash)
    
    if success:
        print(f"Joined group: {group_hash.hex()}")
    
    # Send group message
    group_message = b"Hello group members!"
    await protocol.send_message(
        group_hash,
        group_message,
        MessageType.GROUP_TEXT_MESSAGE
    )
```

## 📈 Error Handling

### Common Exceptions

```python
class SecIRCError(Exception):
    """Base exception for secIRC errors."""
    pass

class EncryptionError(SecIRCError):
    """Encryption/decryption error."""
    pass

class NetworkError(SecIRCError):
    """Network communication error."""
    pass

class AuthenticationError(SecIRCError):
    """Authentication error."""
    pass

class GroupError(SecIRCError):
    """Group management error."""
    pass
```

### Error Handling Example

```python
try:
    success = await protocol.send_message(recipient_hash, message, MessageType.TEXT_MESSAGE)
    if not success:
        print("Failed to send message")
except EncryptionError as e:
    print(f"Encryption error: {e}")
except NetworkError as e:
    print(f"Network error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## 🔍 Debugging and Monitoring

### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Get logger
logger = logging.getLogger('secIRC')

# Log messages
logger.info("Protocol started")
logger.warning("Network connection lost")
logger.error("Encryption failed")
```

### Statistics

```python
# Get protocol statistics
stats = protocol.get_stats()
print(f"Messages sent: {stats['messages_sent']}")
print(f"Messages received: {stats['messages_received']}")
print(f"Groups joined: {stats['groups_joined']}")

# Get server statistics
server_stats = server.get_server_stats()
print(f"Messages relayed: {server_stats['messages_relayed']}")
print(f"Uptime: {server_stats['uptime']} seconds")
```

---

This API reference provides comprehensive documentation for all major components of the secIRC system. For more detailed information about specific components, refer to the individual module documentation.
