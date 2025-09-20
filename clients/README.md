# secIRC Mobile Clients

## Overview

This directory contains the mobile client implementations for secIRC - a secure, anonymous messaging system. The clients provide end-to-end encrypted communication through a decentralized relay network with hardware-backed security.

## 📱 Available Clients

### **Android Client** (`android/`)
- **Platform**: Android 5.0+ (API 21+)
- **Language**: Kotlin
- **Architecture**: MVVM with Jetpack Compose
- **Security**: Android Keystore, Biometric Authentication
- **Features**: Hardware-backed key storage, kernel integrity monitoring

### **iOS Client** (`ios/`)
- **Platform**: iOS 15.0+
- **Language**: Swift
- **Architecture**: MVVM with SwiftUI
- **Security**: Secure Enclave, Touch ID/Face ID
- **Features**: Hardware-backed key storage, kernel integrity monitoring

## 🔒 Security Features

### **Hardware Security**
- **Android**: Android Keystore integration
- **iOS**: Secure Enclave integration
- **Biometric Authentication**: Fingerprint/Face unlock
- **Memory Protection**: Secure memory handling
- **Kernel Monitoring**: Device integrity verification

### **Encryption**
- **End-to-End Encryption**: Individual message encryption
- **Perfect Forward Secrecy**: Key rotation
- **Public Key Cryptography**: RSA 2048-bit keys
- **Message Integrity**: Cryptographic signatures
- **Traffic Analysis Resistance**: Dummy traffic and padding

### **Network Security**
- **TLS 1.3**: Encrypted communication
- **Certificate Pinning**: Prevent man-in-the-middle attacks
- **UDP Protocol**: Censorship-resistant communication
- **Relay Network**: Decentralized message routing
- **No Metadata Storage**: Servers don't store message metadata

## 🏗️ Architecture

### **Core Components**
```
┌─────────────────┐    ┌─────────────────┐
│   Android App   │    │    iOS App      │
├─────────────────┤    ├─────────────────┤
│  UI Layer       │    │  UI Layer       │
│  (Jetpack       │    │  (SwiftUI)      │
│   Compose)      │    │                 │
├─────────────────┤    ├─────────────────┤
│  ViewModel      │    │  ViewModel      │
│  Layer          │    │  Layer          │
├─────────────────┤    ├─────────────────┤
│  Service Layer  │    │  Service Layer  │
│  - KeyManager   │    │  - KeyManager   │
│  - NetworkMgr   │    │  - NetworkMgr   │
│  - GroupMgr     │    │  - GroupMgr     │
│  - SecurityMgr  │    │  - SecurityMgr  │
├─────────────────┤    ├─────────────────┤
│  Protocol Layer │    │  Protocol Layer │
│  - secIRC       │    │  - secIRC       │
│  - Encryption   │    │  - Encryption   │
│  - Network      │    │  - Network      │
└─────────────────┘    └─────────────────┘
```

### **Security Layers**
1. **Hardware Security**: Platform-specific secure storage
2. **Biometric Authentication**: User authentication
3. **Memory Protection**: Secure memory handling
4. **Network Security**: TLS 1.3 with certificate pinning
5. **Kernel Monitoring**: Device integrity verification
6. **Application Security**: Code obfuscation and integrity

## 🚀 Quick Start

### **Android Development**
```bash
# Navigate to Android project
cd clients/android

# Open in Android Studio
android-studio .

# Build the project
./gradlew build

# Run tests
./gradlew test
```

### **iOS Development**
```bash
# Navigate to iOS project
cd clients/ios

# Open in Xcode
open secIRC.xcodeproj

# Build the project
xcodebuild -project secIRC.xcodeproj -scheme secIRC -configuration Debug

# Run tests
xcodebuild test -project secIRC.xcodeproj -scheme secIRC
```

## 📊 Feature Comparison

| Feature | Android | iOS |
|---------|---------|-----|
| **Hardware Security** | ✅ Android Keystore | ✅ Secure Enclave |
| **Biometric Auth** | ✅ Fingerprint/Face | ✅ Touch ID/Face ID |
| **Memory Protection** | ✅ Secure Memory | ✅ Secure Memory |
| **Kernel Monitoring** | ✅ Device Integrity | ✅ Device Integrity |
| **Network Security** | ✅ TLS 1.3 + Pinning | ✅ TLS 1.3 + Pinning |
| **Group Messaging** | ✅ Decentralized | ✅ Decentralized |
| **File Sharing** | ✅ Encrypted | ✅ Encrypted |
| **Voice Messages** | ✅ Encrypted | ✅ Encrypted |
| **Message Reactions** | ✅ Encrypted | ✅ Encrypted |
| **Offline Support** | ✅ Local Storage | ✅ Local Storage |
| **Push Notifications** | ✅ Encrypted | ✅ Encrypted |

## 🔧 Configuration

### **Security Settings**
```kotlin
// Android
object SecurityConfig {
    const val KEY_ALGORITHM = "RSA"
    const val KEY_SIZE = 2048
    const val BIOMETRIC_AUTH_REQUIRED = true
    const val MEMORY_PROTECTION_ENABLED = true
}
```

```swift
// iOS
struct SecurityConfig {
    static let keyAlgorithm = kSecAttrKeyTypeRSA
    static let keySize = 2048
    static let biometricAuthRequired = true
    static let memoryProtectionEnabled = true
}
```

### **Network Settings**
```kotlin
// Android
object NetworkConfig {
    const val DEFAULT_UDP_PORT = 6667
    const val MAX_PACKET_SIZE = 1400
    const val CERTIFICATE_PINNING_ENABLED = true
    const val TLS_VERSION = "TLSv1.3"
}
```

```swift
// iOS
struct NetworkConfig {
    static let defaultUDPPort: UInt16 = 6667
    static let maxPacketSize = 1400
    static let certificatePinningEnabled = true
    static let tlsVersion = "TLSv1.3"
}
```

## 🛡️ Security Implementation

### **Key Management**
- **Hardware-backed storage** using platform-specific secure storage
- **Biometric authentication** for key access
- **Automatic key rotation** for perfect forward secrecy
- **Secure key generation** with proper entropy
- **Key escrow prevention** through hardware security

### **Message Encryption**
- **Individual encryption** for each group member
- **Public key cryptography** with RSA 2048-bit keys
- **Message integrity** with cryptographic signatures
- **Perfect forward secrecy** with key rotation
- **Traffic analysis resistance** with dummy traffic

### **Network Security**
- **TLS 1.3** for encrypted communication
- **Certificate pinning** to prevent MITM attacks
- **UDP protocol** for censorship resistance
- **Relay network** for decentralized routing
- **No metadata storage** on servers

## 📱 User Experience

### **Authentication Flow**
1. **App Launch**: Check for existing keys
2. **Biometric Auth**: Authenticate with fingerprint/face
3. **Key Access**: Access hardware-backed keys
4. **Network Connect**: Connect to relay network
5. **Ready**: App ready for secure messaging

### **Messaging Flow**
1. **Compose Message**: User types message
2. **Encrypt Message**: Encrypt with recipient's public key
3. **Send to Relay**: Send through relay network
4. **Relay Routing**: Message routed through random relays
5. **Delivery**: Message delivered to recipient
6. **Decrypt**: Recipient decrypts with private key

### **Group Messaging Flow**
1. **Create Group**: Owner creates group with member list
2. **Add Members**: Owner adds members with public keys
3. **Send Message**: Owner sends message to group
4. **Individual Encryption**: Message encrypted for each member
5. **Relay Distribution**: Encrypted messages sent to relays
6. **Member Delivery**: Each member receives their encrypted copy
7. **Individual Decryption**: Each member decrypts with their private key

## 🧪 Testing

### **Security Testing**
- **Key Management Tests**: Verify secure key generation and storage
- **Encryption Tests**: Verify message encryption and decryption
- **Authentication Tests**: Verify biometric authentication
- **Network Tests**: Verify secure network communication
- **Integrity Tests**: Verify message integrity and signatures

### **Performance Testing**
- **Memory Usage**: Monitor memory consumption
- **Battery Usage**: Monitor battery consumption
- **Network Usage**: Monitor network traffic
- **CPU Usage**: Monitor CPU consumption
- **Storage Usage**: Monitor storage consumption

### **Compatibility Testing**
- **Device Compatibility**: Test on various devices
- **OS Compatibility**: Test on different OS versions
- **Network Compatibility**: Test on different networks
- **Security Compatibility**: Test with different security settings

## 📦 Dependencies

### **Android Dependencies**
- **Kotlin**: 1.6.21
- **AndroidX**: Core, AppCompat, Lifecycle
- **Jetpack Compose**: 1.2.0
- **Material Design**: 1.6.1
- **Biometric**: 1.1.0
- **Security Crypto**: 1.1.0
- **OkHttp**: 4.9.3
- **Retrofit**: 2.9.0

### **iOS Dependencies**
- **SwiftUI**: Built-in
- **Combine**: Built-in
- **CryptoKit**: Built-in
- **Security**: Built-in
- **LocalAuthentication**: Built-in
- **KeychainAccess**: 4.2.2
- **Alamofire**: 5.6.4

## 🚀 Deployment

### **Android Deployment**
```bash
# Build release APK
./gradlew assembleRelease

# Sign APK
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 \
  -keystore secirc-release-key.keystore \
  app/build/outputs/apk/release/app-release-unsigned.apk \
  secirc-release-key

# Align APK
zipalign -v 4 app-release-unsigned.apk secirc-release.apk
```

### **iOS Deployment**
```bash
# Build release
xcodebuild -project secIRC.xcodeproj -scheme secIRC -configuration Release

# Archive for App Store
xcodebuild archive -project secIRC.xcodeproj -scheme secIRC -configuration Release -archivePath secIRC.xcarchive

# Export for App Store
xcodebuild -exportArchive -archivePath secIRC.xcarchive -exportPath ./Export -exportOptionsPlist ExportOptions.plist
```

## 📚 Documentation

- [Android Client](android/README.md)
- [iOS Client](ios/README.md)
- [Security Architecture](docs/SECURITY.md)
- [API Reference](docs/API.md)
- [User Guide](docs/USER_GUIDE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## 🔗 Links

- [Main secIRC Project](../../README.md)
- [Server Implementation](../../src/server/README.md)
- [Protocol Documentation](../../docs/README.md)
- [Security Documentation](../../docs/SECURITY_MODEL.md)
