"""
Message types and structures for the anonymous messaging protocol.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
import struct
import time


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


@dataclass
class Message:
    """Base message structure for anonymous communication."""
    
    message_type: MessageType
    payload: bytes
    timestamp: int
    message_id: bytes  # 16-byte unique identifier
    relay_chain: Optional[list] = None  # List of relay server IDs
    encryption_layer: int = 0  # Number of encryption layers
    
    def __post_init__(self):
        """Validate message after initialization."""
        if len(self.message_id) != 16:
            raise ValueError("Message ID must be exactly 16 bytes")
        if self.timestamp <= 0:
            self.timestamp = int(time.time())
    
    def to_bytes(self) -> bytes:
        """Serialize message to bytes for UDP transmission."""
        # Message structure:
        # [4 bytes: message_type][8 bytes: timestamp][16 bytes: message_id]
        # [1 byte: encryption_layers][4 bytes: payload_length][payload]
        
        header = struct.pack(
            "!IQ16sB",
            self.message_type.value,
            self.timestamp,
            self.message_id,
            self.encryption_layer
        )
        
        payload_length = len(self.payload)
        length_header = struct.pack("!I", payload_length)
        
        return header + length_header + self.payload
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "Message":
        """Deserialize message from bytes."""
        if len(data) < 33:  # Minimum header size
            raise ValueError("Message too short")
        
        # Parse header
        message_type_val, timestamp, message_id, encryption_layer = struct.unpack(
            "!IQ16sB", data[:29]
        )
        
        # Parse payload length
        payload_length = struct.unpack("!I", data[29:33])[0]
        
        if len(data) < 33 + payload_length:
            raise ValueError("Incomplete message")
        
        payload = data[33:33 + payload_length]
        
        return cls(
            message_type=MessageType(message_type_val),
            payload=payload,
            timestamp=timestamp,
            message_id=message_id,
            encryption_layer=encryption_layer
        )


@dataclass
class RelayInfo:
    """Information about a relay server."""
    
    server_id: bytes  # 16-byte unique identifier
    address: str
    port: int
    public_key: bytes
    last_seen: int
    reputation: float = 1.0
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "server_id": self.server_id.hex(),
            "address": self.address,
            "port": self.port,
            "public_key": self.public_key.hex(),
            "last_seen": self.last_seen,
            "reputation": self.reputation,
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RelayInfo":
        """Create from dictionary."""
        return cls(
            server_id=bytes.fromhex(data["server_id"]),
            address=data["address"],
            port=data["port"],
            public_key=bytes.fromhex(data["public_key"]),
            last_seen=data["last_seen"],
            reputation=data.get("reputation", 1.0),
            is_active=data.get("is_active", True)
        )


@dataclass
class UserIdentity:
    """Anonymous user identity with cryptographic keys."""
    
    user_hash: bytes  # 16-byte hash of public key (primary identifier)
    public_key: bytes
    private_key: bytes  # Encrypted with user password
    nickname: Optional[str] = None
    created_at: int = 0
    
    def __post_init__(self):
        """Set creation timestamp if not provided."""
        if self.created_at == 0:
            self.created_at = int(time.time())
        
        # Generate user hash from public key if not provided
        if not hasattr(self, 'user_hash') or not self.user_hash:
            self.user_hash = self._generate_user_hash()
    
    def _generate_user_hash(self) -> bytes:
        """Generate user hash from public key."""
        import hashlib
        return hashlib.sha256(self.public_key).digest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "user_hash": self.user_hash.hex(),
            "public_key": self.public_key.hex(),
            "private_key": self.private_key.hex(),
            "nickname": self.nickname,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserIdentity":
        """Create from dictionary."""
        return cls(
            user_hash=bytes.fromhex(data["user_hash"]),
            public_key=bytes.fromhex(data["public_key"]),
            private_key=bytes.fromhex(data["private_key"]),
            nickname=data.get("nickname"),
            created_at=data.get("created_at", 0)
        )


@dataclass
class HashIdentity:
    """Hash-based identity for anonymous communication."""
    
    identity_hash: bytes  # 16-byte hash identifier
    public_key: bytes
    identity_type: str  # "user", "group", "relay"
    created_at: int
    last_seen: int = 0
    
    def __post_init__(self):
        """Set timestamps if not provided."""
        current_time = int(time.time())
        if self.created_at == 0:
            self.created_at = current_time
        if self.last_seen == 0:
            self.last_seen = current_time
    
    def update_last_seen(self) -> None:
        """Update last seen timestamp."""
        self.last_seen = int(time.time())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "identity_hash": self.identity_hash.hex(),
            "public_key": self.public_key.hex(),
            "identity_type": self.identity_type,
            "created_at": self.created_at,
            "last_seen": self.last_seen
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HashIdentity":
        """Create from dictionary."""
        return cls(
            identity_hash=bytes.fromhex(data["identity_hash"]),
            public_key=bytes.fromhex(data["public_key"]),
            identity_type=data["identity_type"],
            created_at=data["created_at"],
            last_seen=data.get("last_seen", 0)
        )
