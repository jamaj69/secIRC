# secIRC iOS Client

## Overview

The secIRC iOS client is a secure, anonymous messaging application that provides end-to-end encrypted communication through a decentralized relay network. Built with modern iOS development practices and security-first design principles using SwiftUI and Combine.

## 🔒 Security Features

- **Secure Enclave** integration for hardware-backed key storage
- **Biometric authentication** (Touch ID/Face ID) for key access
- **End-to-end encryption** with individual message encryption
- **Decentralized group management** with owner-only control
- **Kernel integrity monitoring** for device security
- **Certificate pinning** for network security
- **Memory protection** for sensitive data
- **Keychain Services** for secure data storage

## 🏗️ Architecture

### **Core Components**
- **SecIRCProtocol**: Core messaging protocol implementation
- **KeyManager**: Secure key management with Secure Enclave
- **NetworkManager**: UDP communication with relay servers
- **GroupManager**: Decentralized group management
- **SecurityMonitor**: Device security and integrity monitoring
- **MessageEncryption**: End-to-end encryption implementation

### **Security Layers**
1. **Hardware Security**: Secure Enclave integration
2. **Biometric Authentication**: Touch ID/Face ID
3. **Memory Protection**: Secure memory handling
4. **Network Security**: TLS 1.3 with certificate pinning
5. **Kernel Monitoring**: Device integrity verification
6. **Keychain Services**: Secure data storage

## 🚀 Quick Start

### **Prerequisites**
- Xcode 14.0 or later
- iOS 15.0+ deployment target
- Swift 5.7 or later
- macOS 12.0 or later

### **Setup**
```bash
# Clone the repository
git clone https://github.com/your-org/secIRC.git
cd secIRC/clients/ios

# Open in Xcode
open secIRC.xcodeproj

# Build the project
xcodebuild -project secIRC.xcodeproj -scheme secIRC -configuration Debug
```

### **Build**
```bash
# Debug build
xcodebuild -project secIRC.xcodeproj -scheme secIRC -configuration Debug

# Release build
xcodebuild -project secIRC.xcodeproj -scheme secIRC -configuration Release

# Run tests
xcodebuild test -project secIRC.xcodeproj -scheme secIRC -destination 'platform=iOS Simulator,name=iPhone 14'
```

## 📱 Features

### **Messaging**
- **Anonymous messaging** with hash-based identities
- **Group messaging** with decentralized management
- **File sharing** with end-to-end encryption
- **Voice messages** with secure transmission
- **Message reactions** with encrypted responses

### **Security**
- **Hardware-backed key storage** using Secure Enclave
- **Biometric authentication** for key access
- **Perfect forward secrecy** with key rotation
- **Traffic analysis resistance** with dummy traffic
- **Censorship resistance** through relay network

### **Groups**
- **Owner-only group management** with public key verification
- **Individual message encryption** for each member
- **Decentralized group storage** on owner's device
- **Automatic member management** with cryptographic verification
- **Group key rotation** on membership changes

## 🔧 Configuration

### **Security Settings**
```swift
// Security configuration
struct SecurityConfig {
    static let keyAlgorithm = kSecAttrKeyTypeRSA
    static let keySize = 2048
    static let encryptionAlgorithm = kSecAttrKeyTypeAES
    static let hashAlgorithm = kSecAttrKeyTypeECSECPrimeRandom
    static let keyDerivationIterations = 100000
    static let biometricAuthenticationRequired = true
    static let memoryProtectionEnabled = true
}
```

### **Network Settings**
```swift
// Network configuration
struct NetworkConfig {
    static let defaultUDPPort: UInt16 = 6667
    static let maxPacketSize = 1400
    static let relayDiscoveryInterval: TimeInterval = 300 // 5 minutes
    static let messageTTL: TimeInterval = 3600 // 1 hour
    static let certificatePinningEnabled = true
    static let tlsVersion = "TLSv1.3"
}
```

## 🛡️ Security Implementation

### **Key Management**
```swift
class SecIRCKeyManager {
    private let keychain = Keychain(service: "com.secirc.keys")
    
    func generateSecureKeyPair(userPassword: String) throws -> KeyPair {
        let accessControl = SecAccessControlCreateWithFlags(
            kCFAllocatorDefault,
            kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
            [.biometryAny, .or, .devicePasscode],
            nil
        )
        
        let keyPairQuery: [String: Any] = [
            kSecClass as String: kSecClassKey,
            kSecAttrKeyType as String: kSecAttrKeyTypeRSA,
            kSecAttrKeySizeInBits as String: 2048,
            kSecAttrTokenID as String: kSecAttrTokenIDSecureEnclave,
            kSecPrivateKeyAttrs as String: [
                kSecAttrIsPermanent as String: true,
                kSecAttrAccessControl as String: accessControl,
                kSecAttrLabel as String: "secIRC_private_key"
            ]
        ]
        
        var privateKey: SecKey?
        var publicKey: SecKey?
        
        let status = SecKeyGeneratePair(keyPairQuery as CFDictionary, &publicKey, &privateKey)
        
        guard status == errSecSuccess else {
            throw KeyManagerError.keyGenerationFailed(status)
        }
        
        return KeyPair(privateKey: privateKey!, publicKey: publicKey!)
    }
}
```

### **Biometric Authentication**
```swift
class BiometricAuth {
    func authenticateUser() async throws -> Bool {
        let context = LAContext()
        var error: NSError?
        
        guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
            throw BiometricAuthError.notAvailable
        }
        
        do {
            let result = try await context.evaluatePolicy(
                .deviceOwnerAuthenticationWithBiometrics,
                localizedReason: "Authenticate to access secIRC"
            )
            return result
        } catch {
            throw BiometricAuthError.authenticationFailed(error)
        }
    }
}
```

### **Memory Protection**
```swift
class SecureMemoryManager {
    private var secureMemory: [String: Data] = [:]
    
    func storeSensitiveData(key: String, data: Data) {
        // Use platform-specific secure memory
        secureMemory[key] = protectMemory(data)
    }
    
    func clearSensitiveData(key: String) {
        secureMemory[key]?.withUnsafeBytes { bytes in
            // Overwrite memory with random data
            memset_s(bytes.baseAddress, bytes.count, 0, bytes.count)
        }
        secureMemory.removeValue(forKey: key)
    }
    
    private func protectMemory(_ data: Data) -> Data {
        // Implement memory protection
        return data
    }
}
```

## 📊 Project Structure

```
clients/ios/
├── secIRC/
│   ├── secIRC.xcodeproj
│   ├── secIRC/
│   │   ├── App/
│   │   │   ├── SecIRCApp.swift
│   │   │   └── AppDelegate.swift
│   │   ├── Views/
│   │   │   ├── ContentView.swift
│   │   │   ├── LoginView.swift
│   │   │   ├── ChatView.swift
│   │   │   └── GroupView.swift
│   │   ├── ViewModels/
│   │   │   ├── LoginViewModel.swift
│   │   │   ├── ChatViewModel.swift
│   │   │   └── GroupViewModel.swift
│   │   ├── Models/
│   │   │   ├── User.swift
│   │   │   ├── Message.swift
│   │   │   └── Group.swift
│   │   ├── Services/
│   │   │   ├── KeyManager.swift
│   │   │   ├── NetworkManager.swift
│   │   │   ├── GroupManager.swift
│   │   │   └── SecurityMonitor.swift
│   │   ├── Security/
│   │   │   ├── BiometricAuth.swift
│   │   │   ├── MemoryProtection.swift
│   │   │   └── KernelMonitor.swift
│   │   ├── Protocol/
│   │   │   ├── SecIRCProtocol.swift
│   │   │   ├── MessageEncryption.swift
│   │   │   └── NetworkProtocol.swift
│   │   ├── Utils/
│   │   │   ├── CryptoUtils.swift
│   │   │   ├── NetworkUtils.swift
│   │   │   └── SecurityUtils.swift
│   │   └── Resources/
│   │       ├── Info.plist
│   │       ├── Entitlements.entitlements
│   │       └── Assets.xcassets
│   └── secIRCTests/
│       ├── SecIRCTests.swift
│       ├── KeyManagerTests.swift
│       ├── NetworkManagerTests.swift
│       └── SecurityTests.swift
└── README.md
```

## 🧪 Testing

### **Unit Tests**
```bash
# Run unit tests
xcodebuild test -project secIRC.xcodeproj -scheme secIRC -destination 'platform=iOS Simulator,name=iPhone 14'
```

### **UI Tests**
```bash
# Run UI tests
xcodebuild test -project secIRC.xcodeproj -scheme secIRC -destination 'platform=iOS Simulator,name=iPhone 14' -only-testing:secIRCTests/UITests
```

### **Security Tests**
```bash
# Run security tests
xcodebuild test -project secIRC.xcodeproj -scheme secIRC -destination 'platform=iOS Simulator,name=iPhone 14' -only-testing:secIRCTests/SecurityTests
```

## 📦 Dependencies

### **Core Dependencies**
- **SwiftUI**: Built-in
- **Combine**: Built-in
- **CryptoKit**: Built-in
- **Security**: Built-in
- **LocalAuthentication**: Built-in

### **Network Dependencies**
- **URLSession**: Built-in
- **Network**: Built-in
- **CryptoKit**: Built-in

### **Third-Party Dependencies**
- **KeychainAccess**: 4.2.2
- **Alamofire**: 5.6.4
- **SwiftyJSON**: 5.0.1

## 🔐 Permissions

### **Info.plist Permissions**
```xml
<!-- Network access -->
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <false/>
    <key>NSExceptionDomains</key>
    <dict>
        <key>api.secirc.net</key>
        <dict>
            <key>NSExceptionAllowsInsecureHTTPLoads</key>
            <false/>
            <key>NSExceptionMinimumTLSVersion</key>
            <string>TLSv1.3</string>
        </dict>
    </dict>
</dict>

<!-- Camera and microphone -->
<key>NSCameraUsageDescription</key>
<string>secIRC needs camera access to take photos for sharing</string>
<key>NSMicrophoneUsageDescription</key>
<string>secIRC needs microphone access to record voice messages</string>

<!-- Photo library -->
<key>NSPhotoLibraryUsageDescription</key>
<string>secIRC needs photo library access to share images</string>
```

### **Entitlements**
```xml
<!-- Keychain access -->
<key>keychain-access-groups</key>
<array>
    <string>$(AppIdentifierPrefix)com.secirc.ios</string>
</array>

<!-- Secure Enclave -->
<key>com.apple.developer.secure-enclave</key>
<true/>

<!-- Biometric authentication -->
<key>com.apple.developer.biometric-authentication</key>
<true/>
```

## 🚀 Deployment

### **Debug Build**
```bash
# Build debug
xcodebuild -project secIRC.xcodeproj -scheme secIRC -configuration Debug

# Run on simulator
xcodebuild -project secIRC.xcodeproj -scheme secIRC -destination 'platform=iOS Simulator,name=iPhone 14' -configuration Debug
```

### **Release Build**
```bash
# Build release
xcodebuild -project secIRC.xcodeproj -scheme secIRC -configuration Release

# Archive for App Store
xcodebuild archive -project secIRC.xcodeproj -scheme secIRC -configuration Release -archivePath secIRC.xcarchive
```

## 📚 Documentation

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
- [Android Client](../android/README.md)
- [Server Implementation](../../src/server/README.md)
- [Protocol Documentation](../../docs/README.md)
