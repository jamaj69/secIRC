"""
User Status and Message Delivery Protocol

This module implements the protocol for managing user online status
and delivering messages to online users across the relay network.
"""

import asyncio
import hashlib
import time
import json
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque

from .message_types import MessageType, Message, HashIdentity
from .authentication import AuthenticationSession


class UserStatus(Enum):
    """User online status states."""
    OFFLINE = "offline"
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    INVISIBLE = "invisible"


class MessageDeliveryStatus(Enum):
    """Message delivery status."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class UserPresence:
    """Represents a user's presence information."""
    
    user_id: bytes
    status: UserStatus
    last_seen: int
    server_id: bytes
    session_id: Optional[bytes] = None
    public_key: Optional[bytes] = None
    nickname: Optional[str] = None
    status_message: Optional[str] = None
    
    def __post_init__(self):
        if self.last_seen == 0:
            self.last_seen = int(time.time())
    
    def update_presence(self, status: UserStatus = None, status_message: str = None) -> None:
        """Update user presence."""
        if status is not None:
            self.status = status
        if status_message is not None:
            self.status_message = status_message
        self.last_seen = int(time.time())
    
    def is_online(self) -> bool:
        """Check if user is online."""
        return self.status in [UserStatus.ONLINE, UserStatus.AWAY, UserStatus.BUSY]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "user_id": self.user_id.hex(),
            "status": self.status.value,
            "last_seen": self.last_seen,
            "server_id": self.server_id.hex(),
            "session_id": self.session_id.hex() if self.session_id else None,
            "public_key": self.public_key.hex() if self.public_key else None,
            "nickname": self.nickname,
            "status_message": self.status_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPresence":
        """Create from dictionary."""
        return cls(
            user_id=bytes.fromhex(data["user_id"]),
            status=UserStatus(data["status"]),
            last_seen=data["last_seen"],
            server_id=bytes.fromhex(data["server_id"]),
            session_id=bytes.fromhex(data["session_id"]) if data.get("session_id") else None,
            public_key=bytes.fromhex(data["public_key"]) if data.get("public_key") else None,
            nickname=data.get("nickname"),
            status_message=data.get("status_message")
        )


@dataclass
class PendingMessage:
    """Represents a message waiting to be delivered."""
    
    message_id: bytes
    sender_id: bytes
    recipient_id: bytes
    message_type: MessageType
    content: bytes
    timestamp: int
    ttl: int
    delivery_attempts: int = 0
    max_attempts: int = 3
    status: MessageDeliveryStatus = MessageDeliveryStatus.PENDING
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = int(time.time())
    
    def is_expired(self) -> bool:
        """Check if message has expired."""
        return time.time() - self.timestamp > self.ttl
    
    def can_retry(self) -> bool:
        """Check if message can be retried."""
        return (self.delivery_attempts < self.max_attempts and 
                not self.is_expired() and 
                self.status == MessageDeliveryStatus.PENDING)
    
    def mark_delivered(self) -> None:
        """Mark message as delivered."""
        self.status = MessageDeliveryStatus.DELIVERED
    
    def mark_failed(self) -> None:
        """Mark message as failed."""
        self.status = MessageDeliveryStatus.FAILED
    
    def mark_expired(self) -> None:
        """Mark message as expired."""
        self.status = MessageDeliveryStatus.EXPIRED
    
    def increment_attempts(self) -> None:
        """Increment delivery attempts."""
        self.delivery_attempts += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "message_id": self.message_id.hex(),
            "sender_id": self.sender_id.hex(),
            "recipient_id": self.recipient_id.hex(),
            "message_type": self.message_type.value,
            "content": self.content.hex(),
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "delivery_attempts": self.delivery_attempts,
            "max_attempts": self.max_attempts,
            "status": self.status.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PendingMessage":
        """Create from dictionary."""
        return cls(
            message_id=bytes.fromhex(data["message_id"]),
            sender_id=bytes.fromhex(data["sender_id"]),
            recipient_id=bytes.fromhex(data["recipient_id"]),
            message_type=MessageType(data["message_type"]),
            content=bytes.fromhex(data["content"]),
            timestamp=data["timestamp"],
            ttl=data["ttl"],
            delivery_attempts=data.get("delivery_attempts", 0),
            max_attempts=data.get("max_attempts", 3),
            status=MessageDeliveryStatus(data.get("status", "pending"))
        )


class UserStatusManager:
    """Manages user online status across the relay network."""
    
    def __init__(self, server_id: bytes):
        self.server_id = server_id
        self.user_presences: Dict[bytes, UserPresence] = {}  # user_id -> UserPresence
        self.user_sessions: Dict[bytes, bytes] = {}  # user_id -> session_id
        self.server_users: Dict[bytes, Set[bytes]] = defaultdict(set)  # server_id -> set of user_ids
        self.pending_messages: Dict[bytes, List[PendingMessage]] = defaultdict(list)  # user_id -> list of messages
        
        # Configuration
        self.presence_timeout = 300  # 5 minutes
        self.message_ttl = 3600      # 1 hour
        self.max_pending_messages = 100
        
        # Statistics
        self.stats = {
            "users_online": 0,
            "users_offline": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "messages_expired": 0,
            "presence_updates": 0
        }
    
    def user_login(self, user_id: bytes, session_id: bytes, 
                   public_key: bytes, nickname: str = None) -> UserPresence:
        """Handle user login and set online status."""
        # Create or update user presence
        presence = UserPresence(
            user_id=user_id,
            status=UserStatus.ONLINE,
            last_seen=int(time.time()),
            server_id=self.server_id,
            session_id=session_id,
            public_key=public_key,
            nickname=nickname
        )
        
        self.user_presences[user_id] = presence
        self.user_sessions[user_id] = session_id
        self.server_users[self.server_id].add(user_id)
        
        self.stats["users_online"] += 1
        self.stats["presence_updates"] += 1
        
        return presence
    
    def user_logout(self, user_id: bytes) -> bool:
        """Handle user logout and set offline status."""
        if user_id not in self.user_presences:
            return False
        
        presence = self.user_presences[user_id]
        presence.status = UserStatus.OFFLINE
        presence.update_presence()
        
        # Remove from active sessions
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        # Remove from server users
        self.server_users[self.server_id].discard(user_id)
        
        self.stats["users_online"] -= 1
        self.stats["users_offline"] += 1
        self.stats["presence_updates"] += 1
        
        return True
    
    def update_user_status(self, user_id: bytes, status: UserStatus, 
                          status_message: str = None) -> bool:
        """Update user status."""
        if user_id not in self.user_presences:
            return False
        
        presence = self.user_presences[user_id]
        presence.update_presence(status, status_message)
        
        self.stats["presence_updates"] += 1
        return True
    
    def get_user_presence(self, user_id: bytes) -> Optional[UserPresence]:
        """Get user presence information."""
        return self.user_presences.get(user_id)
    
    def is_user_online(self, user_id: bytes) -> bool:
        """Check if user is online."""
        presence = self.user_presences.get(user_id)
        return presence is not None and presence.is_online()
    
    def get_online_users(self) -> List[UserPresence]:
        """Get list of online users."""
        return [presence for presence in self.user_presences.values() 
                if presence.is_online()]
    
    def get_users_by_server(self, server_id: bytes) -> List[UserPresence]:
        """Get users connected to a specific server."""
        user_ids = self.server_users.get(server_id, set())
        return [self.user_presences[user_id] for user_id in user_ids 
                if user_id in self.user_presences]
    
    def broadcast_user_online(self, user_id: bytes, presence: UserPresence) -> Dict[str, Any]:
        """Create message to broadcast user online status."""
        return {
            "type": "user_online",
            "user_id": user_id.hex(),
            "presence": presence.to_dict(),
            "timestamp": int(time.time())
        }
    
    def broadcast_user_offline(self, user_id: bytes) -> Dict[str, Any]:
        """Create message to broadcast user offline status."""
        return {
            "type": "user_offline",
            "user_id": user_id.hex(),
            "timestamp": int(time.time())
        }
    
    def broadcast_user_status_update(self, user_id: bytes, presence: UserPresence) -> Dict[str, Any]:
        """Create message to broadcast user status update."""
        return {
            "type": "user_status_update",
            "user_id": user_id.hex(),
            "presence": presence.to_dict(),
            "timestamp": int(time.time())
        }


class MessageDeliveryManager:
    """Manages message delivery to online users."""
    
    def __init__(self, user_status_manager: UserStatusManager):
        self.user_status_manager = user_status_manager
        self.delivery_queue: deque = deque()
        self.delivery_stats = {
            "messages_queued": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "messages_expired": 0,
            "delivery_attempts": 0
        }
    
    def queue_message(self, sender_id: bytes, recipient_id: bytes,
                     message_type: MessageType, content: bytes,
                     ttl: int = None) -> bytes:
        """Queue a message for delivery."""
        if ttl is None:
            ttl = self.user_status_manager.message_ttl
        
        message_id = hashlib.sha256(
            sender_id + recipient_id + str(int(time.time())).encode() + content
        ).digest()[:16]
        
        message = PendingMessage(
            message_id=message_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=content,
            timestamp=int(time.time()),
            ttl=ttl
        )
        
        # Add to pending messages for the recipient
        self.user_status_manager.pending_messages[recipient_id].append(message)
        
        # Limit pending messages per user
        if len(self.user_status_manager.pending_messages[recipient_id]) > self.user_status_manager.max_pending_messages:
            # Remove oldest messages
            self.user_status_manager.pending_messages[recipient_id] = \
                self.user_status_manager.pending_messages[recipient_id][-self.user_status_manager.max_pending_messages:]
        
        # Add to delivery queue if user is online
        if self.user_status_manager.is_user_online(recipient_id):
            self.delivery_queue.append(message_id)
        
        self.delivery_stats["messages_queued"] += 1
        return message_id
    
    def deliver_pending_messages(self, user_id: bytes) -> List[PendingMessage]:
        """Deliver pending messages to a user who just came online."""
        if user_id not in self.user_status_manager.pending_messages:
            return []
        
        pending_messages = self.user_status_manager.pending_messages[user_id]
        delivered_messages = []
        
        for message in pending_messages[:]:  # Copy list to avoid modification during iteration
            if message.can_retry():
                # Add to delivery queue
                self.delivery_queue.append(message.message_id)
                delivered_messages.append(message)
            elif message.is_expired():
                message.mark_expired()
                self.delivery_stats["messages_expired"] += 1
        
        return delivered_messages
    
    def process_delivery_queue(self) -> List[Tuple[bytes, PendingMessage]]:
        """Process messages in the delivery queue."""
        delivered = []
        
        while self.delivery_queue:
            message_id = self.delivery_queue.popleft()
            
            # Find the message
            message = None
            for user_id, messages in self.user_status_manager.pending_messages.items():
                for msg in messages:
                    if msg.message_id == message_id:
                        message = msg
                        break
                if message:
                    break
            
            if not message:
                continue
            
            # Check if message can be delivered
            if not message.can_retry():
                if message.is_expired():
                    message.mark_expired()
                    self.delivery_stats["messages_expired"] += 1
                else:
                    message.mark_failed()
                    self.delivery_stats["messages_failed"] += 1
                continue
            
            # Check if recipient is online
            if not self.user_status_manager.is_user_online(message.recipient_id):
                # Re-queue for later delivery
                self.delivery_queue.append(message_id)
                continue
            
            # Attempt delivery
            message.increment_attempts()
            self.delivery_stats["delivery_attempts"] += 1
            
            # Simulate delivery (in real implementation, this would send to the user)
            if self._attempt_delivery(message):
                message.mark_delivered()
                delivered.append((message.recipient_id, message))
                self.delivery_stats["messages_delivered"] += 1
                
                # Remove from pending messages
                self.user_status_manager.pending_messages[message.recipient_id].remove(message)
            else:
                # Re-queue for retry
                self.delivery_queue.append(message_id)
        
        return delivered
    
    def _attempt_delivery(self, message: PendingMessage) -> bool:
        """Attempt to deliver a message to a user."""
        # In real implementation, this would:
        # 1. Get user's session
        # 2. Send message through the session
        # 3. Wait for acknowledgment
        # 4. Return success/failure
        
        # For now, simulate delivery with 90% success rate
        import random
        return random.random() < 0.9
    
    def get_pending_messages(self, user_id: bytes) -> List[PendingMessage]:
        """Get pending messages for a user."""
        return self.user_status_manager.pending_messages.get(user_id, [])
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get message delivery statistics."""
        return {
            "stats": self.delivery_stats,
            "queue_size": len(self.delivery_queue),
            "pending_messages": sum(len(messages) for messages in self.user_status_manager.pending_messages.values()),
            "online_users": len(self.user_status_manager.get_online_users())
        }
    
    def cleanup_expired_messages(self) -> int:
        """Clean up expired messages."""
        cleaned = 0
        
        for user_id, messages in list(self.user_status_manager.pending_messages.items()):
            expired_messages = []
            for message in messages:
                if message.is_expired():
                    expired_messages.append(message)
                    self.delivery_stats["messages_expired"] += 1
                    cleaned += 1
            
            # Remove expired messages
            for message in expired_messages:
                messages.remove(message)
            
            # Remove empty lists
            if not messages:
                del self.user_status_manager.pending_messages[user_id]
        
        return cleaned
