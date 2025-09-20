# Key Rotation System

## Overview

The secIRC system implements a comprehensive key rotation mechanism for the first ring of relay servers. This ensures that cryptographic keys are periodically changed to maintain security over time, even if old keys are compromised.

## Key Features

### 🔄 **Periodic Key Rotation**
- **Automatic Rotation**: Keys rotate every 24 hours by default
- **Configurable Intervals**: Rotation intervals can be customized
- **Key Lifetime**: Keys have a maximum lifetime of 48 hours

### 🔐 **Secure Key Change Protocol**
- **Old Key Authentication**: Key change messages signed with old keys
- **New Key Verification**: New keys verified through connection testing
- **Acknowledgment System**: All ring members must acknowledge key changes
- **Connection Verification**: New connections tested before rotation completion

### 🧂 **Salt-Based Message Integrity**
- **Tamper Protection**: All messages protected with cryptographic salts
- **Message Integrity**: SHA-256 hashes verify message authenticity
- **Duplicate Detection**: Sequence numbers prevent replay attacks
- **Timestamp Validation**: Messages expire after 5 minutes

## Key Rotation Process

### Phase 1: Initiation
1. **Rotation Trigger**: Automatic timer or manual initiation
2. **New Key Generation**: Generate new public/private keypair
3. **Session Creation**: Create rotation session with unique ID
4. **Key Distribution**: Send key change messages to all ring members

### Phase 2: Key Distribution
1. **Message Creation**: Create signed key change messages
2. **Salt Protection**: Add cryptographic salt for integrity
3. **Network Transmission**: Send to all first ring members
4. **Signature Verification**: Recipients verify with old keys

### Phase 3: Acknowledgment
1. **Acknowledgment Generation**: Recipients generate new keypairs
2. **Acknowledgment Messages**: Send signed acknowledgments
3. **Acknowledgment Collection**: Wait for all acknowledgments
4. **Threshold Check**: Verify all members acknowledged

### Phase 4: Connection Verification
1. **New Connection Testing**: Test connections with new keys
2. **Verification Messages**: Send verification messages with new keys
3. **Connection Validation**: Verify all new connections work
4. **Rotation Completion**: Complete rotation and update keys

## Salt Protection System

### Message Structure
```
[Message Type][Payload][Salt][Integrity Hash]
```

### Salt Types
- **UDP_DATAGRAM**: For UDP packet integrity
- **RELAY_MESSAGE**: For relay-to-relay messages
- **GROUP_MESSAGE**: For group messaging
- **KEY_CHANGE**: For key rotation messages
- **CHALLENGE_REQUEST**: For authentication challenges

### Integrity Verification
1. **Salt Generation**: Unique salt for each message type
2. **Hash Calculation**: SHA-256 of payload + salt + metadata
3. **Integrity Check**: Verify hash matches expected value
4. **Tamper Detection**: Detect any message modification

## Security Features

### 🔒 **Cryptographic Security**
- **RSA-2048 Keys**: Strong asymmetric encryption
- **SHA-256 Hashing**: Secure message integrity
- **Salt Entropy**: High-quality random salt generation
- **Signature Verification**: All messages cryptographically signed

### 🛡️ **Attack Prevention**
- **Replay Protection**: Sequence numbers prevent replay attacks
- **Tamper Detection**: Salt-based integrity prevents modification
- **Timing Attacks**: Timestamp validation prevents timing attacks
- **Key Compromise**: Regular rotation limits exposure window

### 🔄 **Fault Tolerance**
- **Timeout Handling**: Rotation fails gracefully on timeout
- **Partial Failures**: System continues with available members
- **Rollback Capability**: Can revert to previous keys if needed
- **Health Monitoring**: Continuous monitoring of key health

## Configuration

### Key Rotation Settings
```yaml
key_rotation:
  rotation_interval: 86400  # 24 hours
  key_lifetime: 172800      # 48 hours
  rotation_timeout: 300     # 5 minutes
  max_retries: 3
```

### Salt Protection Settings
```yaml
salt_protection:
  salt_length: 32           # 32 bytes
  integrity_hash_length: 32 # 32 bytes
  max_message_age: 300      # 5 minutes
  duplicate_detection: true
  timestamp_validation: true
```

## API Usage

### Starting Key Rotation
```python
# Automatic rotation (every 24 hours)
await key_rotation_manager.start_key_rotation_service()

# Manual rotation
await key_rotation_manager.initiate_key_rotation()
```

### Salt Protection
```python
# Create protected message
salted_message = salt_protection.create_salted_message(
    message_type="key_change",
    payload=message_data,
    salt_type=SaltType.KEY_CHANGE
)

# Verify message integrity
is_valid = salt_protection.verify_salted_message(salted_message)
```

### Monitoring
```python
# Get rotation status
status = key_rotation_manager.get_rotation_status()

# Get salt protection stats
stats = salt_protection.get_salt_protection_stats()
```

## Implementation Details

### Key Rotation Manager
- **Session Management**: Tracks active rotation sessions
- **Phase Coordination**: Manages rotation phases
- **Timeout Handling**: Handles rotation timeouts
- **Statistics Tracking**: Monitors rotation performance

### Salt Protection System
- **Message Protection**: Protects all network messages
- **Integrity Verification**: Verifies message authenticity
- **Sequence Tracking**: Prevents duplicate messages
- **Cleanup Management**: Manages sequence number cleanup

### Network Integration
- **UDP Integration**: Works with UDP datagram transport
- **Relay Integration**: Integrates with relay network
- **Group Integration**: Works with group messaging
- **Challenge Integration**: Integrates with authentication

## Security Considerations

### Key Management
- **Secure Generation**: Keys generated with cryptographically secure random
- **Secure Storage**: Private keys encrypted with strong passwords
- **Secure Transmission**: Key changes transmitted securely
- **Secure Verification**: New keys verified before activation

### Message Security
- **End-to-End Integrity**: Messages protected from source to destination
- **Tamper Detection**: Any modification detected immediately
- **Replay Prevention**: Sequence numbers prevent replay attacks
- **Timing Protection**: Timestamp validation prevents timing attacks

### Network Security
- **Authentication**: All messages authenticated with signatures
- **Authorization**: Only authorized members can participate
- **Confidentiality**: Message content encrypted end-to-end
- **Availability**: System continues even with some failures

## Monitoring and Logging

### Rotation Monitoring
- **Status Tracking**: Real-time rotation status
- **Performance Metrics**: Rotation success/failure rates
- **Timing Analysis**: Rotation duration tracking
- **Error Reporting**: Detailed error logging

### Salt Protection Monitoring
- **Integrity Statistics**: Message verification rates
- **Tamper Detection**: Tamper attempt logging
- **Performance Metrics**: Verification performance
- **Error Analysis**: Detailed error reporting

## Future Enhancements

### Planned Features
- **Post-Quantum Cryptography**: Support for quantum-resistant algorithms
- **Zero-Knowledge Proofs**: Enhanced authentication without key exposure
- **Advanced Key Derivation**: More sophisticated key generation
- **Distributed Key Management**: Decentralized key management

### Research Areas
- **Key Rotation Optimization**: More efficient rotation protocols
- **Salt Optimization**: Improved salt generation and management
- **Security Analysis**: Formal security analysis of protocols
- **Performance Optimization**: Improved performance and scalability
