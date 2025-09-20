"""
PubSub Server for Decentralized Group Message Distribution.
Implements a publish-subscribe server for distributing individually encrypted group messages
where groups are managed only by their owners and messages are encrypted separately for each member.
The server does not store group keys or group metadata - it only facilitates message delivery.
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
from .decentralized_groups import DecentralizedGroupManager, DecentralizedGroup, GroupMessage


class PubSubEvent(Enum):
    """Types of pubsub events."""
    
    MESSAGE_PUBLISHED = "message_published"
    MESSAGE_DELIVERED = "message_delivered"
    MESSAGE_FAILED = "message_failed"
    GROUP_JOINED = "group_joined"
    GROUP_LEFT = "group_left"
    MESSAGE_CLEANED = "message_cleaned"


@dataclass
class IndividuallyEncryptedMessage:
    """Message encrypted individually for each recipient."""
    
    message_id: bytes                    # Unique message identifier
    group_id: bytes                      # Group identifier
    sender_id: bytes                     # Sender identifier
    message_type: MessageType            # Type of message
    timestamp: int                       # Message timestamp
    ttl: int                             # Time to live in seconds
    # Each recipient gets their own encrypted content
    encrypted_contents_per_member: Dict[bytes, bytes]  # member_hash -> encrypted_content
    delivery_attempts: int = 0           # Number of delivery attempts
    max_delivery_attempts: int = 3       # Maximum delivery attempts
    is_delivered: bool = False           # Whether message was delivered
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "message_id": self.message_id.hex(),
            "group_id": self.group_id.hex(),
            "sender_id": self.sender_id.hex(),
            "message_type": self.message_type.value,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "encrypted_contents_per_member": {
                member_hash.hex(): content.hex() 
                for member_hash, content in self.encrypted_contents_per_member.items()
            },
            "delivery_attempts": self.delivery_attempts,
            "max_delivery_attempts": self.max_delivery_attempts,
            "is_delivered": self.is_delivered
        }


@dataclass
class PubSubEventData:
    """PubSub event data for monitoring."""
    
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
    """PubSub server for decentralized group message distribution.
    
    This server does not store group keys or group metadata. It only facilitates
    the delivery of individually encrypted messages. The group owner encrypts
    each message separately for each group member using their public keys.
    """
    
    def __init__(self, encryption: EndToEndEncryption):
        self.encryption = encryption
        
        # Message delivery tracking
        self.message_delivery_status: Dict[bytes, Dict[bytes, bool]] = defaultdict(dict)  # message_id -> user_hash -> delivered
        
        # Message management - store individually encrypted messages
        self.pending_messages: Dict[bytes, IndividuallyEncryptedMessage] = {}  # message_id -> message
        self.message_queue: deque = deque()  # Message delivery queue
        self.delivered_messages: Set[bytes] = set()  # Delivered message IDs
        
        # Event handling
        self.event_handlers: Dict[PubSubEvent, List[Callable]] = defaultdict(list)
        self.event_history: deque = deque(maxlen=1000)  # Event history
        
        # Configuration
        self.max_message_ttl = 3600  # 1 hour
        self.max_delivery_attempts = 3
        self.cleanup_interval = 300  # 5 minutes
        
        # Statistics
        self.stats = {
            "messages_published": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "messages_cleaned": 0,
            "events_processed": 0
        }
        
        # Background tasks
        self.delivery_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
    
    async def start_pubsub_service(self) -> None:
        """Start the pubsub service."""
        print("📢 Starting PubSub service...")
        
        # Start background tasks
        self.delivery_task = asyncio.create_task(self._message_delivery_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        print("✅ PubSub service started")
    
    # Message Publishing and Distribution
    
    async def publish_individually_encrypted_message(self, group_id: bytes, sender_hash: bytes,
                                                   message_type: MessageType, content: bytes,
                                                   encrypted_contents_per_member: Dict[bytes, bytes]) -> Optional[bytes]:
        """Publish a message that has been individually encrypted for each group member.
        
        Args:
            group_id: The group identifier
            sender_hash: The sender's hash identifier
            message_type: Type of message (TEXT_MESSAGE, etc.)
            content: Original message content (for logging/debugging)
            encrypted_contents_per_member: Dict mapping member_hash -> encrypted_content
            
        Returns:
            message_id if successful, None otherwise
        """
        try:
            # Generate unique message ID
            message_id = hashlib.sha256(
                group_id + sender_hash + str(int(time.time())).encode() + content
            ).digest()[:16]
            
            # Create individually encrypted message
            encrypted_message = IndividuallyEncryptedMessage(
                message_id=message_id,
                group_id=group_id,
                sender_id=sender_hash,
                message_type=message_type,
                timestamp=int(time.time()),
                ttl=self.max_message_ttl,
                encrypted_contents_per_member=encrypted_contents_per_member,
                max_delivery_attempts=self.max_delivery_attempts
            )
            
            # Store message for delivery
            self.pending_messages[message_id] = encrypted_message
            self.message_queue.append(message_id)
            
            # Emit event
            await self._emit_event(PubSubEvent.MESSAGE_PUBLISHED, group_id, sender_hash, message_id, {
                "action": "message_published",
                "message_type": message_type.value,
                "recipient_count": len(encrypted_contents_per_member),
                "content_length": len(content)
            })
            
            self.stats["messages_published"] += 1
            print(f"📤 Published individually encrypted message {message_id.hex()} to {len(encrypted_contents_per_member)} recipients")
            
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
                    await self._deliver_individually_encrypted_message(message_id)
                
                # Wait before next iteration
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Message delivery error: {e}")
                await asyncio.sleep(1)
    
    async def _deliver_individually_encrypted_message(self, message_id: bytes) -> None:
        """Deliver an individually encrypted message to all recipients."""
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
            
            # Deliver to each recipient with their individually encrypted content
            delivered_count = 0
            failed_count = 0
            
            for recipient_id, encrypted_content in list(message.encrypted_contents_per_member.items()):
                try:
                    # Create delivery message with recipient's encrypted content
                    delivery_message = {
                        "type": "group_message",
                        "message_id": message_id.hex(),
                        "group_id": message.group_id.hex(),
                        "sender_id": message.sender_id.hex(),
                        "message_type": message.message_type.value,
                        "encrypted_content": encrypted_content.hex(),
                        "timestamp": message.timestamp
                    }
                    
                    # Send message to recipient (simplified)
                    success = await self._send_message_to_user(recipient_id, delivery_message)
                    
                    if success:
                        delivered_count += 1
                        # Remove from pending delivery
                        del message.encrypted_contents_per_member[recipient_id]
                        
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
            if not message.encrypted_contents_per_member:
                message.is_delivered = True
                await self._cleanup_message(message_id)
                self.stats["messages_delivered"] += 1
                print(f"✅ Message {message_id.hex()} delivered to all {delivered_count} recipients")
            else:
                # Re-queue message for retry
                self.message_queue.append(message_id)
                
                if failed_count > 0:
                    # Emit failure event
                    await self._emit_event(PubSubEvent.MESSAGE_FAILED, message.group_id, None, message_id, {
                        "action": "delivery_failed",
                        "failed_count": failed_count,
                        "remaining_recipients": len(message.encrypted_contents_per_member)
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
    
    
    # Event Handling
    
    async def _emit_event(self, event_type: PubSubEvent, group_id: bytes, user_id: Optional[bytes], 
                         message_id: Optional[bytes], data: Dict[str, Any]) -> None:
        """Emit a pubsub event."""
        try:
            event = PubSubEventData(
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
            "pending_messages": len(self.pending_messages),
            "delivered_messages": len(self.delivered_messages),
            "message_queue_size": len(self.message_queue),
            "event_history_size": len(self.event_history),
            "stats": self.stats
        }
    
    def get_message_status(self, message_id: bytes) -> Optional[Dict]:
        """Get message delivery status."""
        if message_id in self.pending_messages:
            message = self.pending_messages[message_id]
            return {
                "message_id": message_id.hex(),
                "group_id": message.group_id.hex(),
                "sender_id": message.sender_id.hex(),
                "message_type": message.message_type.value,
                "timestamp": message.timestamp,
                "delivery_attempts": message.delivery_attempts,
                "is_delivered": message.is_delivered,
                "remaining_recipients": len(message.encrypted_contents_per_member),
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
            "stats": self.stats,
            "pending_messages": len(self.pending_messages),
            "delivered_messages": len(self.delivered_messages),
            "message_queue_size": len(self.message_queue),
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
        
        print("🛑 PubSub service stopped")
