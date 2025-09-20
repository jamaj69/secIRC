# secIRC System Architecture

## Overview

secIRC is an anonymous, censorship-resistant messaging system built on a distributed mesh network of relay servers. The system provides end-to-end encrypted communication with no metadata storage, ensuring complete anonymity and resistance to censorship.

## 🏗️ High-Level Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        secIRC Ecosystem                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   Client A  │    │   Client B  │    │   Client C  │        │
│  │             │    │             │    │             │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│         │                   │                   │              │
│         └───────────────────┼───────────────────┘              │
│                             │                                  │
│  ┌─────────────────────────────────────────────────────────────┤
│  │                Mesh Network of Relay Servers               │
│  │                                                             │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  │ First Ring  │    │ First Ring  │    │ First Ring  │    │
│  │  │   Relay 1   │    │   Relay 2   │    │   Relay 3   │    │
│  │  └─────────────┘    └─────────────┘    └─────────────┘    │
│  │         │                   │                   │          │
│  │         └───────────────────┼───────────────────┘          │
│  │                             │                              │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  │   Relay 4   │    │   Relay 5   │    │   Relay 6   │    │
│  │  └─────────────┘    └─────────────┘    └─────────────┘    │
│  └─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────────┤
│  │              Discovery and Bootstrap Services              │
│  │                                                             │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  │    DNS      │    │   Web API   │    │   Peer      │    │
│  │  │ Discovery   │    │ Discovery   │    │ Discovery   │    │
│  │  └─────────────┘    └─────────────┘    └─────────────┘    │
│  └─────────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Core Components

### 1. Anonymous Client
- **Purpose**: End-user interface for anonymous messaging
- **Features**:
  - End-to-end encryption
  - Anonymous identity management
  - Group messaging
  - File sharing
  - Voice messaging

### 2. Relay Server Network
- **Purpose**: Message routing and relay infrastructure
- **Features**:
  - No metadata storage
  - Message forwarding
  - Network discovery
  - Load balancing

### 3. First Ring (Trusted Relays)
- **Purpose**: Core trusted relay servers
- **Features**:
  - Cryptographic authentication
  - Key rotation management
  - Consensus mechanisms
  - Network governance

### 4. Mesh Network
- **Purpose**: Distributed relay communication
- **Features**:
  - Peer-to-peer discovery
  - Challenge-based authentication
  - Ring expansion
  - Fault tolerance

## 🌐 Network Architecture

### Mesh Topology
```
                    ┌─────────────┐
                    │   Client    │
                    └─────────────┘
                           │
                    ┌─────────────┐
                    │   Relay A   │
                    └─────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
   │   Relay B   │   │   Relay C   │   │   Relay D   │
   └─────────────┘   └─────────────┘   └─────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌─────────────┐
                    │   Client    │
                    └─────────────┘
```

### Message Flow
1. **Client A** encrypts message with **Client B**'s public key
2. **Client A** sends encrypted message to **Relay A**
3. **Relay A** forwards message to **Relay B** (no metadata stored)
4. **Relay B** forwards message to **Relay C**
5. **Relay C** forwards message to **Client B**
6. **Client B** decrypts message with private key

## 🔐 Security Architecture

### Encryption Layers
```
┌─────────────────────────────────────────────────────────────┐
│                    Message Content                          │
├─────────────────────────────────────────────────────────────┤
│                End-to-End Encryption                        │
│              (RSA-2048 + AES-256)                          │
├─────────────────────────────────────────────────────────────┤
│                Transport Encryption                         │
│              (UDP + Salt Protection)                       │
├─────────────────────────────────────────────────────────────┤
│                Network Layer                                │
│              (UDP Datagrams)                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Management
- **User Keys**: RSA-2048 keypairs for end-to-end encryption
- **Relay Keys**: RSA-2048 keypairs for relay authentication
- **Session Keys**: AES-256 keys for transport encryption
- **Key Rotation**: Automatic key rotation every 24 hours

## 📡 Protocol Stack

### Application Layer
- **Anonymous Protocol**: Core messaging protocol
- **Group Management**: Group creation and management
- **File Transfer**: Encrypted file sharing
- **Voice Messaging**: Encrypted voice communication

### Security Layer
- **End-to-End Encryption**: RSA-2048 + AES-256
- **Key Rotation**: Automatic key management
- **Salt Protection**: Message integrity protection
- **Challenge Authentication**: Relay authentication

### Network Layer
- **UDP Transport**: Connectionless messaging
- **Relay Discovery**: Automatic relay discovery
- **Mesh Networking**: Distributed relay communication
- **Fault Tolerance**: Network resilience

## 🏛️ Data Architecture

### Message Structure
```
┌─────────────────────────────────────────────────────────────┐
│                    Message Header                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Message Type│ │ Timestamp   │ │ Sequence #  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
├─────────────────────────────────────────────────────────────┤
│                    Encrypted Payload                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Recipient   │ │ Message     │ │ Metadata    │          │
│  │ Hash        │ │ Content     │ │ (Optional)  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
├─────────────────────────────────────────────────────────────┤
│                    Integrity Protection                     │
│  ┌─────────────┐ ┌─────────────┐                          │
│  │ Salt        │ │ Hash        │                          │
│  │ (32 bytes)  │ │ (32 bytes)  │                          │
│  └─────────────┘ └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### Identity System
- **User Identity**: SHA-256 hash of public key
- **Group Identity**: SHA-256 hash of group public key
- **Relay Identity**: SHA-256 hash of relay public key
- **Anonymous**: No real-world identity information stored

## 🔄 System Flow

### Message Sending Flow
```
1. User Input → 2. Encryption → 3. Relay Selection → 4. Network Send
     ↓              ↓              ↓              ↓
5. Relay Forward → 6. Mesh Routing → 7. Final Relay → 8. User Receive
```

### Relay Discovery Flow
```
1. Bootstrap → 2. DNS Query → 3. Web API → 4. Peer Discovery
     ↓              ↓              ↓              ↓
5. Relay List → 6. Health Check → 7. Selection → 8. Connection
```

### Key Rotation Flow
```
1. Timer Trigger → 2. Key Generation → 3. Distribution → 4. Acknowledgment
     ↓              ↓              ↓              ↓
5. Verification → 6. Connection Test → 7. Activation → 8. Cleanup
```

## 🛡️ Security Model

### Threat Model
- **Network Surveillance**: Resisted through encryption and anonymity
- **Relay Compromise**: Mitigated through no metadata storage
- **Traffic Analysis**: Prevented through dummy traffic and padding
- **Censorship**: Bypassed through distributed network

### Security Properties
- **Confidentiality**: End-to-end encryption
- **Integrity**: Salt-based message protection
- **Authenticity**: Cryptographic signatures
- **Anonymity**: No identity information stored
- **Availability**: Distributed fault-tolerant network

## 📊 Performance Characteristics

### Scalability
- **Horizontal Scaling**: Add more relay servers
- **Load Distribution**: Automatic load balancing
- **Geographic Distribution**: Global relay network
- **Capacity Planning**: Dynamic capacity adjustment

### Reliability
- **Fault Tolerance**: Multiple relay paths
- **Redundancy**: Backup relay servers
- **Self-Healing**: Automatic network recovery
- **Monitoring**: Continuous health monitoring

## 🔧 Implementation Architecture

### Core Modules
```
src/
├── protocol/           # Core protocol implementation
│   ├── anonymous_protocol.py    # Main protocol handler
│   ├── encryption.py            # End-to-end encryption
│   ├── relay_discovery.py       # Relay discovery
│   ├── mesh_network.py          # Mesh networking
│   ├── key_rotation.py          # Key rotation system
│   └── salt_protection.py       # Salt-based protection
├── server/             # Relay server implementation
│   ├── relay_server.py          # Main server
│   └── main.py                  # Server entry point
├── client/             # Client implementation
│   └── main.py                  # Client entry point
└── security/           # Security modules
    ├── key_management.py        # Key management
    └── authentication.py        # Authentication
```

### Configuration
```
config/
├── server.yaml         # Server configuration
├── client.yaml         # Client configuration
└── security.yaml       # Security settings
```

## 🚀 Deployment Architecture

### Development Environment
- **Local Testing**: Single relay server
- **Integration Testing**: Multiple relay servers
- **Performance Testing**: Load testing with multiple clients

### Production Environment
- **Distributed Deployment**: Multiple geographic locations
- **Load Balancing**: Automatic load distribution
- **Monitoring**: Comprehensive monitoring and alerting
- **Backup**: Redundant systems and data backup

## 📈 Future Architecture

### Planned Enhancements
- **Post-Quantum Cryptography**: Quantum-resistant algorithms
- **Zero-Knowledge Proofs**: Enhanced privacy
- **Blockchain Integration**: Decentralized governance
- **Mobile Support**: Mobile client applications

### Research Areas
- **Advanced Routing**: More sophisticated routing algorithms
- **Privacy Enhancements**: Additional privacy protections
- **Performance Optimization**: Improved performance and scalability
- **Security Analysis**: Formal security verification

---

This architecture provides a robust, secure, and scalable foundation for anonymous, censorship-resistant messaging while maintaining high performance and reliability.
