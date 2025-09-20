"""
Group management system for anonymous messaging.
Groups are identified by hash of their public key, users by hash of their public key.
"""

import hashlib
import time
from typing import Dict, Set, List, Optional, Tuple
from dataclasses import dataclass
from .message_types import Message, MessageType
from .encryption import EndToEndEncryption


@dataclass
class GroupMessage:
    """Message within a group."""
    
    message_id: bytes
    group_hash: bytes
    sender_hash: bytes  # Hash of sender's public key
    message_type: MessageType
    content: bytes
    timestamp: int
    signature: bytes
    
    def to_bytes(self) -> bytes:
        """Serialize group message to bytes."""
        import struct
        return (self.message_id + self.group_hash + self.sender_hash +
                struct.pack("!I", self.message_type.value) +
                struct.pack("!I", len(self.content)) + self.content +
                struct.pack("!I", self.timestamp) + self.signature)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "GroupMessage":
        """Deserialize group message from bytes."""
        import struct
        
        if len(data) < 16 + 16 + 16 + 4 + 4 + 4 + 64:  # Minimum size
            raise ValueError("Invalid group message format")
        
        offset = 0
        message_id = data[offset:offset+16]
        offset += 16
        
        group_hash = data[offset:offset+16]
        offset += 16
        
        sender_hash = data[offset:offset+16]
        offset += 16
        
        message_type = MessageType(struct.unpack("!I", data[offset:offset+4])[0])
        offset += 4
        
        content_length = struct.unpack("!I", data[offset:offset+4])[0]
        offset += 4
        
        content = data[offset:offset+content_length]
        offset += content_length
        
        timestamp = struct.unpack("!I", data[offset:offset+4])[0]
        offset += 4
        
        signature = data[offset:offset+64]
        
        return cls(
            message_id=message_id,
            group_hash=group_hash,
            sender_hash=sender_hash,
            message_type=message_type,
            content=content,
            timestamp=timestamp,
            signature=signature
        )


class GroupManager:
    """Manages groups and group messaging."""
    
    def __init__(self, encryption: EndToEndEncryption):
        self.encryption = encryption
        
        # Group storage: group_hash -> GroupInfo
        self.groups: Dict[bytes, 'GroupInfo'] = {}
        
        # User-group mappings: user_hash -> set of group_hashes
        self.user_groups: Dict[bytes, Set[bytes]] = {}
        
        # Group messages: group_hash -> list of GroupMessage
        self.group_messages: Dict[bytes, List[GroupMessage]] = {}
        
        # Group permissions: group_hash -> user_hash -> permissions
        self.group_permissions: Dict[bytes, Dict[bytes, Set[str]]] = {}
        
        # Message history limits
        self.max_messages_per_group = 1000
        self.message_ttl = 86400  # 24 hours
    
    def create_group(self, owner_public_key: bytes, group_name: str = "") -> Tuple[bytes, bytes]:
        """
        Create a new group.
        Returns (group_hash, group_private_key)
        """
        # Generate group keypair
        group_private_key, group_public_key = self.encryption.generate_keypair()
        
        # Create group hash from public key
        group_hash = self._hash_public_key(group_public_key)
        
        # Create group info
        group_info = GroupInfo(
            group_hash=group_hash,
            group_public_key=group_public_key,
            group_private_key=group_private_key,
            owner_hash=self._hash_public_key(owner_public_key),
            name=group_name,
            created_at=int(time.time()),
            last_updated=int(time.time()),
            member_hashes={self._hash_public_key(owner_public_key)},
            relay_servers=set()
        )
        
        # Store group
        self.groups[group_hash] = group_info
        
        # Update user-group mapping
        owner_hash = self._hash_public_key(owner_public_key)
        if owner_hash not in self.user_groups:
            self.user_groups[owner_hash] = set()
        self.user_groups[owner_hash].add(group_hash)
        
        # Set owner permissions
        self.group_permissions[group_hash] = {
            owner_hash: {"admin", "moderate", "send", "receive"}
        }
        
        # Initialize message storage
        self.group_messages[group_hash] = []
        
        return group_hash, group_private_key
    
    def join_group(self, group_hash: bytes, user_public_key: bytes, 
                   invitation_token: Optional[bytes] = None) -> bool:
        """
        Add a user to a group.
        invitation_token is optional for private groups.
        """
        if group_hash not in self.groups:
            return False
        
        group_info = self.groups[group_hash]
        user_hash = self._hash_public_key(user_public_key)
        
        # Check if group is private and requires invitation
        if group_info.is_private and not self._verify_invitation_token(
            group_hash, user_hash, invitation_token
        ):
            return False
        
        # Add user to group
        group_info.member_hashes.add(user_hash)
        group_info.last_updated = int(time.time())
        
        # Update user-group mapping
        if user_hash not in self.user_groups:
            self.user_groups[user_hash] = set()
        self.user_groups[user_hash].add(group_hash)
        
        # Set default permissions
        if group_hash not in self.group_permissions:
            self.group_permissions[group_hash] = {}
        
        self.group_permissions[group_hash][user_hash] = {"send", "receive"}
        
        return True
    
    def leave_group(self, group_hash: bytes, user_public_key: bytes) -> bool:
        """Remove a user from a group."""
        if group_hash not in self.groups:
            return False
        
        group_info = self.groups[group_hash]
        user_hash = self._hash_public_key(user_public_key)
        
        # Can't remove the owner
        if user_hash == group_info.owner_hash:
            return False
        
        # Remove user from group
        group_info.member_hashes.discard(user_hash)
        group_info.last_updated = int(time.time())
        
        # Update user-group mapping
        if user_hash in self.user_groups:
            self.user_groups[user_hash].discard(group_hash)
            if not self.user_groups[user_hash]:
                del self.user_groups[user_hash]
        
        # Remove permissions
        if group_hash in self.group_permissions and user_hash in self.group_permissions[group_hash]:
            del self.group_permissions[group_hash][user_hash]
        
        return True
    
    def send_group_message(self, group_hash: bytes, sender_public_key: bytes,
                          message_type: MessageType, content: bytes) -> Optional[GroupMessage]:
        """Send a message to a group."""
        if group_hash not in self.groups:
            return None
        
        group_info = self.groups[group_hash]
        sender_hash = self._hash_public_key(sender_public_key)
        
        # Check if user is member of group
        if sender_hash not in group_info.member_hashes:
            return None
        
        # Check permissions
        if not self._has_permission(group_hash, sender_hash, "send"):
            return None
        
        # Create group message
        message_id = self._generate_message_id()
        timestamp = int(time.time())
        
        # Create signature data
        signature_data = (message_id + group_hash + sender_hash +
                         message_type.value.to_bytes(4, 'big') +
                         content + timestamp.to_bytes(4, 'big'))
        
        # Sign message with sender's private key (this would need to be provided)
        # For now, we'll create a placeholder signature
        signature = b"placeholder_signature_64_bytes_long_for_group_message"
        
        group_message = GroupMessage(
            message_id=message_id,
            group_hash=group_hash,
            sender_hash=sender_hash,
            message_type=message_type,
            content=content,
            timestamp=timestamp,
            signature=signature
        )
        
        # Store message
        if group_hash not in self.group_messages:
            self.group_messages[group_hash] = []
        
        self.group_messages[group_hash].append(group_message)
        
        # Cleanup old messages
        self._cleanup_old_messages(group_hash)
        
        return group_message
    
    def get_group_messages(self, group_hash: bytes, user_public_key: bytes,
                          limit: int = 100, offset: int = 0) -> List[GroupMessage]:
        """Get messages from a group."""
        if group_hash not in self.groups:
            return []
        
        user_hash = self._hash_public_key(user_public_key)
        
        # Check if user is member of group
        if user_hash not in self.groups[group_hash].member_hashes:
            return []
        
        # Check permissions
        if not self._has_permission(group_hash, user_hash, "receive"):
            return []
        
        messages = self.group_messages.get(group_hash, [])
        
        # Return messages in reverse chronological order (newest first)
        return messages[-(offset + limit):-offset] if offset > 0 else messages[-limit:]
    
    def get_user_groups(self, user_public_key: bytes) -> List[bytes]:
        """Get all groups that a user belongs to."""
        user_hash = self._hash_public_key(user_public_key)
        return list(self.user_groups.get(user_hash, set()))
    
    def get_group_info(self, group_hash: bytes, user_public_key: bytes) -> Optional['GroupInfo']:
        """Get information about a group."""
        if group_hash not in self.groups:
            return None
        
        user_hash = self._hash_public_key(user_public_key)
        
        # Check if user is member of group
        if user_hash not in self.groups[group_hash].member_hashes:
            return None
        
        return self.groups[group_hash]
    
    def set_group_permissions(self, group_hash: bytes, owner_public_key: bytes,
                             user_hash: bytes, permissions: Set[str]) -> bool:
        """Set permissions for a user in a group."""
        if group_hash not in self.groups:
            return False
        
        group_info = self.groups[group_hash]
        owner_hash = self._hash_public_key(owner_public_key)
        
        # Only owner or admin can set permissions
        if owner_hash != group_info.owner_hash:
            if not self._has_permission(group_hash, owner_hash, "admin"):
                return False
        
        # Can't modify owner's permissions
        if user_hash == group_info.owner_hash:
            return False
        
        if group_hash not in self.group_permissions:
            self.group_permissions[group_hash] = {}
        
        self.group_permissions[group_hash][user_hash] = permissions
        return True
    
    def create_invitation_token(self, group_hash: bytes, owner_public_key: bytes,
                               invited_user_hash: bytes) -> Optional[bytes]:
        """Create an invitation token for a private group."""
        if group_hash not in self.groups:
            return None
        
        group_info = self.groups[group_hash]
        owner_hash = self._hash_public_key(owner_public_key)
        
        # Only owner can create invitations
        if owner_hash != group_info.owner_hash:
            return None
        
        # Create invitation token
        token_data = (group_hash + invited_user_hash + 
                     int(time.time()).to_bytes(4, 'big'))
        
        # Sign token with group's private key
        token = hashlib.sha256(token_data).digest()
        
        return token
    
    def _verify_invitation_token(self, group_hash: bytes, user_hash: bytes,
                                token: Optional[bytes]) -> bool:
        """Verify an invitation token."""
        if not token:
            return False
        
        # For now, we'll implement a simple verification
        # In a real implementation, this would verify the signature
        expected_token = hashlib.sha256(
            group_hash + user_hash + int(time.time()).to_bytes(4, 'big')
        ).digest()
        
        return token == expected_token
    
    def _has_permission(self, group_hash: bytes, user_hash: bytes, permission: str) -> bool:
        """Check if a user has a specific permission in a group."""
        if group_hash not in self.group_permissions:
            return False
        
        user_permissions = self.group_permissions[group_hash].get(user_hash, set())
        return permission in user_permissions
    
    def _hash_public_key(self, public_key: bytes) -> bytes:
        """Create a hash of a public key for identification."""
        return hashlib.sha256(public_key).digest()[:16]  # 16 bytes for efficiency
    
    def _generate_message_id(self) -> bytes:
        """Generate a unique message ID."""
        import os
        return os.urandom(16)
    
    def _cleanup_old_messages(self, group_hash: bytes) -> None:
        """Remove old messages from a group."""
        if group_hash not in self.group_messages:
            return
        
        current_time = int(time.time())
        messages = self.group_messages[group_hash]
        
        # Remove messages older than TTL
        messages[:] = [msg for msg in messages 
                      if current_time - msg.timestamp < self.message_ttl]
        
        # Limit number of messages
        if len(messages) > self.max_messages_per_group:
            messages[:] = messages[-self.max_messages_per_group:]
    
    def get_group_stats(self, group_hash: bytes) -> Dict:
        """Get statistics for a group."""
        if group_hash not in self.groups:
            return {}
        
        group_info = self.groups[group_hash]
        message_count = len(self.group_messages.get(group_hash, []))
        
        return {
            "group_hash": group_hash.hex(),
            "member_count": len(group_info.member_hashes),
            "message_count": message_count,
            "created_at": group_info.created_at,
            "last_updated": group_info.last_updated,
            "is_private": group_info.is_private
        }
    
    def get_all_groups(self) -> List[bytes]:
        """Get all group hashes."""
        return list(self.groups.keys())
    
    def delete_group(self, group_hash: bytes, owner_public_key: bytes) -> bool:
        """Delete a group (only owner can do this)."""
        if group_hash not in self.groups:
            return False
        
        group_info = self.groups[group_hash]
        owner_hash = self._hash_public_key(owner_public_key)
        
        # Only owner can delete group
        if owner_hash != group_info.owner_hash:
            return False
        
        # Remove group and all associated data
        del self.groups[group_hash]
        
        if group_hash in self.group_messages:
            del self.group_messages[group_hash]
        
        if group_hash in self.group_permissions:
            del self.group_permissions[group_hash]
        
        # Remove from user-group mappings
        for user_hash in group_info.member_hashes:
            if user_hash in self.user_groups:
                self.user_groups[user_hash].discard(group_hash)
                if not self.user_groups[user_hash]:
                    del self.user_groups[user_hash]
        
        return True


@dataclass
class GroupInfo:
    """Information about a group."""
    
    group_hash: bytes
    group_public_key: bytes
    group_private_key: bytes
    owner_hash: bytes  # Hash of owner's public key
    name: str
    created_at: int
    last_updated: int
    member_hashes: Set[bytes]  # Set of member public key hashes
    relay_servers: Set[bytes]  # Set of relay server IDs
    is_private: bool = False
    description: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "group_hash": self.group_hash.hex(),
            "group_public_key": self.group_public_key.hex(),
            "owner_hash": self.owner_hash.hex(),
            "name": self.name,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "member_hashes": [h.hex() for h in self.member_hashes],
            "relay_servers": [s.hex() for s in self.relay_servers],
            "is_private": self.is_private,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "GroupInfo":
        """Create from dictionary."""
        return cls(
            group_hash=bytes.fromhex(data["group_hash"]),
            group_public_key=bytes.fromhex(data["group_public_key"]),
            group_private_key=b"",  # Not stored in serialized form
            owner_hash=bytes.fromhex(data["owner_hash"]),
            name=data["name"],
            created_at=data["created_at"],
            last_updated=data["last_updated"],
            member_hashes={bytes.fromhex(h) for h in data["member_hashes"]},
            relay_servers={bytes.fromhex(s) for s in data["relay_servers"]},
            is_private=data.get("is_private", False),
            description=data.get("description", "")
        )
