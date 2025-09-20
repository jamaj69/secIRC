"""
Salt-based message integrity protection system.
Implements salt-based tamper detection for all network messages.
"""

import hashlib
import os
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .encryption import EndToEndEncryption


class SaltType(Enum):
    """Types of salt for different message categories."""
    
    # Network protocol salts
    UDP_DATAGRAM = "udp_datagram"
    RELAY_MESSAGE = "relay_message"
    GROUP_MESSAGE = "group_message"
    
    # Key rotation salts
    KEY_CHANGE = "key_change"
    KEY_ACK = "key_ack"
    KEY_VERIFY = "key_verify"
    
    # Ring management salts
    RING_JOIN = "ring_join"
    RING_CONSENSUS = "ring_consensus"
    RING_HEARTBEAT = "ring_heartbeat"
    
    # Challenge salts
    CHALLENGE_REQUEST = "challenge_request"
    CHALLENGE_RESPONSE = "challenge_response"
    CHALLENGE_VERIFY = "challenge_verify"


@dataclass
class SaltedMessage:
    """Message with salt-based integrity protection."""
    
    message_type: str
    payload: bytes
    salt: bytes
    salt_type: SaltType
    timestamp: int
    sequence_number: int
    integrity_hash: bytes
    
    def to_bytes(self) -> bytes:
        """Serialize salted message to bytes."""
        # Message structure:
        # [4 bytes: message_type_length][message_type][4 bytes: salt_type_length][salt_type]
        # [8 bytes: timestamp][4 bytes: sequence_number][4 bytes: payload_length][payload]
        # [32 bytes: salt][32 bytes: integrity_hash]
        
        import struct
        
        message_type_bytes = self.message_type.encode('utf-8')
        salt_type_bytes = self.salt_type.value.encode('utf-8')
        
        header = struct.pack(
            "!I", len(message_type_bytes)
        ) + message_type_bytes + struct.pack(
            "!I", len(salt_type_bytes)
        ) + salt_type_bytes + struct.pack(
            "!QII", self.timestamp, self.sequence_number, len(self.payload)
        )
        
        return header + self.payload + self.salt + self.integrity_hash
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "SaltedMessage":
        """Deserialize salted message from bytes."""
        import struct
        
        if len(data) < 80:  # Minimum size
            raise ValueError("Message too short")
        
        offset = 0
        
        # Parse message type
        message_type_length = struct.unpack("!I", data[offset:offset+4])[0]
        offset += 4
        message_type = data[offset:offset+message_type_length].decode('utf-8')
        offset += message_type_length
        
        # Parse salt type
        salt_type_length = struct.unpack("!I", data[offset:offset+4])[0]
        offset += 4
        salt_type = SaltType(data[offset:offset+salt_type_length].decode('utf-8'))
        offset += salt_type_length
        
        # Parse timestamp, sequence number, and payload length
        timestamp, sequence_number, payload_length = struct.unpack("!QII", data[offset:offset+16])
        offset += 16
        
        # Parse payload
        payload = data[offset:offset+payload_length]
        offset += payload_length
        
        # Parse salt and integrity hash
        salt = data[offset:offset+32]
        offset += 32
        integrity_hash = data[offset:offset+32]
        
        return cls(
            message_type=message_type,
            payload=payload,
            salt=salt,
            salt_type=salt_type,
            timestamp=timestamp,
            sequence_number=sequence_number,
            integrity_hash=integrity_hash
        )


class SaltProtectionSystem:
    """System for salt-based message integrity protection."""
    
    def __init__(self):
        self.encryption = EndToEndEncryption()
        
        # Salt configuration
        self.salt_length = 32  # 32 bytes
        self.integrity_hash_length = 32  # 32 bytes
        self.salt_entropy_source = os.urandom  # Entropy source for salts
        
        # Message sequence tracking
        self.sequence_numbers: Dict[str, int] = {}  # message_type -> sequence_number
        self.received_sequences: Dict[str, set] = {}  # message_type -> set of received sequences
        
        # Salt validation
        self.salt_validation_enabled = True
        self.duplicate_salt_detection = True
        self.timestamp_validation = True
        self.max_message_age = 300  # 5 minutes
        
        # Statistics
        self.stats = {
            "messages_protected": 0,
            "messages_verified": 0,
            "integrity_failures": 0,
            "salt_collisions": 0,
            "duplicate_messages": 0,
            "timestamp_failures": 0
        }
    
    def create_salted_message(self, message_type: str, payload: bytes, 
                            salt_type: SaltType) -> SaltedMessage:
        """Create a salted message with integrity protection."""
        # Generate unique salt
        salt = self._generate_salt(salt_type)
        
        # Get sequence number
        sequence_number = self._get_next_sequence_number(message_type)
        
        # Create message
        message = SaltedMessage(
            message_type=message_type,
            payload=payload,
            salt=salt,
            salt_type=salt_type,
            timestamp=int(time.time()),
            sequence_number=sequence_number,
            integrity_hash=b""  # Will be calculated
        )
        
        # Calculate integrity hash
        message.integrity_hash = self._calculate_integrity_hash(message)
        
        self.stats["messages_protected"] += 1
        
        return message
    
    def verify_salted_message(self, message: SaltedMessage) -> bool:
        """Verify the integrity of a salted message."""
        try:
            # Check timestamp validity
            if self.timestamp_validation:
                if not self._verify_timestamp(message.timestamp):
                    self.stats["timestamp_failures"] += 1
                    return False
            
            # Check for duplicate sequence numbers
            if self.duplicate_salt_detection:
                if not self._verify_sequence_number(message.message_type, message.sequence_number):
                    self.stats["duplicate_messages"] += 1
                    return False
            
            # Verify integrity hash
            expected_hash = self._calculate_integrity_hash(message)
            if message.integrity_hash != expected_hash:
                self.stats["integrity_failures"] += 1
                return False
            
            # Check for salt collisions
            if self._is_duplicate_salt(message.salt, message.salt_type):
                self.stats["salt_collisions"] += 1
                return False
            
            # Record successful verification
            self._record_sequence_number(message.message_type, message.sequence_number)
            self.stats["messages_verified"] += 1
            
            return True
            
        except Exception as e:
            print(f"Error verifying salted message: {e}")
            return False
    
    def _generate_salt(self, salt_type: SaltType) -> bytes:
        """Generate a unique salt for the given type."""
        # Create salt with type-specific entropy
        base_salt = self.salt_entropy_source(self.salt_length)
        
        # Add type-specific data to prevent cross-type collisions
        type_data = salt_type.value.encode('utf-8')
        timestamp_data = int(time.time()).to_bytes(8, 'big')
        
        # Combine and hash to create final salt
        combined_data = base_salt + type_data + timestamp_data
        salt = hashlib.sha256(combined_data).digest()[:self.salt_length]
        
        return salt
    
    def _calculate_integrity_hash(self, message: SaltedMessage) -> bytes:
        """Calculate integrity hash for a message."""
        # Create hash input: payload + salt + type + timestamp + sequence
        hash_input = (
            message.payload +
            message.salt +
            message.salt_type.value.encode('utf-8') +
            message.timestamp.to_bytes(8, 'big') +
            message.sequence_number.to_bytes(4, 'big')
        )
        
        # Calculate hash
        integrity_hash = hashlib.sha256(hash_input).digest()
        
        return integrity_hash
    
    def _verify_timestamp(self, timestamp: int) -> bool:
        """Verify message timestamp is within acceptable range."""
        current_time = int(time.time())
        age = current_time - timestamp
        
        # Check if message is too old
        if age > self.max_message_age:
            return False
        
        # Check if message is from the future (with small tolerance)
        if timestamp > current_time + 60:  # 1 minute tolerance
            return False
        
        return True
    
    def _get_next_sequence_number(self, message_type: str) -> int:
        """Get next sequence number for message type."""
        if message_type not in self.sequence_numbers:
            self.sequence_numbers[message_type] = 0
        
        self.sequence_numbers[message_type] += 1
        return self.sequence_numbers[message_type]
    
    def _verify_sequence_number(self, message_type: str, sequence_number: int) -> bool:
        """Verify sequence number is not a duplicate."""
        if message_type not in self.received_sequences:
            self.received_sequences[message_type] = set()
        
        # Check if sequence number already received
        if sequence_number in self.received_sequences[message_type]:
            return False
        
        return True
    
    def _record_sequence_number(self, message_type: str, sequence_number: int) -> None:
        """Record a received sequence number."""
        if message_type not in self.received_sequences:
            self.received_sequences[message_type] = set()
        
        self.received_sequences[message_type].add(sequence_number)
        
        # Clean up old sequence numbers (keep last 1000)
        if len(self.received_sequences[message_type]) > 1000:
            # Remove oldest sequence numbers
            sorted_sequences = sorted(self.received_sequences[message_type])
            self.received_sequences[message_type] = set(sorted_sequences[-1000:])
    
    def _is_duplicate_salt(self, salt: bytes, salt_type: SaltType) -> bool:
        """Check if salt has been used before."""
        # In a real implementation, this would maintain a database of used salts
        # For now, we'll use a simple in-memory set
        # This is not production-ready as it will grow indefinitely
        
        # For demonstration, we'll just return False
        # In production, implement proper salt tracking with cleanup
        return False
    
    def create_udp_datagram_salt(self, payload: bytes) -> Tuple[bytes, bytes]:
        """Create salt and integrity hash for UDP datagram."""
        salt = self._generate_salt(SaltType.UDP_DATAGRAM)
        
        # Calculate integrity hash for UDP datagram
        hash_input = payload + salt + SaltType.UDP_DATAGRAM.value.encode('utf-8')
        integrity_hash = hashlib.sha256(hash_input).digest()
        
        return salt, integrity_hash
    
    def verify_udp_datagram(self, payload: bytes, salt: bytes, 
                          integrity_hash: bytes) -> bool:
        """Verify UDP datagram integrity."""
        # Calculate expected hash
        hash_input = payload + salt + SaltType.UDP_DATAGRAM.value.encode('utf-8')
        expected_hash = hashlib.sha256(hash_input).digest()
        
        return integrity_hash == expected_hash
    
    def create_relay_message_salt(self, message_data: bytes) -> Tuple[bytes, bytes]:
        """Create salt and integrity hash for relay message."""
        salt = self._generate_salt(SaltType.RELAY_MESSAGE)
        
        # Calculate integrity hash for relay message
        hash_input = message_data + salt + SaltType.RELAY_MESSAGE.value.encode('utf-8')
        integrity_hash = hashlib.sha256(hash_input).digest()
        
        return salt, integrity_hash
    
    def verify_relay_message(self, message_data: bytes, salt: bytes,
                           integrity_hash: bytes) -> bool:
        """Verify relay message integrity."""
        # Calculate expected hash
        hash_input = message_data + salt + SaltType.RELAY_MESSAGE.value.encode('utf-8')
        expected_hash = hashlib.sha256(hash_input).digest()
        
        return integrity_hash == expected_hash
    
    def create_group_message_salt(self, group_data: bytes) -> Tuple[bytes, bytes]:
        """Create salt and integrity hash for group message."""
        salt = self._generate_salt(SaltType.GROUP_MESSAGE)
        
        # Calculate integrity hash for group message
        hash_input = group_data + salt + SaltType.GROUP_MESSAGE.value.encode('utf-8')
        integrity_hash = hashlib.sha256(hash_input).digest()
        
        return salt, integrity_hash
    
    def verify_group_message(self, group_data: bytes, salt: bytes,
                           integrity_hash: bytes) -> bool:
        """Verify group message integrity."""
        # Calculate expected hash
        hash_input = group_data + salt + SaltType.GROUP_MESSAGE.value.encode('utf-8')
        expected_hash = hashlib.sha256(hash_input).digest()
        
        return integrity_hash == expected_hash
    
    def create_key_rotation_salt(self, key_data: bytes, rotation_id: bytes) -> Tuple[bytes, bytes]:
        """Create salt and integrity hash for key rotation message."""
        salt = self._generate_salt(SaltType.KEY_CHANGE)
        
        # Include rotation ID in hash calculation for uniqueness
        hash_input = key_data + salt + rotation_id + SaltType.KEY_CHANGE.value.encode('utf-8')
        integrity_hash = hashlib.sha256(hash_input).digest()
        
        return salt, integrity_hash
    
    def verify_key_rotation_message(self, key_data: bytes, salt: bytes,
                                  integrity_hash: bytes, rotation_id: bytes) -> bool:
        """Verify key rotation message integrity."""
        # Calculate expected hash
        hash_input = key_data + salt + rotation_id + SaltType.KEY_CHANGE.value.encode('utf-8')
        expected_hash = hashlib.sha256(hash_input).digest()
        
        return integrity_hash == expected_hash
    
    def create_challenge_salt(self, challenge_data: bytes, challenge_id: bytes) -> Tuple[bytes, bytes]:
        """Create salt and integrity hash for challenge message."""
        salt = self._generate_salt(SaltType.CHALLENGE_REQUEST)
        
        # Include challenge ID in hash calculation
        hash_input = challenge_data + salt + challenge_id + SaltType.CHALLENGE_REQUEST.value.encode('utf-8')
        integrity_hash = hashlib.sha256(hash_input).digest()
        
        return salt, integrity_hash
    
    def verify_challenge_message(self, challenge_data: bytes, salt: bytes,
                               integrity_hash: bytes, challenge_id: bytes) -> bool:
        """Verify challenge message integrity."""
        # Calculate expected hash
        hash_input = challenge_data + salt + challenge_id + SaltType.CHALLENGE_REQUEST.value.encode('utf-8')
        expected_hash = hashlib.sha256(hash_input).digest()
        
        return integrity_hash == expected_hash
    
    def get_salt_protection_stats(self) -> Dict:
        """Get salt protection statistics."""
        return {
            **self.stats,
            "salt_length": self.salt_length,
            "integrity_hash_length": self.integrity_hash_length,
            "max_message_age": self.max_message_age,
            "active_sequence_types": len(self.sequence_numbers),
            "total_received_sequences": sum(len(seqs) for seqs in self.received_sequences.values())
        }
    
    def reset_sequence_numbers(self, message_type: Optional[str] = None) -> None:
        """Reset sequence numbers for a message type or all types."""
        if message_type:
            if message_type in self.sequence_numbers:
                del self.sequence_numbers[message_type]
            if message_type in self.received_sequences:
                del self.received_sequences[message_type]
        else:
            self.sequence_numbers.clear()
            self.received_sequences.clear()
    
    def cleanup_old_sequences(self, max_age_seconds: int = 3600) -> None:
        """Clean up old sequence numbers."""
        current_time = int(time.time())
        
        # This is a simplified cleanup - in production, you'd want more sophisticated cleanup
        for message_type in list(self.received_sequences.keys()):
            sequences = self.received_sequences[message_type]
            if len(sequences) > 1000:  # Keep only last 1000 sequences
                sorted_sequences = sorted(sequences)
                self.received_sequences[message_type] = set(sorted_sequences[-1000:])
    
    def enable_salt_validation(self, enabled: bool = True) -> None:
        """Enable or disable salt validation."""
        self.salt_validation_enabled = enabled
    
    def enable_duplicate_detection(self, enabled: bool = True) -> None:
        """Enable or disable duplicate message detection."""
        self.duplicate_salt_detection = enabled
    
    def enable_timestamp_validation(self, enabled: bool = True) -> None:
        """Enable or disable timestamp validation."""
        self.timestamp_validation = enabled
    
    def set_max_message_age(self, max_age_seconds: int) -> None:
        """Set maximum message age for validation."""
        self.max_message_age = max_age_seconds
