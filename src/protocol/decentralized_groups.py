"""
Decentralized Group Management System.
Implements secure group management where groups are stored only on the creator's client
with a list of public key hashes, and messages are encrypted individually for each member.
"""

import asyncio
import hashlib
import json
import os
import time
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

from .encryption import EndToEndEncryption
from .message_types import MessageType, Message, HashIdentity


class GroupRole(Enum):
    """Roles in a group."""
    
    OWNER = "owner"
    MEMBER = "member"


class GroupStatus(Enum):
    """Status of a group."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


@dataclass
class GroupMember:
    """Group member information."""
    
    user_hash: bytes                    # Hash of user's public key
    public_key: bytes                   # User's public key
    role: GroupRole                     # Member role
    joined_at: int                      # When member joined
    last_seen: int                      # Last seen timestamp
    is_active: bool = True              # Whether member is active
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "user_hash": self.user_hash.hex(),
            "public_key": self.public_key.hex(),
            "role": self.role.value,
            "joined_at": self.joined_at,
            "last_seen": self.last_seen,
            "is_active": self.is_active
        }


@dataclass
class DecentralizedGroup:
    """Decentralized group managed by owner only."""
    
    group_id: bytes                     # Unique group identifier
    group_hash: bytes                   # Hash of group (for verification)
    owner_hash: bytes                   # Hash of owner's public key
    owner_public_key: bytes             # Owner's public key
    group_name: str                     # Group name
    description: str                    # Group description
    created_at: int                     # Creation timestamp
    status: GroupStatus                 # Group status
    members: Dict[bytes, GroupMember]   # user_hash -> GroupMember
    max_members: int = 100              # Maximum number of members
    is_private: bool = True             # Whether group is private
    
    def __post_init__(self):
        """Initialize group hash."""
        if not hasattr(self, 'group_hash') or not self.group_hash:
            self.group_hash = self._generate_group_hash()
    
    def _generate_group_hash(self) -> bytes:
        """Generate group hash for verification."""
        group_data = (
            self.group_id +
            self.owner_hash +
            self.group_name.encode() +
            str(self.created_at).encode()
        )
        return hashlib.sha256(group_data).digest()[:16]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "group_id": self.group_id.hex(),
            "group_hash": self.group_hash.hex(),
            "owner_hash": self.owner_hash.hex(),
            "owner_public_key": self.owner_public_key.hex(),
            "group_name": self.group_name,
            "description": self.description,
            "created_at": self.created_at,
            "status": self.status.value,
            "members": {user_hash.hex(): member.to_dict() for user_hash, member in self.members.items()},
            "max_members": self.max_members,
            "is_private": self.is_private
        }


@dataclass
class GroupMessage:
    """Group message with individual encryption for each member."""
    
    message_id: bytes                   # Unique message identifier
    group_id: bytes                     # Group identifier
    sender_hash: bytes                  # Hash of sender's public key
    sender_public_key: bytes            # Sender's public key
    message_type: MessageType           # Type of message
    encrypted_messages: Dict[bytes, bytes]  # user_hash -> encrypted_message
    timestamp: int                      # Message timestamp
    ttl: int = 3600                     # Time to live in seconds
    signature: bytes                    # Message signature
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "message_id": self.message_id.hex(),
            "group_id": self.group_id.hex(),
            "sender_hash": self.sender_hash.hex(),
            "sender_public_key": self.sender_public_key.hex(),
            "message_type": self.message_type.value,
            "encrypted_messages": {user_hash.hex(): msg.hex() for user_hash, msg in self.encrypted_messages.items()},
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "signature": self.signature.hex()
        }


@dataclass
class GroupSubscription:
    """Group subscription for a user."""
    
    user_hash: bytes                    # Hash of user's public key
    group_id: bytes                     # Group identifier
    group_hash: bytes                   # Group hash for verification
    subscribed_at: int                  # Subscription timestamp
    last_message_id: Optional[bytes] = None  # Last received message ID
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "user_hash": self.user_hash.hex(),
            "group_id": self.group_id.hex(),
            "group_hash": self.group_hash.hex(),
            "subscribed_at": self.subscribed_at,
            "last_message_id": self.last_message_id.hex() if self.last_message_id else None
        }


class DecentralizedGroupManager:
    """Decentralized group management system."""
    
    def __init__(self, encryption: EndToEndEncryption):
        self.encryption = encryption
        
        # Group storage (only on owner's client)
        self.owned_groups: Dict[bytes, DecentralizedGroup] = {}  # group_id -> group
        
        # User subscriptions (on each user's client)
        self.user_subscriptions: Dict[bytes, Set[bytes]] = defaultdict(set)  # user_hash -> group_ids
        self.subscription_details: Dict[bytes, GroupSubscription] = {}  # (user_hash, group_id) -> subscription
        
        # Message storage (temporary on server)
        self.pending_messages: Dict[bytes, GroupMessage] = {}  # message_id -> message
        self.delivered_messages: Set[bytes] = set()  # Delivered message IDs
        
        # Statistics
        self.stats = {
            "groups_created": 0,
            "groups_joined": 0,
            "messages_sent": 0,
            "messages_delivered": 0,
            "members_added": 0,
            "members_removed": 0
        }
    
    # Group Management (Owner Only)
    
    async def create_group(self, owner_hash: bytes, owner_public_key: bytes, 
                          group_name: str, description: str = "", 
                          max_members: int = 100, is_private: bool = True) -> Optional[DecentralizedGroup]:
        """Create a new group (owner only)."""
        try:
            # Generate unique group ID
            group_id = hashlib.sha256(
                owner_hash + group_name.encode() + str(time.time()).encode()
            ).digest()[:16]
            
            # Create group
            group = DecentralizedGroup(
                group_id=group_id,
                group_hash=b"",  # Will be generated in __post_init__
                owner_hash=owner_hash,
                owner_public_key=owner_public_key,
                group_name=group_name,
                description=description,
                created_at=int(time.time()),
                status=GroupStatus.ACTIVE,
                members={},
                max_members=max_members,
                is_private=is_private
            )
            
            # Add owner as first member
            owner_member = GroupMember(
                user_hash=owner_hash,
                public_key=owner_public_key,
                role=GroupRole.OWNER,
                joined_at=int(time.time()),
                last_seen=int(time.time())
            )
            group.members[owner_hash] = owner_member
            
            # Store group (only on owner's client)
            self.owned_groups[group_id] = group
            
            self.stats["groups_created"] += 1
            return group
            
        except Exception as e:
            print(f"❌ Failed to create group: {e}")
            return None
    
    async def add_member(self, group_id: bytes, owner_hash: bytes, 
                        new_member_hash: bytes, new_member_public_key: bytes) -> bool:
        """Add a member to a group (owner only)."""
        try:
            if group_id not in self.owned_groups:
                print(f"❌ Group {group_id.hex()} not found")
                return False
            
            group = self.owned_groups[group_id]
            
            # Verify owner
            if group.owner_hash != owner_hash:
                print(f"❌ Only group owner can add members")
                return False
            
            # Check if group is full
            if len(group.members) >= group.max_members:
                print(f"❌ Group is full (max {group.max_members} members)")
                return False
            
            # Check if member already exists
            if new_member_hash in group.members:
                print(f"❌ Member already exists in group")
                return False
            
            # Add new member
            new_member = GroupMember(
                user_hash=new_member_hash,
                public_key=new_member_public_key,
                role=GroupRole.MEMBER,
                joined_at=int(time.time()),
                last_seen=int(time.time())
            )
            group.members[new_member_hash] = new_member
            
            self.stats["members_added"] += 1
            return True
            
        except Exception as e:
            print(f"❌ Failed to add member: {e}")
            return False
    
    async def remove_member(self, group_id: bytes, owner_hash: bytes, 
                           member_hash: bytes) -> bool:
        """Remove a member from a group (owner only)."""
        try:
            if group_id not in self.owned_groups:
                print(f"❌ Group {group_id.hex()} not found")
                return False
            
            group = self.owned_groups[group_id]
            
            # Verify owner
            if group.owner_hash != owner_hash:
                print(f"❌ Only group owner can remove members")
                return False
            
            # Check if member exists
            if member_hash not in group.members:
                print(f"❌ Member not found in group")
                return False
            
            # Don't allow removing the owner
            if member_hash == owner_hash:
                print(f"❌ Cannot remove group owner")
                return False
            
            # Remove member
            del group.members[member_hash]
            
            self.stats["members_removed"] += 1
            return True
            
        except Exception as e:
            print(f"❌ Failed to remove member: {e}")
            return False
    
    async def delete_group(self, group_id: bytes, owner_hash: bytes) -> bool:
        """Delete a group (owner only)."""
        try:
            if group_id not in self.owned_groups:
                print(f"❌ Group {group_id.hex()} not found")
                return False
            
            group = self.owned_groups[group_id]
            
            # Verify owner
            if group.owner_hash != owner_hash:
                print(f"❌ Only group owner can delete group")
                return False
            
            # Mark group as deleted
            group.status = GroupStatus.DELETED
            
            # Remove from owned groups
            del self.owned_groups[group_id]
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete group: {e}")
            return False
    
    # Group Information (Owner Only)
    
    def get_group_info(self, group_id: bytes, owner_hash: bytes) -> Optional[Dict]:
        """Get group information (owner only)."""
        if group_id not in self.owned_groups:
            return None
        
        group = self.owned_groups[group_id]
        
        # Verify owner
        if group.owner_hash != owner_hash:
            return None
        
        return group.to_dict()
    
    def get_owned_groups(self, owner_hash: bytes) -> List[Dict]:
        """Get all groups owned by a user."""
        owned_groups = []
        for group_id, group in self.owned_groups.items():
            if group.owner_hash == owner_hash:
                owned_groups.append(group.to_dict())
        return owned_groups
    
    # Group Subscription (Members)
    
    async def join_group(self, user_hash: bytes, group_id: bytes, 
                        group_hash: bytes, group_info: Dict) -> bool:
        """Join a group (member)."""
        try:
            # Verify group hash
            expected_hash = hashlib.sha256(
                bytes.fromhex(group_info["group_id"]) +
                bytes.fromhex(group_info["owner_hash"]) +
                group_info["group_name"].encode() +
                str(group_info["created_at"]).encode()
            ).digest()[:16]
            
            if expected_hash != group_hash:
                print(f"❌ Invalid group hash")
                return False
            
            # Create subscription
            subscription = GroupSubscription(
                user_hash=user_hash,
                group_id=group_id,
                group_hash=group_hash,
                subscribed_at=int(time.time())
            )
            
            # Store subscription
            self.user_subscriptions[user_hash].add(group_id)
            self.subscription_details[(user_hash, group_id)] = subscription
            
            self.stats["groups_joined"] += 1
            return True
            
        except Exception as e:
            print(f"❌ Failed to join group: {e}")
            return False
    
    async def leave_group(self, user_hash: bytes, group_id: bytes) -> bool:
        """Leave a group (member)."""
        try:
            # Remove subscription
            if user_hash in self.user_subscriptions:
                self.user_subscriptions[user_hash].discard(group_id)
            
            # Remove subscription details
            subscription_key = (user_hash, group_id)
            if subscription_key in self.subscription_details:
                del self.subscription_details[subscription_key]
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to leave group: {e}")
            return False
    
    def get_user_groups(self, user_hash: bytes) -> List[Dict]:
        """Get all groups a user is subscribed to."""
        user_groups = []
        for group_id in self.user_subscriptions[user_hash]:
            subscription_key = (user_hash, group_id)
            if subscription_key in self.subscription_details:
                subscription = self.subscription_details[subscription_key]
                user_groups.append({
                    "group_id": group_id.hex(),
                    "group_hash": subscription.group_hash.hex(),
                    "subscribed_at": subscription.subscribed_at,
                    "last_message_id": subscription.last_message_id.hex() if subscription.last_message_id else None
                })
        return user_groups
    
    # Message Handling
    
    async def send_group_message(self, group_id: bytes, sender_hash: bytes, 
                                sender_public_key: bytes, message_type: MessageType,
                                content: bytes) -> Optional[bytes]:
        """Send a message to a group (owner only)."""
        try:
            if group_id not in self.owned_groups:
                print(f"❌ Group {group_id.hex()} not found")
                return None
            
            group = self.owned_groups[group_id]
            
            # Verify sender is group owner
            if group.owner_hash != sender_hash:
                print(f"❌ Only group owner can send messages")
                return None
            
            # Generate message ID
            message_id = hashlib.sha256(
                group_id + sender_hash + content + str(time.time()).encode()
            ).digest()[:16]
            
            # Encrypt message for each member
            encrypted_messages = {}
            for member_hash, member in group.members.items():
                if member_hash != sender_hash:  # Don't encrypt for self
                    try:
                        encrypted_message = self.encryption.encrypt_message(content, member.public_key)
                        encrypted_messages[member_hash] = encrypted_message
                    except Exception as e:
                        print(f"❌ Failed to encrypt message for member {member_hash.hex()}: {e}")
                        continue
            
            # Create message signature
            signature = self._sign_message(message_id, group_id, sender_hash, content)
            
            # Create group message
            group_message = GroupMessage(
                message_id=message_id,
                group_id=group_id,
                sender_hash=sender_hash,
                sender_public_key=sender_public_key,
                message_type=message_type,
                encrypted_messages=encrypted_messages,
                timestamp=int(time.time()),
                signature=signature
            )
            
            # Store message (temporary on server)
            self.pending_messages[message_id] = group_message
            
            self.stats["messages_sent"] += 1
            return message_id
            
        except Exception as e:
            print(f"❌ Failed to send group message: {e}")
            return None
    
    async def deliver_group_message(self, message_id: bytes, recipient_hash: bytes) -> Optional[bytes]:
        """Deliver a group message to a recipient."""
        try:
            if message_id not in self.pending_messages:
                print(f"❌ Message {message_id.hex()} not found")
                return None
            
            message = self.pending_messages[message_id]
            
            # Check if recipient is in the message
            if recipient_hash not in message.encrypted_messages:
                print(f"❌ Recipient {recipient_hash.hex()} not in message recipients")
                return None
            
            # Get encrypted message for recipient
            encrypted_message = message.encrypted_messages[recipient_hash]
            
            # Update subscription last message ID
            subscription_key = (recipient_hash, message.group_id)
            if subscription_key in self.subscription_details:
                self.subscription_details[subscription_key].last_message_id = message_id
            
            self.stats["messages_delivered"] += 1
            return encrypted_message
            
        except Exception as e:
            print(f"❌ Failed to deliver group message: {e}")
            return None
    
    async def cleanup_delivered_message(self, message_id: bytes) -> None:
        """Clean up a delivered message."""
        try:
            if message_id in self.pending_messages:
                # Check if all recipients have been delivered
                message = self.pending_messages[message_id]
                
                # For now, we'll clean up after a timeout
                # In a real implementation, you'd track delivery status
                if time.time() - message.timestamp > message.ttl:
                    del self.pending_messages[message_id]
                    self.delivered_messages.add(message_id)
                    
        except Exception as e:
            print(f"❌ Failed to cleanup message: {e}")
    
    def _sign_message(self, message_id: bytes, group_id: bytes, 
                     sender_hash: bytes, content: bytes) -> bytes:
        """Sign a message for integrity verification."""
        try:
            # Create message hash
            message_data = message_id + group_id + sender_hash + content
            message_hash = hashlib.sha256(message_data).digest()
            
            # Sign with sender's private key (simplified)
            # In real implementation, use actual private key
            signature = hashlib.hmac.new(
                sender_hash, message_hash, hashlib.sha256
            ).digest()
            
            return signature
            
        except Exception as e:
            print(f"❌ Failed to sign message: {e}")
            return b""
    
    # Public API
    
    def get_group_manager_stats(self) -> Dict:
        """Get group manager statistics."""
        return {
            **self.stats,
            "owned_groups_count": len(self.owned_groups),
            "total_subscriptions": sum(len(groups) for groups in self.user_subscriptions.values()),
            "pending_messages_count": len(self.pending_messages),
            "delivered_messages_count": len(self.delivered_messages)
        }
    
    def get_pending_messages(self, user_hash: bytes) -> List[Dict]:
        """Get pending messages for a user."""
        pending_messages = []
        for group_id in self.user_subscriptions[user_hash]:
            for message_id, message in self.pending_messages.items():
                if message.group_id == group_id and user_hash in message.encrypted_messages:
                    pending_messages.append({
                        "message_id": message_id.hex(),
                        "group_id": message.group_id.hex(),
                        "sender_hash": message.sender_hash.hex(),
                        "message_type": message.message_type.value,
                        "timestamp": message.timestamp,
                        "encrypted_message": message.encrypted_messages[user_hash].hex()
                    })
        return pending_messages
