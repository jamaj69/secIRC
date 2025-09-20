# secIRC PubSub Group Messaging System

## Overview

This document describes the PubSub (Publish-Subscribe) server system implemented in secIRC for secure group messaging. The system addresses the critical challenge of **group encryption key management** while maintaining end-to-end encryption and ensuring all group members can decrypt messages.

## 🔑 Core Challenge Solved

### **The Problem**
- **Group messages** need to be encrypted for all group members
- **Individual encryption** (user-to-user) is simple: encrypt with recipient's public key
- **Group encryption** is complex: all group members must be able to decrypt
- **Server storage** must maintain encrypted messages without decryption capability
- **Key distribution** must be secure and efficient

### **The Solution**
A comprehensive **PubSub server with group key management** that:
- **Generates shared group keys** for each group
- **Encrypts group keys** with each member's public key
- **Distributes encrypted group keys** to all members
- **Encrypts messages** with the shared group key
- **Automatically cleans up** messages after delivery
- **Rotates keys** when members join/leave

## 🏗️ System Architecture

### **PubSub Server Components**

#### **1. Group Management**
- **Group Creation**: Create groups with initial key generation
- **Member Management**: Add/remove members with key rotation
- **Subscription Management**: Track user subscriptions to groups

#### **2. Group Key Management**
- **Key Generation**: Generate shared secret keys for groups
- **Key Distribution**: Encrypt and distribute keys to all members
- **Key Rotation**: Rotate keys when membership changes
- **Key Storage**: Store encrypted keys for each user

#### **3. Message Distribution**
- **Message Publishing**: Publish encrypted messages to groups
- **Message Delivery**: Deliver messages to all group members
- **Message Cleanup**: Automatically clean up delivered messages
- **Delivery Tracking**: Track delivery status and retry failed deliveries

#### **4. Event System**
- **Event Emission**: Emit events for monitoring and logging
- **Event Handlers**: Custom event handlers for different events
- **Event History**: Maintain event history for debugging

## 🔐 Group Key Management

### **Key Generation Process**

#### **1. Group Key Creation**
```python
async def generate_group_key(self, group_id: bytes, group_members: List[bytes]) -> GroupKeyMaterial:
    # Generate random key material
    key = os.urandom(32)  # 256-bit key
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    salt = os.urandom(16)  # 128-bit salt
    
    # Create key ID
    key_id = hashlib.sha256(
        group_id + key + nonce + salt + str(time.time()).encode()
    ).digest()[:16]
    
    # Create key material
    key_material = GroupKeyMaterial(
        group_id=group_id,
        key_id=key_id,
        algorithm=GroupKeyAlgorithm.AES_256_GCM,
        key=key,
        nonce=nonce,
        salt=salt,
        created_at=int(time.time()),
        expires_at=int(time.time()) + self.key_rotation_interval,
        version=len(self.group_keys[group_id]) + 1
    )
```

#### **2. Key Distribution**
```python
async def _distribute_group_key(self, key_material: GroupKeyMaterial, group_members: List[bytes]) -> None:
    encrypted_keys = {}
    
    for user_id in group_members:
        # Get user's public key
        user_public_key = await self._get_user_public_key(user_id)
        
        # Encrypt group key with user's public key
        encrypted_group_key = self.encryption.encrypt_message(key_material.key, user_public_key)
        encrypted_keys[user_id] = encrypted_group_key
        
        # Store encrypted key for user
        self.user_group_keys[user_id][key_material.group_id] = encrypted_group_key
```

### **Key Rotation Process**

#### **1. Automatic Key Rotation**
```python
async def _key_rotation_loop(self) -> None:
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
            print(f"Key rotation error: {e}")
            await asyncio.sleep(60)
```

#### **2. Membership-Based Key Rotation**
```python
async def rotate_group_key(self, group_id: bytes, group_members: List[bytes]) -> Optional[GroupKeyMaterial]:
    # Generate new group key
    new_key_material = await self.generate_group_key(group_id, group_members)
    
    # Mark old keys as inactive
    for key_id, key_material in self.group_keys[group_id].items():
        if key_id != new_key_material.key_id:
            key_material.expires_at = int(time.time())
    
    return new_key_material
```

## 📨 Message Encryption and Distribution

### **Message Encryption Process**

#### **1. Group Message Encryption**
```python
async def encrypt_group_message(self, group_id: bytes, sender_id: bytes, content: bytes) -> Optional[EncryptedGroupMessage]:
    # Get active group key
    key_material = self.active_group_keys[group_id]
    
    # Generate message ID
    message_id = hashlib.sha256(
        group_id + sender_id + content + str(time.time()).encode()
    ).digest()[:16]
    
    # Generate unique nonce for this message
    message_nonce = os.urandom(12)
    
    # Encrypt message content
    encrypted_content = await self._encrypt_content(content, key_material.key, message_nonce, key_material.algorithm)
    
    # Create message signature
    signature = await self._sign_message(message_id, group_id, sender_id, encrypted_content, key_material.key)
    
    # Create encrypted message
    encrypted_message = EncryptedGroupMessage(
        message_id=message_id,
        group_id=group_id,
        sender_id=sender_id,
        encrypted_content=encrypted_content,
        key_id=key_material.key_id,
        nonce=message_nonce,
        timestamp=int(time.time()),
        signature=signature,
        algorithm=key_material.algorithm
    )
    
    return encrypted_message
```

#### **2. Multiple Encryption Algorithms**
```python
async def _encrypt_content(self, content: bytes, key: bytes, nonce: bytes, algorithm: GroupKeyAlgorithm) -> bytes:
    if algorithm == GroupKeyAlgorithm.AES_256_GCM:
        return await self._encrypt_aes_gcm(content, key, nonce)
    elif algorithm == GroupKeyAlgorithm.CHACHA20_POLY1305:
        return await self._encrypt_chacha20_poly1305(content, key, nonce)
    elif algorithm == GroupKeyAlgorithm.XSALSA20_POLY1305:
        return await self._encrypt_xsalsa20_poly1305(content, key, nonce)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
```

### **Message Distribution Process**

#### **1. Message Publishing**
```python
async def publish_message(self, group_id: bytes, sender_id: bytes, content: bytes) -> Optional[bytes]:
    # Get active group key
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
    
    # Store message and queue for delivery
    self.pending_messages[message_id] = group_message
    self.message_queue.append(message_id)
    
    return message_id
```

#### **2. Message Delivery**
```python
async def _deliver_message(self, message_id: bytes) -> None:
    message = self.pending_messages[message_id]
    group_key = self.active_group_keys[message.group_id]
    
    # Deliver to each recipient
    for recipient_id in list(message.recipients):
        try:
            # Get recipient's encrypted group key
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
            
            # Send message to recipient
            success = await self._send_message_to_user(recipient_id, delivery_message)
            
            if success:
                message.recipients.discard(recipient_id)
                
                # Emit delivery event
                await self._emit_event(PubSubEvent.MESSAGE_DELIVERED, message.group_id, recipient_id, message_id, {
                    "action": "message_delivered",
                    "recipient_id": recipient_id.hex()
                })
            
        except Exception as e:
            print(f"Failed to deliver message to {recipient_id.hex()}: {e}")
    
    # Update delivery attempts
    message.delivery_attempts += 1
    
    # Check if all recipients have been delivered
    if not message.recipients:
        message.is_delivered = True
        await self._cleanup_message(message_id)
```

## 🔓 Message Decryption

### **Client-Side Decryption Process**

#### **1. Receive Encrypted Message**
```python
# Client receives delivery message
delivery_message = {
    "type": "group_message",
    "message_id": "abc123...",
    "group_id": "group456...",
    "sender_id": "user789...",
    "encrypted_content": "encrypted_data...",
    "key_id": "key123...",
    "encrypted_group_key": "encrypted_key...",
    "timestamp": 1234567890
}
```

#### **2. Decrypt Group Key**
```python
# Decrypt group key with user's private key
encrypted_group_key = bytes.fromhex(delivery_message["encrypted_group_key"])
user_private_key = get_user_private_key()  # From user's keyring
group_key = encryption.decrypt_message(encrypted_group_key, user_private_key)
```

#### **3. Decrypt Message Content**
```python
# Decrypt message content with group key
encrypted_content = bytes.fromhex(delivery_message["encrypted_content"])
message_content = encryption.decrypt_message(encrypted_content, group_key)

# Verify message signature
message_id = bytes.fromhex(delivery_message["message_id"])
group_id = bytes.fromhex(delivery_message["group_id"])
sender_id = bytes.fromhex(delivery_message["sender_id"])

signature_valid = verify_message_signature(
    message_id, group_id, sender_id, encrypted_content, group_key
)
```

## 🧹 Message Cleanup

### **Automatic Cleanup Process**

#### **1. Cleanup Loop**
```python
async def _cleanup_loop(self) -> None:
    while True:
        try:
            # Clean up expired messages
            await self._cleanup_expired_messages()
            
            # Clean up old events
            await self._cleanup_old_events()
            
            # Wait before next cleanup
            await asyncio.sleep(self.cleanup_interval)
            
        except Exception as e:
            print(f"Cleanup error: {e}")
            await asyncio.sleep(60)
```

#### **2. Message Expiration**
```python
async def _cleanup_expired_messages(self) -> None:
    current_time = time.time()
    expired_messages = []
    
    for message_id, message in self.pending_messages.items():
        if current_time - message.timestamp > message.ttl:
            expired_messages.append(message_id)
    
    for message_id in expired_messages:
        await self._cleanup_message(message_id)
```

#### **3. Message Cleanup**
```python
async def _cleanup_message(self, message_id: bytes) -> None:
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
```

## 📊 Event System

### **Event Types**

#### **1. Message Events**
- **MESSAGE_PUBLISHED**: Message published to group
- **MESSAGE_DELIVERED**: Message delivered to recipient
- **MESSAGE_FAILED**: Message delivery failed
- **MESSAGE_CLEANED**: Message cleaned up

#### **2. Group Events**
- **GROUP_JOINED**: User joined group
- **GROUP_LEFT**: User left group
- **KEY_ROTATED**: Group key rotated

### **Event Handling**
```python
async def _emit_event(self, event_type: PubSubEvent, group_id: bytes, user_id: Optional[bytes], 
                     message_id: Optional[bytes], data: Dict[str, Any]) -> None:
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
                print(f"Event handler error: {e}")
```

## 🔧 Configuration

### **PubSub Configuration**

```yaml
# config/pubsub.yaml
pubsub:
  max_message_ttl: 3600  # 1 hour
  max_delivery_attempts: 3
  cleanup_interval: 300  # 5 minutes
  key_rotation_interval: 86400  # 24 hours
  
  encryption:
    default_algorithm: "aes_256_gcm"
    key_size: 32  # 256 bits
    nonce_size: 12  # 96 bits for GCM
    salt_size: 16  # 128 bits
  
  delivery:
    retry_interval: 60  # 60 seconds
    max_retries: 3
    priority: "normal"
```

## 🚀 Usage Examples

### **Basic Group Operations**

#### **1. Create Group**
```python
# Create a new group
group_id = os.urandom(16)
creator_id = os.urandom(16)
group_info = {
    "name": "My Group",
    "description": "A secure group for messaging",
    "max_members": 100
}

success = await pubsub_server.create_group(group_id, creator_id, group_info)
if success:
    print(f"Group created: {group_id.hex()}")
```

#### **2. Join Group**
```python
# Join a group
user_id = os.urandom(16)
success = await pubsub_server.join_group(group_id, user_id)
if success:
    print(f"User {user_id.hex()} joined group {group_id.hex()}")
```

#### **3. Publish Message**
```python
# Publish a message to group
sender_id = os.urandom(16)
content = "Hello, group members!"
message_id = await pubsub_server.publish_message(group_id, sender_id, content.encode())
if message_id:
    print(f"Message published: {message_id.hex()}")
```

### **Message Monitoring**

#### **1. Check Message Status**
```python
# Check message delivery status
status = pubsub_server.get_message_status(message_id)
if status:
    print(f"Message status: {status}")
    print(f"Delivery attempts: {status['delivery_attempts']}")
    print(f"Remaining recipients: {status['remaining_recipients']}")
```

#### **2. Monitor Events**
```python
# Add event handler
async def message_delivered_handler(event):
    print(f"Message delivered to {event.user_id.hex()}")
    print(f"Group: {event.group_id.hex()}")
    print(f"Message: {event.message_id.hex()}")

pubsub_server.add_event_handler(PubSubEvent.MESSAGE_DELIVERED, message_delivered_handler)
```

### **Group Management**

#### **1. Get Group Info**
```python
# Get group information
group_info = pubsub_server.get_group_info(group_id)
if group_info:
    print(f"Group: {group_info['name']}")
    print(f"Members: {group_info['member_count']}")
    print(f"Active key: {group_info['active_key_id']}")
```

#### **2. Get User Groups**
```python
# Get groups for a user
user_groups = pubsub_server.get_user_groups(user_id)
for group in user_groups:
    print(f"Group: {group['name']} ({group['group_id']})")
    print(f"Members: {group['member_count']}")
```

## 📈 Statistics and Monitoring

### **PubSub Statistics**
```python
# Get pubsub statistics
stats = pubsub_server.get_pubsub_stats()
print(f"Messages published: {stats['messages_published']}")
print(f"Messages delivered: {stats['messages_delivered']}")
print(f"Messages failed: {stats['messages_failed']}")
print(f"Groups created: {stats['groups_created']}")
print(f"Users subscribed: {stats['users_subscribed']}")
print(f"Keys rotated: {stats['keys_rotated']}")
```

### **Encryption Statistics**
```python
# Get encryption statistics
encryption_stats = group_encryption.get_encryption_stats()
print(f"Keys generated: {encryption_stats['keys_generated']}")
print(f"Keys distributed: {encryption_stats['keys_distributed']}")
print(f"Messages encrypted: {encryption_stats['messages_encrypted']}")
print(f"Messages decrypted: {encryption_stats['messages_decrypted']}")
print(f"Key rotations: {encryption_stats['key_rotations']}")
```

## 🔮 Future Enhancements

### **Planned Improvements**

#### **1. Advanced Encryption**
- **Perfect Forward Secrecy**: Rotate keys for each message
- **Post-Quantum Cryptography**: Quantum-resistant algorithms
- **Homomorphic Encryption**: Compute on encrypted data
- **Zero-Knowledge Proofs**: Verify without revealing data

#### **2. Enhanced Distribution**
- **Message Prioritization**: Priority-based delivery
- **Load Balancing**: Distribute load across servers
- **Caching**: Intelligent message caching
- **Compression**: Message compression for efficiency

#### **3. Advanced Features**
- **Message Reactions**: React to messages
- **Message Threading**: Threaded conversations
- **File Sharing**: Encrypted file sharing
- **Voice Messages**: Encrypted voice messages

---

This PubSub group messaging system provides a comprehensive solution for secure group communication while maintaining end-to-end encryption and ensuring all group members can decrypt messages. The system handles group key management, message distribution, and automatic cleanup while providing extensive monitoring and event handling capabilities.
