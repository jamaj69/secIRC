"""
PubSub Server for Group Message Distribution.
Implements a publish-subscribe server for distributing encrypted group messages
with proper group key management and automatic message cleanup.
"""

import asyncio
import hashlib
import json
import os
import time
from typing import Dict, List, Set, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import struct

from .encryption import EndToEndEncryption
from .message_types import MessageType, Message, HashIdentity


class PubSubEvent(Enum):
    """Types of pubsub events."""
    
    MESSAGE_PUBLISHED = "message_published"
    MESSAGE_DELIVERED = "message_delivered"
    MESSAGE_FAILED = "message_failed"
    GROUP_JOINED = "group_joined"
    GROUP_LEFT = "group_left"
    KEY_ROTATED = "key_rotated"
    MESSAGE_CLEANED = "message_cleaned"


class GroupKeyType(Enum):
    """Types of group keys."""
    
    SHARED_SECRET = "shared_secret"      # Shared secret key
    KEY_AGREEMENT = "key_agreement"      # Key agreement protocol
    HYBRID = "hybrid"                    # Hybrid approach


@dataclass
class GroupKey:
    """Group encryption key."""
    
    group_id: bytes                      # Group identifier
    key_id: bytes                        # Key identifier
    key_type: GroupKeyType               # Type of key
    encrypted_key: bytes                 # Encrypted group key
    key_encryption_keys: Dict[bytes, bytes]  # User ID -> encrypted key
    created_at: int                      # Creation timestamp
    expires_at: int                      # Expiration timestamp
    version: int                         # Key version
    is_active: bool = True               # Whether key is active
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "group_id": self.group_id.hex(),
            "key_id": self.key_id.hex(),
            "key_type": self.key_type.value,
            "encrypted_key": self.encrypted_key.hex(),
            "key_encryption_keys": {user_id.hex(): key.hex() for user_id, key in self.key_encryption_keys.items()},
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "version": self.version,
            "is_active": self.is_active
        }


@dataclass
class GroupMessage:
    """Group message for pubsub distribution."""
    
    message_id: bytes                    # Unique message identifier
    group_id: bytes                      # Group identifier
    sender_id: bytes                     # Sender identifier
    encrypted_content: bytes             # Encrypted message content
    key_id: bytes                        # Group key identifier
    timestamp: int                       # Message timestamp
    ttl: int                             # Time to live in seconds
    delivery_attempts: int = 0           # Number of delivery attempts
    max_delivery_attempts: int = 3       # Maximum delivery attempts
    is_delivered: bool = False           # Whether message was delivered
    recipients: Set[bytes] = None        # Set of recipient IDs
    
    def __post_init__(self):
        """Initialize recipients set if not provided."""
        if self.recipients is None:
            self.recipients = set()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "message_id": self.message_id.hex(),
            "group_id": self.group_id.hex(),
            "sender_id": self.sender_id.hex(),
            "encrypted_content": self.encrypted_content.hex(),
            "key_id": self.key_id.hex(),
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "delivery_attempts": self.delivery_attempts,
            "max_delivery_attempts": self.max_delivery_attempts,
            "is_delivered": self.is_delivered,
            "recipients": [recipient.hex() for recipient in self.recipients]
        }


@dataclass
class GroupSubscription:
    """Group subscription for a user."""
    
    user_id: bytes                       # User identifier
    group_id: bytes                      # Group identifier
    subscribed_at: int                   # Subscription timestamp
    last_seen: int                       # Last seen timestamp
    is_active: bool = True               # Whether subscription is active
    delivery_preferences: Dict[str, Any] = None  # Delivery preferences
    
    def __post_init__(self):
        """Initialize delivery preferences if not provided."""
        if self.delivery_preferences is None:
            self.delivery_preferences = {
                "max_retries": 3,
                "retry_interval": 60,
                "priority": "normal"
            }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "user_id": self.user_id.hex(),
            "group_id": self.group_id.hex(),
            "subscribed_at": self.subscribed_at,
            "last_seen": self.last_seen,
            "is_active": self.is_active,
            "delivery_preferences": self.delivery_preferences
        }


@dataclass
class PubSubEvent:
    """PubSub event for monitoring."""
    
    event_type: PubSubEvent
    group_id: bytes
    user_id: Optional[bytes]
    message_id: Optional[bytes]
    timestamp: int
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "group_id": self.group_id.hex(),
            "user_id": self.user_id.hex() if self.user_id else None,
            "message_id": self.message_id.hex() if self.message_id else None,
            "timestamp": self.timestamp,
            "data": self.data
        }


class PubSubServer:
    """PubSub server for group message distribution with group key management."""
    
    def __init__(self, encryption: EndToEndEncryption):
        self.encryption = encryption
        
        # Group management
        self.groups: Dict[bytes, Dict[str, Any]] = {}  # group_id -> group info
        self.group_subscriptions: Dict[bytes, Set[bytes]] = defaultdict(set)  # group_id -> user_ids
        self.user_subscriptions: Dict[bytes, Set[bytes]] = defaultdict(set)  # user_id -> group_ids
        
        # Group key management
        self.group_keys: Dict[bytes, List[GroupKey]] = defaultdict(list)  # group_id -> keys
        self.active_group_keys: Dict[bytes, GroupKey] = {}  # group_id -> active key
        
        # Message management
        self.pending_messages: Dict[bytes, GroupMessage] = {}  # message_id -> message
        self.message_queue: deque = deque()  # Message delivery queue
        self.delivered_messages: Set[bytes] = set()  # Delivered message IDs
        
        # Event handling
        self.event_handlers: Dict[PubSubEvent, List[Callable]] = defaultdict(list)
        self.event_history: deque = deque(maxlen=1000)  # Event history
        
        # Configuration
        self.max_message_ttl = 3600  # 1 hour
        self.max_delivery_attempts = 3
        self.cleanup_interval = 300  # 5 minutes
        self.key_rotation_interval = 86400  # 24 hours
        
        # Statistics
        self.stats = {
            "messages_published": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "messages_cleaned": 0,
            "groups_created": 0,
            "users_subscribed": 0,
            "keys_rotated": 0,
            "events_processed": 0
        }
        
        # Background tasks
        self.delivery_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.key_rotation_task: Optional[asyncio.Task] = None
    
    async def start_pubsub_service(self) -> None:
        """Start the pubsub service."""
        print("📢 Starting PubSub service...")
        
        # Start background tasks
        self.delivery_task = asyncio.create_task(self._message_delivery_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.key_rotation_task = asyncio.create_task(self._key_rotation_loop())
        
        print("✅ PubSub service started")
    
    # Group Management
    
    async def create_group(self, group_id: bytes, creator_id: bytes, group_info: Dict[str, Any]) -> bool:
        """Create a new group with initial key."""
        try:
            # Create group
            self.groups[group_id] = {
                "group_id": group_id.hex(),
                "creator_id": creator_id.hex(),
                "created_at": int(time.time()),
                "member_count": 1,
                "is_active": True,
                **group_info
            }
            
            # Add creator as first member
            await self._add_group_member(group_id, creator_id)
            
            # Generate initial group key
            await self._generate_group_key(group_id, creator_id)
            
            # Emit event
            await self._emit_event(PubSubEvent.GROUP_JOINED, group_id, creator_id, None, {
                "action": "group_created",
                "creator_id": creator_id.hex()
            })
            
            self.stats["groups_created"] += 1
            return True
            
        except Exception as e:
            print(f"❌ Failed to create group: {e}")
            return False
    
    async def join_group(self, group_id: bytes, user_id: bytes) -> bool:
        """Join a group and receive group key."""
        try:
            if group_id not in self.groups:
                print(f"❌ Group {group_id.hex()} does not exist")
                return False
            
            # Add user to group
            await self._add_group_member(group_id, user_id)
            
            # Generate new group key with user included
            await self._generate_group_key(group_id, user_id)
            
            # Emit event
            await self._emit_event(PubSubEvent.GROUP_JOINED, group_id, user_id, None, {
                "action": "user_joined",
                "user_id": user_id.hex()
            })
            
            self.stats["users_subscribed"] += 1
            return True
            
        except Exception as e:
            print(f"❌ Failed to join group: {e}")
            return False
    
    async def leave_group(self, group_id: bytes, user_id: bytes) -> bool:
        """Leave a group and rotate group key."""
        try:
            if group_id not in self.groups:
                return False
            
            # Remove user from group
            await self._remove_group_member(group_id, user_id)
            
            # Rotate group key to exclude user
            await self._rotate_group_key(group_id, user_id)
            
            # Emit event
            await self._emit_event(PubSubEvent.GROUP_LEFT, group_id, user_id, None, {
                "action": "user_left",
                "user_id": user_id.hex()
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to leave group: {e}")
            return False
    
    async def _add_group_member(self, group_id: bytes, user_id: bytes) -> None:
        """Add user to group."""
        self.group_subscriptions[group_id].add(user_id)
        self.user_subscriptions[user_id].add(group_id)
        self.groups[group_id]["member_count"] = len(self.group_subscriptions[group_id])
    
    async def _remove_group_member(self, group_id: bytes, user_id: bytes) -> None:
        """Remove user from group."""
        self.group_subscriptions[group_id].discard(user_id)
        self.user_subscriptions[user_id].discard(group_id)
        self.groups[group_id]["member_count"] = len(self.group_subscriptions[group_id])
    
    # Group Key Management
    
    async def _generate_group_key(self, group_id: bytes, requesting_user_id: bytes) -> GroupKey:
        """Generate a new group key."""
        try:
            # Generate shared secret key
            group_secret = os.urandom(32)  # 256-bit key
            
            # Create key ID
            key_id = hashlib.sha256(group_secret + group_id + str(time.time()).encode()).digest()[:16]
            
            # Get group members
            group_members = self.group_subscriptions[group_id]
            
            # Encrypt group key for each member
            key_encryption_keys = {}
            for user_id in group_members:
                # Get user's public key (simplified - in real implementation, fetch from identity system)
                user_public_key = await self._get_user_public_key(user_id)
                
                # Encrypt group key with user's public key
                encrypted_key = self.encryption.encrypt_message(group_secret, user_public_key)
                key_encryption_keys[user_id] = encrypted_key
            
            # Create group key
            group_key = GroupKey(
                group_id=group_id,
                key_id=key_id,
                key_type=GroupKeyType.SHARED_SECRET,
                encrypted_key=group_secret,  # Store plain key for server use
                key_encryption_keys=key_encryption_keys,
                created_at=int(time.time()),
                expires_at=int(time.time()) + self.key_rotation_interval,
                version=len(self.group_keys[group_id]) + 1
            )
            
            # Store group key
            self.group_keys[group_id].append(group_key)
            self.active_group_keys[group_id] = group_key
            
            # Emit event
            await self._emit_event(PubSubEvent.KEY_ROTATED, group_id, requesting_user_id, None, {
                "action": "key_generated",
                "key_id": key_id.hex(),
                "version": group_key.version,
                "member_count": len(group_members)
            })
            
            return group_key
            
        except Exception as e:
            print(f"❌ Failed to generate group key: {e}")
            raise
    
    async def _rotate_group_key(self, group_id: bytes, excluded_user_id: Optional[bytes] = None) -> GroupKey:
        """Rotate group key, optionally excluding a user."""
        try:
            # Get current group members
            group_members = self.group_subscriptions[group_id].copy()
            
            # Remove excluded user if specified
            if excluded_user_id:
                group_members.discard(excluded_user_id)
            
            if not group_members:
                print(f"❌ No members left in group {group_id.hex()}")
                return None
            
            # Generate new group key
            new_group_key = await self._generate_group_key(group_id, list(group_members)[0])
            
            # Emit event
            await self._emit_event(PubSubEvent.KEY_ROTATED, group_id, None, None, {
                "action": "key_rotated",
                "key_id": new_group_key.key_id.hex(),
                "version": new_group_key.version,
                "excluded_user": excluded_user_id.hex() if excluded_user_id else None
            })
            
            self.stats["keys_rotated"] += 1
            return new_group_key
            
        except Exception as e:
            print(f"❌ Failed to rotate group key: {e}")
            raise
    
    async def _get_user_public_key(self, user_id: bytes) -> bytes:
        """Get user's public key (simplified implementation)."""
        # In real implementation, fetch from identity system
        # For now, generate a dummy key
        return os.urandom(32)
    
    # Message Publishing and Distribution
    
    async def publish_message(self, group_id: bytes, sender_id: bytes, content: bytes) -> Optional[bytes]:
        """Publish a message to a group."""
        try:
            if group_id not in self.groups:
                print(f"❌ Group {group_id.hex()} does not exist")
                return None
            
            if sender_id not in self.group_subscriptions[group_id]:
                print(f"❌ User {sender_id.hex()} is not a member of group {group_id.hex()}")
                return None
            
            # Get active group key
            if group_id not in self.active_group_keys:
                print(f"❌ No active key for group {group_id.hex()}")
                return None
            
            group_key = self.active_group_keys[group_id]
            
            # Encrypt message with group key
            encrypted_content = self.encryption.encrypt_message(content, group_key.encrypted_key)
            
            # Create message ID
            message_id = hashlib.sha256(
                group_id + sender_id + encrypted_content + str(time.time()).encode()
            ).digest()[:16]
            
            # Create group message
            group_message = GroupMessage(
                message_id=message_id,
                group_id=group_id,
                sender_id=sender_id,
                encrypted_content=encrypted_content,
                key_id=group_key.key_id,
                timestamp=int(time.time()),
                ttl=self.max_message_ttl,
                recipients=self.group_subscriptions[group_id].copy()
            )
            
            # Remove sender from recipients (don't send to self)
            group_message.recipients.discard(sender_id)
            
            # Store message
            self.pending_messages[message_id] = group_message
            self.message_queue.append(message_id)
            
            # Emit event
            await self._emit_event(PubSubEvent.MESSAGE_PUBLISHED, group_id, sender_id, message_id, {
                "action": "message_published",
                "recipient_count": len(group_message.recipients),
                "key_id": group_key.key_id.hex()
            })
            
            self.stats["messages_published"] += 1
            return message_id
            
        except Exception as e:
            print(f"❌ Failed to publish message: {e}")
            return None
    
    async def _message_delivery_loop(self) -> None:
        """Main message delivery loop."""
        while True:
            try:
                # Process messages in queue
                if self.message_queue:
                    message_id = self.message_queue.popleft()
                    await self._deliver_message(message_id)
                
                # Wait before next iteration
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Message delivery error: {e}")
                await asyncio.sleep(1)
    
    async def _deliver_message(self, message_id: bytes) -> None:
        """Deliver a message to all recipients."""
        try:
            if message_id not in self.pending_messages:
                return
            
            message = self.pending_messages[message_id]
            
            # Check if message has expired
            if time.time() - message.timestamp > message.ttl:
                await self._cleanup_message(message_id)
                return
            
            # Check if message has exceeded max delivery attempts
            if message.delivery_attempts >= message.max_delivery_attempts:
                await self._cleanup_message(message_id)
                return
            
            # Get group key
            if message.group_id not in self.active_group_keys:
                await self._cleanup_message(message_id)
                return
            
            group_key = self.active_group_keys[message.group_id]
            
            # Deliver to each recipient
            delivered_count = 0
            failed_count = 0
            
            for recipient_id in list(message.recipients):
                try:
                    # Get recipient's encrypted group key
                    if recipient_id not in group_key.key_encryption_keys:
                        print(f"❌ No group key for recipient {recipient_id.hex()}")
                        failed_count += 1
                        continue
                    
                    recipient_encrypted_key = group_key.key_encryption_keys[recipient_id]
                    
                    # Create delivery message
                    delivery_message = {
                        "type": "group_message",
                        "message_id": message_id.hex(),
                        "group_id": message.group_id.hex(),
                        "sender_id": message.sender_id.hex(),
                        "encrypted_content": message.encrypted_content.hex(),
                        "key_id": message.key_id.hex(),
                        "encrypted_group_key": recipient_encrypted_key.hex(),
                        "timestamp": message.timestamp
                    }
                    
                    # Send message to recipient (simplified)
                    success = await self._send_message_to_user(recipient_id, delivery_message)
                    
                    if success:
                        delivered_count += 1
                        message.recipients.discard(recipient_id)
                        
                        # Emit delivery event
                        await self._emit_event(PubSubEvent.MESSAGE_DELIVERED, message.group_id, recipient_id, message_id, {
                            "action": "message_delivered",
                            "recipient_id": recipient_id.hex()
                        })
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    print(f"❌ Failed to deliver message to {recipient_id.hex()}: {e}")
                    failed_count += 1
            
            # Update delivery attempts
            message.delivery_attempts += 1
            
            # Check if all recipients have been delivered
            if not message.recipients:
                message.is_delivered = True
                await self._cleanup_message(message_id)
                self.stats["messages_delivered"] += 1
            else:
                # Re-queue message for retry
                self.message_queue.append(message_id)
                
                if failed_count > 0:
                    # Emit failure event
                    await self._emit_event(PubSubEvent.MESSAGE_FAILED, message.group_id, None, message_id, {
                        "action": "delivery_failed",
                        "failed_count": failed_count,
                        "remaining_recipients": len(message.recipients)
                    })
            
        except Exception as e:
            print(f"❌ Failed to deliver message {message_id.hex()}: {e}")
            await self._cleanup_message(message_id)
    
    async def _send_message_to_user(self, user_id: bytes, message: Dict[str, Any]) -> bool:
        """Send message to user (simplified implementation)."""
        try:
            # In real implementation, send via network
            # For now, simulate successful delivery
            await asyncio.sleep(0.01)  # Simulate network delay
            return True
            
        except Exception as e:
            print(f"❌ Failed to send message to user {user_id.hex()}: {e}")
            return False
    
    # Message Cleanup
    
    async def _cleanup_loop(self) -> None:
        """Main cleanup loop."""
        while True:
            try:
                # Clean up expired messages
                await self._cleanup_expired_messages()
                
                # Clean up old events
                await self._cleanup_old_events()
                
                # Wait before next cleanup
                await asyncio.sleep(self.cleanup_interval)
                
            except Exception as e:
                print(f"❌ Cleanup error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_expired_messages(self) -> None:
        """Clean up expired messages."""
        current_time = time.time()
        expired_messages = []
        
        for message_id, message in self.pending_messages.items():
            if current_time - message.timestamp > message.ttl:
                expired_messages.append(message_id)
        
        for message_id in expired_messages:
            await self._cleanup_message(message_id)
    
    async def _cleanup_message(self, message_id: bytes) -> None:
        """Clean up a message."""
        try:
            if message_id in self.pending_messages:
                message = self.pending_messages[message_id]
                
                # Emit cleanup event
                await self._emit_event(PubSubEvent.MESSAGE_CLEANED, message.group_id, None, message_id, {
                    "action": "message_cleaned",
                    "reason": "expired" if time.time() - message.timestamp > message.ttl else "delivered",
                    "delivery_attempts": message.delivery_attempts
                })
                
                # Remove from pending messages
                del self.pending_messages[message_id]
                
                # Add to delivered messages
                self.delivered_messages.add(message_id)
                
                self.stats["messages_cleaned"] += 1
                
        except Exception as e:
            print(f"❌ Failed to cleanup message {message_id.hex()}: {e}")
    
    async def _cleanup_old_events(self) -> None:
        """Clean up old events."""
        # Events are automatically cleaned up due to deque maxlen
        pass
    
    # Key Rotation
    
    async def _key_rotation_loop(self) -> None:
        """Main key rotation loop."""
        while True:
            try:
                # Check for keys that need rotation
                current_time = time.time()
                
                for group_id, group_key in list(self.active_group_keys.items()):
                    if current_time >= group_key.expires_at:
                        await self._rotate_group_key(group_id)
                
                # Wait before next check
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                print(f"❌ Key rotation error: {e}")
                await asyncio.sleep(60)
    
    # Event Handling
    
    async def _emit_event(self, event_type: PubSubEvent, group_id: bytes, user_id: Optional[bytes], 
                         message_id: Optional[bytes], data: Dict[str, Any]) -> None:
        """Emit a pubsub event."""
        try:
            event = PubSubEvent(
                event_type=event_type,
                group_id=group_id,
                user_id=user_id,
                message_id=message_id,
                timestamp=int(time.time()),
                data=data
            )
            
            # Add to event history
            self.event_history.append(event)
            
            # Call event handlers
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        await handler(event)
                    except Exception as e:
                        print(f"❌ Event handler error: {e}")
            
            self.stats["events_processed"] += 1
            
        except Exception as e:
            print(f"❌ Failed to emit event: {e}")
    
    def add_event_handler(self, event_type: PubSubEvent, handler: Callable) -> None:
        """Add an event handler."""
        self.event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: PubSubEvent, handler: Callable) -> None:
        """Remove an event handler."""
        if handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
    
    # Public API
    
    def get_pubsub_status(self) -> Dict:
        """Get pubsub server status."""
        return {
            "active": True,
            "groups_count": len(self.groups),
            "pending_messages": len(self.pending_messages),
            "delivered_messages": len(self.delivered_messages),
            "active_group_keys": len(self.active_group_keys),
            "total_subscriptions": sum(len(subscriptions) for subscriptions in self.group_subscriptions.values())
        }
    
    def get_group_info(self, group_id: bytes) -> Optional[Dict]:
        """Get group information."""
        if group_id not in self.groups:
            return None
        
        group_info = self.groups[group_id].copy()
        group_info["members"] = [user_id.hex() for user_id in self.group_subscriptions[group_id]]
        group_info["active_key_id"] = self.active_group_keys[group_id].key_id.hex() if group_id in self.active_group_keys else None
        
        return group_info
    
    def get_user_groups(self, user_id: bytes) -> List[Dict]:
        """Get groups for a user."""
        groups = []
        for group_id in self.user_subscriptions[user_id]:
            group_info = self.get_group_info(group_id)
            if group_info:
                groups.append(group_info)
        return groups
    
    def get_message_status(self, message_id: bytes) -> Optional[Dict]:
        """Get message delivery status."""
        if message_id in self.pending_messages:
            message = self.pending_messages[message_id]
            return {
                "message_id": message_id.hex(),
                "group_id": message.group_id.hex(),
                "sender_id": message.sender_id.hex(),
                "timestamp": message.timestamp,
                "delivery_attempts": message.delivery_attempts,
                "is_delivered": message.is_delivered,
                "remaining_recipients": len(message.recipients),
                "ttl": message.ttl
            }
        elif message_id in self.delivered_messages:
            return {
                "message_id": message_id.hex(),
                "status": "delivered",
                "delivered_at": int(time.time())
            }
        else:
            return None
    
    def get_pubsub_stats(self) -> Dict:
        """Get pubsub statistics."""
        return {
            **self.stats,
            "groups_count": len(self.groups),
            "pending_messages_count": len(self.pending_messages),
            "delivered_messages_count": len(self.delivered_messages),
            "active_group_keys_count": len(self.active_group_keys),
            "total_subscriptions": sum(len(subscriptions) for subscriptions in self.group_subscriptions.values()),
            "event_history_size": len(self.event_history)
        }
    
    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        """Get recent events."""
        events = list(self.event_history)[-limit:]
        return [event.to_dict() for event in events]
    
    async def stop_pubsub_service(self) -> None:
        """Stop the pubsub service."""
        if self.delivery_task:
            self.delivery_task.cancel()
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        if self.key_rotation_task:
            self.key_rotation_task.cancel()
        
        print("🛑 PubSub service stopped")
