# secIRC User Manual

## Overview

Welcome to secIRC, the anonymous, censorship-resistant messaging system. This manual will guide you through using secIRC to communicate securely and anonymously.

## 🚀 Getting Started

### First Launch

When you first start secIRC, you'll be guided through the setup process:

1. **Create Your Identity**: Choose a nickname and set a strong password
2. **Generate Keys**: Your cryptographic keys will be generated automatically
3. **Connect to Network**: secIRC will automatically discover and connect to relay servers
4. **Start Messaging**: You're ready to send anonymous messages!

### Your Anonymous Identity

In secIRC, you are identified by a cryptographic hash of your public key, not by your real name or email address. This ensures complete anonymity.

- **Your Hash**: A unique identifier like `a1b2c3d4e5f6...`
- **Your Nickname**: A display name you choose (can be changed anytime)
- **Your Keys**: Cryptographic keys that protect your messages

## 💬 Basic Messaging

### Sending Messages

1. **Find a Contact**: You need their hash ID to send messages
2. **Compose Message**: Type your message in the compose area
3. **Send**: Click send - your message is encrypted and sent anonymously

### Receiving Messages

- **Automatic Reception**: Messages are received automatically
- **Decryption**: Messages are decrypted using your private key
- **Display**: Messages appear in your conversation window

### Message Types

- **Text Messages**: Standard text communication
- **File Messages**: Send encrypted files
- **Voice Messages**: Send encrypted voice recordings

## 👥 Group Messaging

### Creating Groups

1. **Create Group**: Click "Create Group" button
2. **Set Name**: Choose a group name
3. **Add Members**: Add members by their hash IDs
4. **Start Chatting**: Begin group conversation

### Joining Groups

1. **Receive Invitation**: Get group invitation from another member
2. **Accept Invitation**: Click to join the group
3. **Start Participating**: Begin chatting in the group

### Group Management

- **Add Members**: Invite new members to the group
- **Remove Members**: Remove members from the group
- **Leave Group**: Leave a group anytime
- **Group Settings**: Modify group settings

## 🔐 Security Features

### End-to-End Encryption

All messages are encrypted end-to-end:
- **Sender Encryption**: Messages encrypted with recipient's public key
- **Relay Forwarding**: Relays cannot read message content
- **Recipient Decryption**: Only recipient can decrypt with private key

### Anonymous Routing

Messages are routed through multiple relay servers:
- **No Metadata**: Relays don't store who sent what to whom
- **Random Paths**: Messages take different paths each time
- **Traffic Obfuscation**: Dummy traffic hides real communication

### Key Management

- **Automatic Rotation**: Keys rotate automatically every 24 hours
- **Password Protection**: Private keys protected with your password
- **Secure Storage**: Keys stored encrypted on your device

## 🌐 Network Features

### Relay Discovery

secIRC automatically discovers relay servers:
- **DNS Discovery**: Finds relays via DNS records
- **Web Discovery**: Discovers relays via web APIs
- **Peer Discovery**: Learns about relays from other users

### Connection Management

- **Automatic Connection**: Connects to best available relays
- **Failover**: Automatically switches to backup relays
- **Load Balancing**: Distributes load across multiple relays

## ⚙️ Settings and Configuration

### User Settings

Access settings through the menu:

#### General Settings
- **Nickname**: Change your display name
- **Language**: Select interface language
- **Theme**: Choose light or dark theme
- **Notifications**: Configure message notifications

#### Security Settings
- **Password**: Change your password
- **Key Rotation**: Configure automatic key rotation
- **Message Retention**: Set how long to keep messages
- **Auto-Lock**: Set automatic lock timeout

#### Network Settings
- **Relay Selection**: Choose preferred relays
- **Connection Timeout**: Set connection timeout
- **Retry Attempts**: Configure retry behavior
- **Proxy Settings**: Configure proxy if needed

### Advanced Settings

#### Privacy Settings
- **Message Padding**: Add padding to messages
- **Dummy Traffic**: Generate dummy traffic
- **Traffic Obfuscation**: Obfuscate traffic patterns
- **Metadata Protection**: Protect message metadata

#### Performance Settings
- **Message Cache**: Configure message cache size
- **Connection Pool**: Set connection pool size
- **Threading**: Configure threading options
- **Memory Usage**: Set memory usage limits

## 🔧 Troubleshooting

### Common Issues

#### Connection Problems
- **Check Internet**: Ensure you have internet connection
- **Firewall**: Check if firewall is blocking secIRC
- **Proxy**: Configure proxy settings if needed
- **Relay Status**: Check if relays are online

#### Message Issues
- **Recipient Hash**: Verify recipient hash is correct
- **Key Exchange**: Ensure key exchange completed
- **Network**: Check network connectivity
- **Relay Status**: Verify relays are functioning

#### Performance Issues
- **Memory Usage**: Check available memory
- **CPU Usage**: Monitor CPU usage
- **Network Speed**: Check network speed
- **Relay Load**: Try different relays

### Getting Help

#### Built-in Help
- **Help Menu**: Access help from the menu
- **Tooltips**: Hover over buttons for help
- **Status Messages**: Read status messages for guidance

#### Community Support
- **GitHub Issues**: Report bugs and ask questions
- **Discussions**: Join community discussions
- **Documentation**: Read comprehensive documentation
- **Tutorials**: Follow step-by-step tutorials

## 📱 Mobile Usage

### Mobile Client

secIRC is designed to work on mobile devices:
- **Responsive Design**: Adapts to different screen sizes
- **Touch Interface**: Optimized for touch interaction
- **Mobile Notifications**: Push notifications for messages
- **Offline Support**: Works offline with message queuing

### Mobile Security

- **Screen Lock**: Lock screen when not in use
- **Biometric Auth**: Use fingerprint or face recognition
- **Secure Storage**: Keys stored in secure enclave
- **Network Security**: Use secure networks only

## 🔒 Privacy and Anonymity

### What secIRC Protects

- **Message Content**: End-to-end encrypted
- **Sender Identity**: Anonymous hash-based identity
- **Recipient Identity**: Anonymous hash-based identity
- **Communication Patterns**: Obfuscated with dummy traffic
- **Metadata**: No metadata stored on relays

### What secIRC Cannot Protect

- **Device Security**: Keep your device secure
- **Network Security**: Use secure networks
- **User Behavior**: Be careful about what you share
- **Social Engineering**: Be aware of social engineering attacks

### Best Practices

- **Strong Passwords**: Use strong, unique passwords
- **Regular Updates**: Keep secIRC updated
- **Secure Networks**: Use secure, trusted networks
- **Backup Keys**: Backup your keys securely
- **Identity Rotation**: Rotate identities periodically

## 🎯 Advanced Features

### File Sharing

- **Encrypted Files**: Files encrypted end-to-end
- **Size Limits**: Check file size limits
- **Type Restrictions**: Some file types may be restricted
- **Progress Tracking**: Monitor file transfer progress

### Voice Messages

- **Encrypted Audio**: Voice messages encrypted
- **Quality Settings**: Configure audio quality
- **Recording**: Record voice messages
- **Playback**: Play received voice messages

### Message Search

- **Full-Text Search**: Search through message history
- **Date Filtering**: Filter messages by date
- **Contact Filtering**: Filter messages by contact
- **Group Filtering**: Filter messages by group

## 📊 Statistics and Monitoring

### Connection Statistics

- **Uptime**: How long you've been connected
- **Messages Sent**: Number of messages sent
- **Messages Received**: Number of messages received
- **Relay Status**: Status of connected relays

### Network Statistics

- **Relay Count**: Number of available relays
- **Connection Quality**: Quality of connections
- **Latency**: Message delivery latency
- **Throughput**: Message throughput

### Security Statistics

- **Encryption Status**: Status of encryption
- **Key Rotation**: Key rotation history
- **Security Events**: Security-related events
- **Threat Detection**: Detected threats

## 🚀 Tips and Tricks

### Productivity Tips

- **Keyboard Shortcuts**: Learn keyboard shortcuts
- **Message Templates**: Create message templates
- **Auto-Reply**: Set up auto-reply messages
- **Message Scheduling**: Schedule messages for later

### Security Tips

- **Regular Backups**: Backup your keys regularly
- **Identity Verification**: Verify identities before sharing sensitive info
- **Network Monitoring**: Monitor network connections
- **Threat Awareness**: Stay aware of security threats

### Performance Tips

- **Relay Selection**: Choose fast, reliable relays
- **Message Size**: Keep messages reasonably sized
- **Connection Management**: Manage connections efficiently
- **Resource Usage**: Monitor resource usage

---

This user manual provides comprehensive guidance for using secIRC effectively and securely. For more advanced topics, refer to the Administrator Guide and Developer Guide.
