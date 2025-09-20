# secIRC Android Client

## Overview

The secIRC Android client is a secure, anonymous messaging application that provides end-to-end encrypted communication through a decentralized relay network. Built with modern Android development practices and security-first design principles.

## 🔒 Security Features

- **Hardware Security Module (HSM)** integration with Android Keystore
- **Biometric authentication** for key access
- **End-to-end encryption** with individual message encryption
- **Decentralized group management** with owner-only control
- **Kernel integrity monitoring** for device security
- **Certificate pinning** for network security
- **Memory protection** for sensitive data

## 🏗️ Architecture

### **Core Components**
- **SecIRCProtocol**: Core messaging protocol implementation
- **KeyManager**: Secure key management with Android Keystore
- **NetworkManager**: UDP communication with relay servers
- **GroupManager**: Decentralized group management
- **SecurityMonitor**: Device security and integrity monitoring
- **MessageEncryption**: End-to-end encryption implementation

### **Security Layers**
1. **Hardware Security**: Android Keystore integration
2. **Biometric Authentication**: Fingerprint/Face unlock
3. **Memory Protection**: Secure memory handling
4. **Network Security**: TLS 1.3 with certificate pinning
5. **Kernel Monitoring**: Device integrity verification

## 🚀 Quick Start

### **Prerequisites**
- Android Studio Arctic Fox or later
- Android SDK 21+ (Android 5.0+)
- Java 11 or later
- Kotlin 1.6+

### **Setup**
```bash
# Clone the repository
git clone https://github.com/your-org/secIRC.git
cd secIRC/clients/android

# Open in Android Studio
android-studio .

# Sync project with Gradle files
./gradlew build
```

### **Build**
```bash
# Debug build
./gradlew assembleDebug

# Release build
./gradlew assembleRelease

# Run tests
./gradlew test
```

## 📱 Features

### **Messaging**
- **Anonymous messaging** with hash-based identities
- **Group messaging** with decentralized management
- **File sharing** with end-to-end encryption
- **Voice messages** with secure transmission
- **Message reactions** with encrypted responses

### **Security**
- **Hardware-backed key storage** using Android Keystore
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
```kotlin
// Security configuration
object SecurityConfig {
    const val KEY_ALGORITHM = "RSA"
    const val KEY_SIZE = 2048
    const val ENCRYPTION_ALGORITHM = "AES/GCM/NoPadding"
    const val HASH_ALGORITHM = "SHA-256"
    const val KEY_DERIVATION_ITERATIONS = 100000
    const val BIOMETRIC_AUTHENTICATION_REQUIRED = true
    const val MEMORY_PROTECTION_ENABLED = true
}
```

### **Network Settings**
```kotlin
// Network configuration
object NetworkConfig {
    const val DEFAULT_UDP_PORT = 6667
    const val MAX_PACKET_SIZE = 1400
    const val RELAY_DISCOVERY_INTERVAL = 300000L // 5 minutes
    const val MESSAGE_TTL = 3600000L // 1 hour
    const val CERTIFICATE_PINNING_ENABLED = true
    const val TLS_VERSION = "TLSv1.3"
}
```

## 🛡️ Security Implementation

### **Key Management**
```kotlin
class SecIRCKeyManager(private val context: Context) {
    private val keyStore = KeyStore.getInstance("AndroidKeyStore")
    
    fun generateSecureKeyPair(userPassword: String): KeyPair {
        val keyPairGenerator = KeyPairGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_RSA, "AndroidKeyStore"
        )
        
        val keyGenParameterSpec = KeyGenParameterSpec.Builder(
            "secIRC_private_key",
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT or
            KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
        )
        .setDigests(KeyProperties.DIGEST_SHA256)
        .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_RSA_OAEP)
        .setUserAuthenticationRequired(true)
        .setUserAuthenticationValidityDurationSeconds(300)
        .setInvalidatedByBiometricEnrollment(true)
        .build()
        
        keyPairGenerator.initialize(keyGenParameterSpec)
        return keyPairGenerator.generateKeyPair()
    }
}
```

### **Biometric Authentication**
```kotlin
class BiometricAuth(private val context: Context) {
    fun authenticateUser(): Boolean {
        val biometricManager = BiometricManager.from(context)
        
        return when (biometricManager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_WEAK)) {
            BiometricManager.BIOMETRIC_SUCCESS -> {
                // Start biometric authentication
                startBiometricAuthentication()
                true
            }
            BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE -> {
                // Fallback to PIN/password
                startPasswordAuthentication()
                true
            }
            else -> false
        }
    }
}
```

### **Memory Protection**
```kotlin
class SecureMemoryManager {
    private val secureMemory = mutableMapOf<String, ByteArray>()
    
    fun storeSensitiveData(key: String, data: ByteArray) {
        // Use platform-specific secure memory
        secureMemory[key] = protectMemory(data)
    }
    
    fun clearSensitiveData(key: String) {
        secureMemory[key]?.let { data ->
            // Overwrite memory with random data
            secureWipe(data)
            secureMemory.remove(key)
        }
    }
    
    private fun protectMemory(data: ByteArray): ByteArray {
        // Implement memory protection
        return data
    }
}
```

## 📊 Project Structure

```
clients/android/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/secirc/android/
│   │   │   │   ├── SecIRCApplication.kt
│   │   │   │   ├── ui/
│   │   │   │   │   ├── MainActivity.kt
│   │   │   │   │   ├── LoginActivity.kt
│   │   │   │   │   ├── ChatActivity.kt
│   │   │   │   │   └── GroupActivity.kt
│   │   │   │   ├── security/
│   │   │   │   │   ├── KeyManager.kt
│   │   │   │   │   ├── BiometricAuth.kt
│   │   │   │   │   ├── MemoryProtection.kt
│   │   │   │   │   └── KernelMonitor.kt
│   │   │   │   ├── protocol/
│   │   │   │   │   ├── SecIRCProtocol.kt
│   │   │   │   │   ├── MessageEncryption.kt
│   │   │   │   │   ├── GroupManager.kt
│   │   │   │   │   └── NetworkManager.kt
│   │   │   │   └── utils/
│   │   │   │       ├── CryptoUtils.kt
│   │   │   │       ├── NetworkUtils.kt
│   │   │   │       └── SecurityUtils.kt
│   │   │   ├── res/
│   │   │   │   ├── layout/
│   │   │   │   ├── values/
│   │   │   │   └── drawable/
│   │   │   └── AndroidManifest.xml
│   │   └── test/
│   │       └── java/com/secirc/android/
│   ├── build.gradle
│   └── proguard-rules.pro
├── build.gradle
├── settings.gradle
└── README.md
```

## 🧪 Testing

### **Unit Tests**
```bash
# Run unit tests
./gradlew test

# Run with coverage
./gradlew testDebugUnitTestCoverage
```

### **Instrumented Tests**
```bash
# Run instrumented tests
./gradlew connectedAndroidTest
```

### **Security Tests**
```bash
# Run security tests
./gradlew testSecurity
```

## 📦 Dependencies

### **Core Dependencies**
- **Kotlin**: 1.6.21
- **AndroidX**: Core, AppCompat, Lifecycle
- **Material Design**: 1.6.1
- **Navigation**: 2.5.0
- **Room**: 2.4.2 (for local data)

### **Security Dependencies**
- **Android Keystore**: Built-in
- **Biometric**: 1.1.0
- **Crypto**: Built-in
- **Network Security**: Built-in

### **Network Dependencies**
- **OkHttp**: 4.9.3
- **Retrofit**: 2.9.0
- **Gson**: 2.9.0

## 🔐 Permissions

### **Required Permissions**
```xml
<!-- Network access -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

<!-- Biometric authentication -->
<uses-permission android:name="android.permission.USE_BIOMETRIC" />
<uses-permission android:name="android.permission.USE_FINGERPRINT" />

<!-- File access -->
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />

<!-- Camera and microphone -->
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
```

## 🚀 Deployment

### **Debug Build**
```bash
# Build debug APK
./gradlew assembleDebug

# Install on device
adb install app/build/outputs/apk/debug/app-debug.apk
```

### **Release Build**
```bash
# Build release APK
./gradlew assembleRelease

# Sign APK
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 \
  -keystore secirc-release-key.keystore \
  app/build/outputs/apk/release/app-release-unsigned.apk \
  secirc-release-key
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
- [iOS Client](../ios/README.md)
- [Server Implementation](../../src/server/README.md)
- [Protocol Documentation](../../docs/README.md)
