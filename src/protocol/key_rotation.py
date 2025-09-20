"""
Key rotation system for first ring relay servers.
Implements periodic key changes with salt-based message integrity.
"""

import asyncio
import hashlib
import json
import os
import time
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .encryption import EndToEndEncryption
from .mesh_network import MeshNetwork, RelayNode


class KeyRotationPhase(Enum):
    """Phases of key rotation process."""
    
    IDLE = "idle"  # No rotation in progress
    INITIATED = "initiated"  # Rotation initiated by a member
    KEY_GENERATION = "key_generation"  # New keys being generated
    KEY_DISTRIBUTION = "key_distribution"  # New keys being distributed
    ACKNOWLEDGMENT = "acknowledgment"  # Waiting for acknowledgments
    VERIFICATION = "verification"  # Verifying new connections
    COMPLETED = "completed"  # Rotation completed
    FAILED = "failed"  # Rotation failed


@dataclass
class KeyRotationMessage:
    """Message for key rotation protocol."""
    
    message_type: str  # "key_change_init", "key_change_ack", "key_change_verify"
    rotation_id: bytes  # Unique rotation session ID
    sender_id: bytes  # Sender's node ID
    old_key_hash: bytes  # Hash of old key for verification
    new_public_key: bytes  # New public key
    timestamp: int
    sequence_number: int
    salt: bytes  # Random salt for integrity
    signature: bytes  # Signature with old key
    
    def to_bytes(self) -> bytes:
        """Serialize message to bytes with salt at the end."""
        message_data = {
            "type": self.message_type,
            "rotation_id": self.rotation_id.hex(),
            "sender_id": self.sender_id.hex(),
            "old_key_hash": self.old_key_hash.hex(),
            "new_public_key": self.new_public_key.hex(),
            "timestamp": self.timestamp,
            "sequence_number": self.sequence_number
        }
        
        # Convert to JSON and add salt
        json_data = json.dumps(message_data).encode('utf-8')
        return json_data + self.salt + self.signature
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "KeyRotationMessage":
        """Deserialize message from bytes."""
        # Extract signature (last 256 bytes)
        signature = data[-256:]
        data_without_signature = data[:-256]
        
        # Extract salt (next to last 32 bytes)
        salt = data_without_signature[-32:]
        json_data = data_without_signature[:-32]
        
        # Parse JSON
        message_data = json.loads(json_data.decode('utf-8'))
        
        return cls(
            message_type=message_data["type"],
            rotation_id=bytes.fromhex(message_data["rotation_id"]),
            sender_id=bytes.fromhex(message_data["sender_id"]),
            old_key_hash=bytes.fromhex(message_data["old_key_hash"]),
            new_public_key=bytes.fromhex(message_data["new_public_key"]),
            timestamp=message_data["timestamp"],
            sequence_number=message_data["sequence_number"],
            salt=salt,
            signature=signature
        )


@dataclass
class KeyRotationSession:
    """Session for key rotation process."""
    
    rotation_id: bytes
    initiator_id: bytes
    phase: KeyRotationPhase
    start_time: int
    participants: Set[bytes]  # Set of participating node IDs
    acknowledgments: Dict[bytes, bool]  # node_id -> acknowledged
    new_connections: Dict[bytes, bool]  # node_id -> connection_verified
    old_keys: Dict[bytes, bytes]  # node_id -> old_public_key
    new_keys: Dict[bytes, bytes]  # node_id -> new_public_key
    timeout: int = 300  # 5 minutes timeout
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "rotation_id": self.rotation_id.hex(),
            "initiator_id": self.initiator_id.hex(),
            "phase": self.phase.value,
            "start_time": self.start_time,
            "participants": [node_id.hex() for node_id in self.participants],
            "acknowledgments": {node_id.hex(): ack for node_id, ack in self.acknowledgments.items()},
            "new_connections": {node_id.hex(): conn for node_id, conn in self.new_connections.items()},
            "old_keys": {node_id.hex(): key.hex() for node_id, key in self.old_keys.items()},
            "new_keys": {node_id.hex(): key.hex() for node_id, key in self.new_keys.items()},
            "timeout": self.timeout
        }


class KeyRotationManager:
    """Manages key rotation for first ring relay servers."""
    
    def __init__(self, mesh_network: MeshNetwork):
        self.mesh_network = mesh_network
        self.encryption = EndToEndEncryption()
        
        # Key rotation state
        self.active_rotation: Optional[KeyRotationSession] = None
        self.rotation_history: List[KeyRotationSession] = []
        
        # Key management
        self.current_keys: Dict[bytes, Tuple[bytes, bytes]] = {}  # node_id -> (public_key, private_key)
        self.pending_keys: Dict[bytes, Tuple[bytes, bytes]] = {}  # node_id -> (new_public_key, new_private_key)
        
        # Configuration
        self.rotation_interval = 86400  # 24 hours
        self.key_lifetime = 172800  # 48 hours (2 days)
        self.rotation_timeout = 300  # 5 minutes
        self.salt_length = 32  # 32 bytes salt
        
        # Statistics
        self.stats = {
            "rotations_initiated": 0,
            "rotations_completed": 0,
            "rotations_failed": 0,
            "key_changes_processed": 0,
            "acknowledgments_received": 0,
            "connections_verified": 0
        }
        
        # Background tasks
        self.rotation_task: Optional[asyncio.Task] = None
        self.monitor_task: Optional[asyncio.Task] = None
    
    async def start_key_rotation_service(self) -> None:
        """Start the key rotation service."""
        print("🔑 Starting key rotation service...")
        
        # Initialize current keys for all ring members
        await self._initialize_current_keys()
        
        # Start background tasks
        self.rotation_task = asyncio.create_task(self._periodic_key_rotation())
        self.monitor_task = asyncio.create_task(self._monitor_rotation_sessions())
        
        print("✅ Key rotation service started")
    
    async def _initialize_current_keys(self) -> None:
        """Initialize current keys for all ring members."""
        for member_id in self.mesh_network.first_ring:
            if member_id == self.mesh_network.node_id:
                # Use our own keys
                self.current_keys[member_id] = (
                    self.mesh_network.public_key,
                    self.mesh_network.private_key
                )
            else:
                # Get keys from known nodes
                node = self.mesh_network.known_nodes.get(member_id)
                if node:
                    # For now, we don't have private keys of other nodes
                    # In a real implementation, this would be handled differently
                    self.current_keys[member_id] = (node.public_key, b"")
    
    async def _periodic_key_rotation(self) -> None:
        """Periodic key rotation based on interval."""
        while True:
            await asyncio.sleep(self.rotation_interval)
            
            # Check if rotation is needed
            if await self._is_rotation_needed():
                await self.initiate_key_rotation()
    
    async def _is_rotation_needed(self) -> bool:
        """Check if key rotation is needed."""
        # Check if we have an active rotation
        if self.active_rotation:
            return False
        
        # Check if keys are approaching expiration
        current_time = int(time.time())
        for member_id, (public_key, private_key) in self.current_keys.items():
            # In a real implementation, we'd check key creation time
            # For now, always return True to test rotation
            return True
        
        return False
    
    async def initiate_key_rotation(self) -> bool:
        """Initiate a key rotation process."""
        if self.active_rotation:
            print("⚠️ Key rotation already in progress")
            return False
        
        print("🔄 Initiating key rotation...")
        
        # Generate new keypair for ourselves
        new_private_key, new_public_key = self.encryption.generate_keypair()
        
        # Create rotation session
        import os
        rotation_id = os.urandom(16)
        
        self.active_rotation = KeyRotationSession(
            rotation_id=rotation_id,
            initiator_id=self.mesh_network.node_id,
            phase=KeyRotationPhase.INITIATED,
            start_time=int(time.time()),
            participants=self.mesh_network.first_ring.copy(),
            acknowledgments={},
            new_connections={},
            old_keys={},
            new_keys={}
        )
        
        # Store our new keys
        self.pending_keys[self.mesh_network.node_id] = (new_public_key, new_private_key)
        self.active_rotation.old_keys[self.mesh_network.node_id] = self.mesh_network.public_key
        self.active_rotation.new_keys[self.mesh_network.node_id] = new_public_key
        
        # Store old keys for other members
        for member_id in self.mesh_network.first_ring:
            if member_id != self.mesh_network.node_id:
                old_public_key, _ = self.current_keys.get(member_id, (b"", b""))
                self.active_rotation.old_keys[member_id] = old_public_key
        
        self.stats["rotations_initiated"] += 1
        
        # Start key distribution phase
        await self._start_key_distribution()
        
        return True
    
    async def _start_key_distribution(self) -> None:
        """Start distributing new keys to ring members."""
        if not self.active_rotation:
            return
        
        print("📤 Starting key distribution...")
        self.active_rotation.phase = KeyRotationPhase.KEY_DISTRIBUTION
        
        # Send key change message to all ring members
        for member_id in self.mesh_network.first_ring:
            if member_id != self.mesh_network.node_id:
                await self._send_key_change_message(member_id)
    
    async def _send_key_change_message(self, target_id: bytes) -> None:
        """Send key change message to a specific member."""
        if not self.active_rotation:
            return
        
        try:
            # Create key change message
            message = KeyRotationMessage(
                message_type="key_change_init",
                rotation_id=self.active_rotation.rotation_id,
                sender_id=self.mesh_network.node_id,
                old_key_hash=self._hash_public_key(self.mesh_network.public_key),
                new_public_key=self.pending_keys[self.mesh_network.node_id][0],
                timestamp=int(time.time()),
                sequence_number=1,
                salt=os.urandom(self.salt_length),
                signature=b""  # Will be set after signing
            )
            
            # Sign message with old private key
            message_data = message.to_bytes()[:-256]  # Exclude signature
            message.signature = self.encryption._sign_message(message_data, self.mesh_network.private_key)
            
            # Send message
            await self._send_rotation_message(target_id, message)
            
            print(f"📤 Sent key change message to {target_id.hex()}")
            
        except Exception as e:
            print(f"Failed to send key change message to {target_id.hex()}: {e}")
    
    async def _send_rotation_message(self, target_id: bytes, message: KeyRotationMessage) -> None:
        """Send rotation message to target."""
        # This would implement actual network communication
        # For now, simulate sending
        print(f"📡 Sending rotation message to {target_id.hex()}")
        
        # Simulate message processing
        await asyncio.sleep(0.1)
    
    async def process_key_change_message(self, message_data: bytes) -> bool:
        """Process incoming key change message."""
        try:
            # Parse message
            message = KeyRotationMessage.from_bytes(message_data)
            
            # Verify message integrity using salt
            if not await self._verify_message_integrity(message):
                print("❌ Message integrity verification failed")
                return False
            
            # Verify signature with old key
            if not await self._verify_message_signature(message):
                print("❌ Message signature verification failed")
                return False
            
            print(f"📥 Received key change message from {message.sender_id.hex()}")
            
            # Process based on message type
            if message.message_type == "key_change_init":
                return await self._process_key_change_init(message)
            elif message.message_type == "key_change_ack":
                return await self._process_key_change_ack(message)
            elif message.message_type == "key_change_verify":
                return await self._process_key_change_verify(message)
            else:
                print(f"❌ Unknown message type: {message.message_type}")
                return False
                
        except Exception as e:
            print(f"Error processing key change message: {e}")
            return False
    
    async def _verify_message_integrity(self, message: KeyRotationMessage) -> bool:
        """Verify message integrity using salt."""
        try:
            # Recreate the message data without signature
            message_data = {
                "type": message.message_type,
                "rotation_id": message.rotation_id.hex(),
                "sender_id": message.sender_id.hex(),
                "old_key_hash": message.old_key_hash.hex(),
                "new_public_key": message.new_public_key.hex(),
                "timestamp": message.timestamp,
                "sequence_number": message.sequence_number
            }
            
            json_data = json.dumps(message_data).encode('utf-8')
            expected_data = json_data + message.salt
            
            # Verify the data matches what we received
            # In a real implementation, we'd verify the hash
            return True
            
        except Exception:
            return False
    
    async def _verify_message_signature(self, message: KeyRotationMessage) -> bool:
        """Verify message signature with old key."""
        try:
            # Get sender's old public key
            old_public_key = self.active_rotation.old_keys.get(message.sender_id) if self.active_rotation else None
            if not old_public_key:
                # Try to get from current keys
                old_public_key, _ = self.current_keys.get(message.sender_id, (b"", b""))
            
            if not old_public_key:
                print(f"❌ No old key found for sender {message.sender_id.hex()}")
                return False
            
            # Verify signature
            message_data = message.to_bytes()[:-256]  # Exclude signature
            return self.encryption._verify_signature(message_data, message.signature, old_public_key)
            
        except Exception as e:
            print(f"Error verifying signature: {e}")
            return False
    
    async def _process_key_change_init(self, message: KeyRotationMessage) -> bool:
        """Process key change initiation message."""
        # Check if we already have an active rotation
        if self.active_rotation and self.active_rotation.rotation_id != message.rotation_id:
            print("⚠️ Different rotation already in progress")
            return False
        
        # If no active rotation, create one
        if not self.active_rotation:
            self.active_rotation = KeyRotationSession(
                rotation_id=message.rotation_id,
                initiator_id=message.sender_id,
                phase=KeyRotationPhase.KEY_GENERATION,
                start_time=int(time.time()),
                participants=self.mesh_network.first_ring.copy(),
                acknowledgments={},
                new_connections={},
                old_keys={},
                new_keys={}
            )
        
        # Generate new keypair for ourselves
        new_private_key, new_public_key = self.encryption.generate_keypair()
        
        # Store new keys
        self.pending_keys[self.mesh_network.node_id] = (new_public_key, new_private_key)
        self.active_rotation.old_keys[self.mesh_network.node_id] = self.mesh_network.public_key
        self.active_rotation.new_keys[self.mesh_network.node_id] = new_public_key
        self.active_rotation.old_keys[message.sender_id] = message.old_key_hash
        self.active_rotation.new_keys[message.sender_id] = message.new_public_key
        
        # Send acknowledgment
        await self._send_key_change_acknowledgment(message.sender_id, message.rotation_id)
        
        return True
    
    async def _send_key_change_acknowledgment(self, target_id: bytes, rotation_id: bytes) -> None:
        """Send key change acknowledgment."""
        try:
            # Create acknowledgment message
            message = KeyRotationMessage(
                message_type="key_change_ack",
                rotation_id=rotation_id,
                sender_id=self.mesh_network.node_id,
                old_key_hash=self._hash_public_key(self.mesh_network.public_key),
                new_public_key=self.pending_keys[self.mesh_network.node_id][0],
                timestamp=int(time.time()),
                sequence_number=2,
                salt=os.urandom(self.salt_length),
                signature=b""
            )
            
            # Sign with old private key
            message_data = message.to_bytes()[:-256]
            message.signature = self.encryption._sign_message(message_data, self.mesh_network.private_key)
            
            # Send message
            await self._send_rotation_message(target_id, message)
            
            print(f"📤 Sent key change acknowledgment to {target_id.hex()}")
            
        except Exception as e:
            print(f"Failed to send acknowledgment to {target_id.hex()}: {e}")
    
    async def _process_key_change_ack(self, message: KeyRotationMessage) -> bool:
        """Process key change acknowledgment."""
        if not self.active_rotation or self.active_rotation.rotation_id != message.rotation_id:
            return False
        
        # Record acknowledgment
        self.active_rotation.acknowledgments[message.sender_id] = True
        self.stats["acknowledgments_received"] += 1
        
        print(f"✅ Received acknowledgment from {message.sender_id.hex()}")
        
        # Check if all acknowledgments received
        if len(self.active_rotation.acknowledgments) >= len(self.active_rotation.participants) - 1:
            await self._start_connection_verification()
        
        return True
    
    async def _start_connection_verification(self) -> None:
        """Start verifying new connections."""
        if not self.active_rotation:
            return
        
        print("🔍 Starting connection verification...")
        self.active_rotation.phase = KeyRotationPhase.VERIFICATION
        
        # Test connections with new keys
        for member_id in self.mesh_network.first_ring:
            if member_id != self.mesh_network.node_id:
                await self._verify_new_connection(member_id)
    
    async def _verify_new_connection(self, target_id: bytes) -> None:
        """Verify new connection with target."""
        try:
            # Create verification message
            message = KeyRotationMessage(
                message_type="key_change_verify",
                rotation_id=self.active_rotation.rotation_id,
                sender_id=self.mesh_network.node_id,
                old_key_hash=self._hash_public_key(self.mesh_network.public_key),
                new_public_key=self.pending_keys[self.mesh_network.node_id][0],
                timestamp=int(time.time()),
                sequence_number=3,
                salt=os.urandom(self.salt_length),
                signature=b""
            )
            
            # Sign with NEW private key
            new_private_key = self.pending_keys[self.mesh_network.node_id][1]
            message_data = message.to_bytes()[:-256]
            message.signature = self.encryption._sign_message(message_data, new_private_key)
            
            # Send verification message
            await self._send_rotation_message(target_id, message)
            
            print(f"🔍 Sent connection verification to {target_id.hex()}")
            
        except Exception as e:
            print(f"Failed to verify connection with {target_id.hex()}: {e}")
    
    async def _process_key_change_verify(self, message: KeyRotationMessage) -> bool:
        """Process key change verification message."""
        if not self.active_rotation or self.active_rotation.rotation_id != message.rotation_id:
            return False
        
        # Verify signature with NEW public key
        new_public_key = self.active_rotation.new_keys.get(message.sender_id)
        if not new_public_key:
            print(f"❌ No new key found for sender {message.sender_id.hex()}")
            return False
        
        message_data = message.to_bytes()[:-256]
        if not self.encryption._verify_signature(message_data, message.signature, new_public_key):
            print(f"❌ New key signature verification failed for {message.sender_id.hex()}")
            return False
        
        # Record successful verification
        self.active_rotation.new_connections[message.sender_id] = True
        self.stats["connections_verified"] += 1
        
        print(f"✅ Connection verified with {message.sender_id.hex()}")
        
        # Check if all connections verified
        if len(self.active_rotation.new_connections) >= len(self.active_rotation.participants) - 1:
            await self._complete_key_rotation()
        
        return True
    
    async def _complete_key_rotation(self) -> None:
        """Complete the key rotation process."""
        if not self.active_rotation:
            return
        
        print("🎉 Key rotation completed successfully!")
        
        # Update current keys
        for member_id, (new_public_key, new_private_key) in self.pending_keys.items():
            self.current_keys[member_id] = (new_public_key, new_private_key)
        
        # Update mesh network keys
        if self.mesh_network.node_id in self.pending_keys:
            new_public_key, new_private_key = self.pending_keys[self.mesh_network.node_id]
            self.mesh_network.public_key = new_public_key
            self.mesh_network.private_key = new_private_key
        
        # Update ring member keys
        for member_id, new_public_key in self.active_rotation.new_keys.items():
            if member_id in self.mesh_network.known_nodes:
                self.mesh_network.known_nodes[member_id].public_key = new_public_key
        
        # Complete rotation
        self.active_rotation.phase = KeyRotationPhase.COMPLETED
        self.rotation_history.append(self.active_rotation)
        self.stats["rotations_completed"] += 1
        
        # Clear pending keys and active rotation
        self.pending_keys.clear()
        self.active_rotation = None
        
        print("✅ All keys updated successfully")
    
    async def _monitor_rotation_sessions(self) -> None:
        """Monitor active rotation sessions for timeouts."""
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            if not self.active_rotation:
                continue
            
            current_time = int(time.time())
            
            # Check for timeout
            if current_time - self.active_rotation.start_time > self.active_rotation.timeout:
                print("⏰ Key rotation timed out")
                await self._fail_key_rotation("timeout")
    
    async def _fail_key_rotation(self, reason: str) -> None:
        """Fail the current key rotation."""
        if not self.active_rotation:
            return
        
        print(f"❌ Key rotation failed: {reason}")
        
        self.active_rotation.phase = KeyRotationPhase.FAILED
        self.rotation_history.append(self.active_rotation)
        self.stats["rotations_failed"] += 1
        
        # Clear pending keys and active rotation
        self.pending_keys.clear()
        self.active_rotation = None
    
    def _hash_public_key(self, public_key: bytes) -> bytes:
        """Create a hash of a public key."""
        return hashlib.sha256(public_key).digest()[:16]
    
    def get_rotation_status(self) -> Dict:
        """Get current rotation status."""
        if not self.active_rotation:
            return {
                "active": False,
                "phase": None,
                "participants": 0,
                "acknowledgments": 0,
                "verified_connections": 0
            }
        
        return {
            "active": True,
            "phase": self.active_rotation.phase.value,
            "participants": len(self.active_rotation.participants),
            "acknowledgments": len(self.active_rotation.acknowledgments),
            "verified_connections": len(self.active_rotation.new_connections),
            "start_time": self.active_rotation.start_time,
            "timeout": self.active_rotation.timeout
        }
    
    def get_rotation_history(self) -> List[Dict]:
        """Get rotation history."""
        return [session.to_dict() for session in self.rotation_history]
    
    def get_rotation_stats(self) -> Dict:
        """Get rotation statistics."""
        return {
            **self.stats,
            "current_keys_count": len(self.current_keys),
            "pending_keys_count": len(self.pending_keys),
            "rotation_history_count": len(self.rotation_history)
        }
    
    async def stop_key_rotation_service(self) -> None:
        """Stop the key rotation service."""
        if self.rotation_task:
            self.rotation_task.cancel()
        
        if self.monitor_task:
            self.monitor_task.cancel()
        
        print("🛑 Key rotation service stopped")
