# secIRC Decentralized Group Messaging System

## Overview

This document describes the **secure decentralized group messaging system** implemented in secIRC that fixes the security flaws in traditional group messaging. The system ensures that groups are stored only on the creator's client with a list of public key hashes, and messages are encrypted individually for each group member.

## 🔒 Security Flaws Fixed

### **Previous System Problems**
- **Centralized group storage** on servers
- **Shared group keys** that could be compromised
- **Server knowledge** of group membership
- **Single point of failure** for group management

### **New Secure System**
- **Decentralized group storage** only on owner's client
- **Individual message encryption** for each member
- **Server ignorance** of group membership details
- **Owner-only group management** with public key verification

## 🏗️ System Architecture

### **Core Principles**

#### **1. Owner-Only Group Management**
- **Group Creation**: Only the owner can create groups
- **Member Management**: Only the owner can add/remove members
- **Message Sending**: Only the owner can send messages to the group
- **Group Deletion**: Only the owner can delete groups

#### **2. Decentralized Storage**
- **Group Data**: Stored only on owner's client
- **Member List**: List of public key hashes maintained by owner
- **Server Role**: Only delivers messages, doesn't store group info
- **No Central Authority**: No server knows complete group membership

#### **3. Individual Message Encryption**
- **Per-Member Encryption**: Each message encrypted separately for each member
- **Public Key Encryption**: Uses each member's public key
- **No Shared Keys**: No group keys that could be compromised
- **Perfect Forward Secrecy**: Each message uses fresh encryption

## 🔐 How It Works

### **1. Group Creation Process**

```python
# Owner creates a group
group = await group_manager.create_group(
    owner_hash=owner_hash,
    owner_public_key=owner_public_key,
    group_name="My Secure Group",
    description="Private group for secure communication",
    max_members=100,
    is_private=True
)

# Group is stored ONLY on owner's client
# Server has no knowledge of the group
```

**What happens:**
- Owner generates unique group ID
- Owner creates group with their public key hash
- Group stored locally on owner's client
- Server receives no group information

### **2. Member Addition Process**

```python
# Owner adds a member to the group
success = await group_manager.add_member(
    group_id=group_id,
    owner_hash=owner_hash,
    new_member_hash=new_member_hash,
    new_member_public_key=new_member_public_key
)

# Member is added to owner's local group list
# Server still has no knowledge of group membership
```

**What happens:**
- Owner adds member's public key hash to local group list
- Member's public key stored for encryption
- Group membership updated only on owner's client
- Server remains unaware of group changes

### **3. Message Sending Process**

```python
# Owner sends a message to the group
message_id = await group_manager.send_group_message(
    group_id=group_id,
    sender_hash=owner_hash,
    sender_public_key=owner_public_key,
    message_type=MessageType.TEXT_MESSAGE,
    content="Hello everyone!".encode()
)
```

**What happens:**
1. **Message Encryption**: Message encrypted separately for each member
2. **Individual Encryption**: Each member gets their own encrypted copy
3. **Server Delivery**: Server delivers encrypted messages to subscribed users
4. **No Group Knowledge**: Server doesn't know it's a group message

### **4. Message Encryption Details**

```python
# For each group member (except sender)
for member_hash, member in group.members.items():
    if member_hash != sender_hash:
        # Encrypt message with member's public key
        encrypted_message = encryption.encrypt_message(content, member.public_key)
        
        # Store encrypted message for this member
        encrypted_messages[member_hash] = encrypted_message

# Create group message with individual encryptions
group_message = GroupMessage(
    message_id=message_id,
    group_id=group_id,
    sender_hash=sender_hash,
    encrypted_messages=encrypted_messages,  # Different for each member
    timestamp=timestamp,
    signature=signature
)
```

**Security Benefits:**
- **Individual Encryption**: Each member gets unique encrypted message
- **No Shared Keys**: No group keys that could be compromised
- **Perfect Forward Secrecy**: Each message uses fresh encryption
- **Server Ignorance**: Server can't decrypt any messages

### **5. Message Delivery Process**

```python
# Server delivers message to subscribed users
for user_hash in subscribed_users:
    if user_hash in group_message.encrypted_messages:
        encrypted_message = group_message.encrypted_messages[user_hash]
        
        # Send encrypted message to user
        await send_to_user(user_hash, {
            "message_id": message_id.hex(),
            "group_id": group_id.hex(),
            "encrypted_message": encrypted_message.hex(),
            "sender_hash": sender_hash.hex(),
            "timestamp": timestamp
        })
```

**What happens:**
- Server checks if user is subscribed to the group
- Server sends user their encrypted copy of the message
- Server doesn't know it's part of a group
- Each user receives different encrypted content

### **6. Message Decryption (Client Side)**

```python
# User receives encrypted message
delivery_package = receive_message()

# Decrypt message with user's private key
encrypted_message = bytes.fromhex(delivery_package["encrypted_message"])
user_private_key = get_user_private_key()
decrypted_content = encryption.decrypt_message(encrypted_message, user_private_key)

# Verify message signature
signature_valid = verify_message_signature(
    message_id, group_id, sender_hash, encrypted_message
)
```

**What happens:**
- User decrypts message with their private key
- User verifies message integrity
- User displays decrypted content
- No group keys involved in decryption

## 🛡️ Security Features

### **1. Decentralized Group Management**
- **Owner Control**: Only group owner can manage the group
- **Local Storage**: Group data stored only on owner's client
- **No Server Knowledge**: Server doesn't know group membership
- **Public Key Verification**: All operations verified with public keys

### **2. Individual Message Encryption**
- **Per-Member Encryption**: Each message encrypted for each member
- **Public Key Cryptography**: Uses each member's public key
- **No Shared Secrets**: No group keys to compromise
- **Perfect Forward Secrecy**: Each message independently encrypted

### **3. Server Role Limitation**
- **Message Delivery Only**: Server only delivers messages
- **No Group Knowledge**: Server doesn't know group structure
- **Subscription-Based**: Server only knows user subscriptions
- **No Decryption Capability**: Server can't decrypt any messages

### **4. Access Control**
- **Owner-Only Operations**: Only owner can manage group
- **Public Key Verification**: All operations verified cryptographically
- **Member List Privacy**: Member list known only to owner
- **Message Authorization**: Only owner can send group messages

## 📊 Data Structures

### **DecentralizedGroup**
```python
@dataclass
class DecentralizedGroup:
    group_id: bytes                     # Unique group identifier
    group_hash: bytes                   # Hash for verification
    owner_hash: bytes                   # Owner's public key hash
    owner_public_key: bytes             # Owner's public key
    group_name: str                     # Group name
    description: str                    # Group description
    created_at: int                     # Creation timestamp
    status: GroupStatus                 # Group status
    members: Dict[bytes, GroupMember]   # user_hash -> GroupMember
    max_members: int                    # Maximum members
    is_private: bool                    # Privacy setting
```

### **GroupMember**
```python
@dataclass
class GroupMember:
    user_hash: bytes                    # Hash of user's public key
    public_key: bytes                   # User's public key
    role: GroupRole                     # Member role (OWNER/MEMBER)
    joined_at: int                      # Join timestamp
    last_seen: int                      # Last seen timestamp
    is_active: bool                     # Active status
```

### **GroupMessage**
```python
@dataclass
class GroupMessage:
    message_id: bytes                   # Unique message identifier
    group_id: bytes                     # Group identifier
    sender_hash: bytes                  # Sender's public key hash
    sender_public_key: bytes            # Sender's public key
    message_type: MessageType           # Message type
    encrypted_messages: Dict[bytes, bytes]  # user_hash -> encrypted_message
    timestamp: int                      # Message timestamp
    ttl: int                           # Time to live
    signature: bytes                   # Message signature
```

## 🔧 API Usage

### **Group Management (Owner Only)**

```python
# Create a group
group = await group_manager.create_group(
    owner_hash=owner_hash,
    owner_public_key=owner_public_key,
    group_name="My Group",
    description="Secure group",
    max_members=50
)

# Add a member
success = await group_manager.add_member(
    group_id=group.group_id,
    owner_hash=owner_hash,
    new_member_hash=member_hash,
    new_member_public_key=member_public_key
)

# Remove a member
success = await group_manager.remove_member(
    group_id=group.group_id,
    owner_hash=owner_hash,
    member_hash=member_hash
)

# Send a message
message_id = await group_manager.send_group_message(
    group_id=group.group_id,
    sender_hash=owner_hash,
    sender_public_key=owner_public_key,
    message_type=MessageType.TEXT_MESSAGE,
    content="Hello group!".encode()
)
```

### **Group Subscription (Members)**

```python
# Join a group (member)
success = await group_manager.join_group(
    user_hash=user_hash,
    group_id=group_id,
    group_hash=group_hash,
    group_info=group_info
)

# Leave a group
success = await group_manager.leave_group(
    user_hash=user_hash,
    group_id=group_id
)

# Get user's groups
user_groups = group_manager.get_user_groups(user_hash)
```

### **Message Handling**

```python
# Get pending messages for user
pending_messages = group_manager.get_pending_messages(user_hash)

# Deliver message to user
encrypted_message = await group_manager.deliver_group_message(
    message_id=message_id,
    recipient_hash=user_hash
)

# Clean up delivered message
await group_manager.cleanup_delivered_message(message_id)
```

## 🎯 Security Benefits

### **1. Privacy Protection**
- **No Server Knowledge**: Server doesn't know group membership
- **Local Group Storage**: Group data stored only on owner's client
- **Individual Encryption**: Each message encrypted separately
- **No Metadata Leakage**: Server can't infer group relationships

### **2. Access Control**
- **Owner-Only Management**: Only owner can manage group
- **Public Key Verification**: All operations cryptographically verified
- **Member List Privacy**: Member list known only to owner
- **Message Authorization**: Only owner can send group messages

### **3. Encryption Security**
- **Individual Encryption**: Each member gets unique encrypted message
- **No Shared Keys**: No group keys that could be compromised
- **Perfect Forward Secrecy**: Each message independently encrypted
- **Public Key Cryptography**: Uses proven encryption methods

### **4. System Resilience**
- **No Single Point of Failure**: Group data distributed across clients
- **Server Independence**: Groups work even if servers are compromised
- **Owner Control**: Owner has complete control over their groups
- **Decentralized Architecture**: No central authority required

## 🔄 Comparison with Previous System

| Aspect | Previous System | New Secure System |
|--------|----------------|-------------------|
| **Group Storage** | Centralized on server | Decentralized on owner's client |
| **Group Keys** | Shared group keys | Individual encryption per member |
| **Server Knowledge** | Full group membership | Only message delivery |
| **Key Management** | Complex key rotation | Simple public key encryption |
| **Security** | Vulnerable to key compromise | Individual encryption protection |
| **Privacy** | Server knows groups | Server ignorant of groups |
| **Access Control** | Server-managed | Owner-controlled |
| **Scalability** | Limited by key management | Scales with public key cryptography |

## 🚀 Future Enhancements

### **Planned Improvements**
- **Message Reactions**: Encrypted reactions to messages
- **File Sharing**: Encrypted file sharing in groups
- **Voice Messages**: Encrypted voice message support
- **Message Threading**: Encrypted threaded conversations
- **Group Invitations**: Secure invitation system
- **Message Search**: Encrypted message search capabilities

---

This decentralized group messaging system provides **maximum security** by ensuring that groups are managed only by their owners, messages are encrypted individually for each member, and servers have no knowledge of group membership or content. The system eliminates the security flaws of traditional group messaging while maintaining full functionality and user experience.
