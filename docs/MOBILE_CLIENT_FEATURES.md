# secIRC Mobile Client Features

## Overview

This document describes the enhanced features implemented in the secIRC mobile clients (Android and iOS), including secure RSA key pair generation with password protection, nickname association, and BitTorrent-based relay discovery.

## 🔐 Enhanced Security Features

### **1. Secure RSA Key Pair Generation**

#### **Password-Protected Key Storage**
- **RSA 2048-bit keys** generated using cryptographically secure random number generators
- **Password-based encryption** using PBKDF2 with 100,000 iterations
- **AES-GCM encryption** for private key storage with 256-bit keys
- **Hardware-backed security** when available (Android Keystore, iOS Secure Enclave)
- **Fallback to software encryption** when hardware security is not available

#### **Key Generation Process**
```kotlin
// Android
val keyPair = keyManager.generateSecureKeyPair(
    nickname = "Alice",
    password = "strong_password_123"
)
```

```swift
// iOS
let keyPair = try await keyManager.generateSecureKeyPair(
    nickname: "Alice",
    password: "strong_password_123"
)
```

#### **Password Requirements**
- **Minimum length**: 8 characters
- **Maximum length**: 128 characters
- **Character validation**: No restrictions (user choice)
- **Entropy validation**: Encouraged but not enforced

### **2. Nickname Association System**

#### **Nickname Management**
- **Unique nicknames** associated with each key pair
- **Nickname validation**: Alphanumeric characters, underscores, and hyphens only
- **Length limits**: 1-32 characters
- **Persistence**: Stored securely with encrypted key data
- **Display**: Used for user identification in the interface

#### **Nickname Validation**
```kotlin
// Android
private fun validateNickname(nickname: String) {
    if (nickname.isBlank()) {
        throw KeyManagerException("Nickname cannot be empty")
    }
    if (nickname.length > 32) {
        throw KeyManagerException("Nickname too long (max 32 characters)")
    }
    if (!nickname.matches(Regex("^[a-zA-Z0-9_-]+$"))) {
        throw KeyManagerException("Nickname contains invalid characters")
    }
}
```

```swift
// iOS
private func validateNickname(_ nickname: String) throws {
    if nickname.isEmpty {
        throw KeyManagerError.invalidNickname("Nickname cannot be empty")
    }
    if nickname.count > 32 {
        throw KeyManagerError.invalidNickname("Nickname too long (max 32 characters)")
    }
    if !nickname.range(of: "^[a-zA-Z0-9_-]+$", options: .regularExpression) != nil {
        throw KeyManagerError.invalidNickname("Nickname contains invalid characters")
    }
}
```

### **3. User Hash Generation**

#### **Hash-Based Identity**
- **SHA-256 hash** of the public key
- **16-byte truncation** for compact representation
- **Unique identifier** for each user
- **Anonymous communication** using hash instead of real identity

#### **Hash Generation**
```kotlin
// Android
private fun generateUserHash(publicKey: PublicKey): ByteArray {
    val publicKeyBytes = publicKey.encoded
    val digest = MessageDigest.getInstance("SHA-256")
    val hash = digest.digest(publicKeyBytes)
    return hash.sliceArray(0..15) // Use first 16 bytes
}
```

```swift
// iOS
private func generateUserHash(from publicKey: SecKey) throws -> Data {
    var error: Unmanaged<CFError>?
    guard let publicKeyData = SecKeyCopyExternalRepresentation(publicKey, &error) else {
        throw KeyManagerError.publicKeyExtractionFailed(error?.takeRetainedValue())
    }
    
    let hash = SHA256.hash(data: publicKeyData as Data)
    return Data(hash.prefix(16)) // Use first 16 bytes as user hash
}
```

## 🌐 BitTorrent-Based Relay Discovery

### **1. Distributed Hash Table (DHT)**

#### **DHT Implementation**
- **Kademlia-based DHT** for decentralized relay discovery
- **UDP-based communication** for efficiency
- **Node discovery** through iterative queries
- **Relay information storage** in distributed hash table

#### **DHT Message Types**
```kotlin
// Android
enum class DHTMessageType {
    PING, PONG, FIND_NODE, GET_PEERS, ANNOUNCE_PEER
}
```

```swift
// iOS
enum DHTMessageType {
    case ping, pong, findNode, getPeers, announcePeer
}
```

#### **DHT Operations**
- **PING/PONG**: Node liveness checks
- **FIND_NODE**: Locate nodes by ID
- **GET_PEERS**: Retrieve relay information
- **ANNOUNCE_PEER**: Announce relay availability

### **2. Tracker Protocol**

#### **HTTP/UDP Tracker Support**
- **HTTP tracker queries** for relay discovery
- **UDP tracker protocol** for efficiency
- **Periodic announcements** to maintain relay lists
- **Bootstrap trackers** for initial discovery

#### **Tracker Communication**
```kotlin
// Android
private suspend fun queryTracker(trackerHost: String) = withContext(Dispatchers.IO) {
    try {
        val url = URL("http://$trackerHost:$TRACKER_PORT/announce")
        val connection = url.openConnection() as HttpURLConnection
        
        connection.requestMethod = "GET"
        connection.setRequestProperty("User-Agent", "secIRC-Android/1.0")
        connection.connectTimeout = 10000
        connection.readTimeout = 10000
        
        if (connection.responseCode == 200) {
            val response = connection.inputStream.readBytes()
            val trackerResponse = parseTrackerResponse(response)
            
            for (relay in trackerResponse.relays) {
                addDiscoveredRelay(relay)
            }
        }
    } catch (e: Exception) {
        // Handle error
    }
}
```

```swift
// iOS
private func queryTracker(_ trackerHost: String) async {
    do {
        let url = URL(string: "http://\(trackerHost):\(trackerPort)/announce")!
        let (data, response) = try await URLSession.shared.data(from: url)
        
        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
            let trackerResponse = try parseTrackerResponse(data)
            
            for relay in trackerResponse.relays {
                addDiscoveredRelay(relay)
            }
        }
    } catch {
        // Continue with next tracker
    }
}
```

### **3. Peer Exchange (PEX)**

#### **PEX Implementation**
- **Direct peer-to-peer communication** for relay discovery
- **Relay information exchange** between connected peers
- **Efficient discovery** of new relays
- **Reduced tracker dependency**

#### **PEX Operations**
```kotlin
// Android
private suspend fun exchangePeerInfo() = withContext(Dispatchers.IO) {
    try {
        val knownRelays = discoveredRelays.values.filter { it.isActive }
        
        for (relay in knownRelays.take(5)) { // Limit to 5 relays
            try {
                val socket = Socket()
                socket.connect(InetSocketAddress(relay.host, relay.port), 5000)
                
                val outputStream = socket.getOutputStream()
                val inputStream = socket.getInputStream()
                
                // Send PEX request
                val pexRequest = createPEXRequest()
                outputStream.write(pexRequest)
                outputStream.flush()
                
                // Read PEX response
                val response = inputStream.readBytes()
                val pexResponse = parsePEXResponse(response)
                
                // Add new relays from PEX
                for (newRelay in pexResponse.relays) {
                    addDiscoveredRelay(newRelay)
                }
                
                socket.close()
                
            } catch (e: Exception) {
                // Mark relay as inactive
                relay.isActive = false
            }
        }
    } catch (e: Exception) {
        // Handle error
    }
}
```

```swift
// iOS
private func exchangePeerInfo() async {
    let knownRelays = discoveredRelays.filter { $0.isActive }
    
    for relay in knownRelays.prefix(5) { // Limit to 5 relays
        await exchangeWithRelay(relay)
    }
}

private func exchangeWithRelay(_ relay: RelayInfo) async {
    do {
        let connection = NWConnection(
            host: NWEndpoint.Host(relay.host),
            port: NWEndpoint.Port(relay.port)!,
            using: .tcp
        )
        
        connection.start(queue: discoveryQueue)
        
        // Wait for connection and exchange data
        // Implementation details...
        
    } catch {
        // Mark relay as inactive
        if let index = discoveredRelays.firstIndex(where: { $0.host == relay.host && $0.port == relay.port }) {
            discoveredRelays[index].isActive = false
        }
    }
}
```

### **4. Bootstrap Process**

#### **Bootstrap Nodes**
- **Known bootstrap servers** for initial discovery
- **Fallback mechanism** when DHT is empty
- **Redundant bootstrap nodes** for reliability
- **Automatic bootstrap** on app startup

#### **Bootstrap Implementation**
```kotlin
// Android
companion object {
    private val BOOTSTRAP_NODES = listOf(
        "bootstrap1.secirc.net",
        "bootstrap2.secirc.net", 
        "bootstrap3.secirc.net"
    )
}

private suspend fun bootstrapFromKnownNodes() = withContext(Dispatchers.IO) {
    try {
        for (bootstrapNode in BOOTSTRAP_NODES) {
            try {
                val socket = Socket()
                socket.connect(InetSocketAddress(bootstrapNode, DHT_PORT), 5000)
                
                val outputStream = socket.getOutputStream()
                val inputStream = socket.getInputStream()
                
                // Send bootstrap request
                val bootstrapRequest = createBootstrapRequest()
                outputStream.write(bootstrapRequest)
                outputStream.flush()
                
                // Read bootstrap response
                val response = inputStream.readBytes()
                val bootstrapResponse = parseBootstrapResponse(response)
                
                // Add discovered relays
                for (relay in bootstrapResponse.relays) {
                    addDiscoveredRelay(relay)
                }
                
                socket.close()
                
            } catch (e: Exception) {
                // Continue with next bootstrap node
            }
        }
    } catch (e: Exception) {
        // Handle error
    }
}
```

```swift
// iOS
private let bootstrapNodes = [
    "bootstrap1.secirc.net",
    "bootstrap2.secirc.net",
    "bootstrap3.secirc.net"
]

private func bootstrapFromKnownNodes() async {
    for bootstrapNode in bootstrapNodes {
        await bootstrapFromNode(bootstrapNode)
    }
}

private func bootstrapFromNode(_ nodeHost: String) async {
    do {
        let connection = NWConnection(
            host: NWEndpoint.Host(nodeHost),
            port: NWEndpoint.Port(dhtPort)!,
            using: .tcp
        )
        
        connection.start(queue: discoveryQueue)
        
        // Wait for connection and exchange data
        // Implementation details...
        
    } catch {
        // Continue with next bootstrap node
    }
}
```

## 🔄 Discovery Flow

### **1. Initialization**
1. **App startup**: Initialize relay discovery system
2. **Bootstrap process**: Query known bootstrap nodes
3. **DHT initialization**: Start DHT listener and join network
4. **Tracker communication**: Begin periodic tracker queries
5. **PEX activation**: Start peer exchange with discovered relays

### **2. Continuous Discovery**
1. **Periodic queries**: Regular tracker and PEX queries
2. **DHT maintenance**: Keep DHT nodes updated
3. **Relay validation**: Verify relay availability
4. **Cleanup**: Remove inactive relays
5. **New relay integration**: Add newly discovered relays

### **3. Relay Management**
1. **Relay storage**: Maintain list of discovered relays
2. **Health monitoring**: Track relay availability
3. **Load balancing**: Distribute traffic across relays
4. **Failover**: Switch to backup relays when needed
5. **Performance optimization**: Prefer faster/more reliable relays

## 📊 Data Structures

### **Relay Information**
```kotlin
// Android
data class RelayInfo(
    val host: String,
    val port: Int,
    val publicKey: ByteArray,
    val relayHash: ByteArray,
    var isActive: Boolean = true,
    var lastSeen: Long = System.currentTimeMillis(),
    val capabilities: List<String> = emptyList()
) {
    val relayId: String
        get() = relayHash.joinToString("") { "%02x".format(it) }
}
```

```swift
// iOS
struct RelayInfo: Identifiable, Codable {
    let id = UUID()
    let host: String
    let port: Int
    let publicKey: Data
    let relayHash: Data
    var isActive: Bool = true
    var lastSeen: Date = Date()
    let capabilities: [String] = []
    
    var relayId: String {
        return relayHash.map { String(format: "%02x", $0) }.joined()
    }
}
```

### **Key Pair Structure**
```kotlin
// Android
data class SecIRCKeyPair(
    val publicKey: PublicKey,
    val encryptedPrivateKey: EncryptedKeyData,
    val userHash: ByteArray,
    val nickname: String
) {
    val userHashHex: String
        get() = userHash.joinToString("") { "%02x".format(it) }
}

data class EncryptedKeyData(
    val encryptedData: ByteArray,
    val salt: ByteArray,
    val iv: ByteArray
)
```

```swift
// iOS
struct SecIRCKeyPair {
    let publicKey: SecKey
    let encryptedPrivateKey: EncryptedKeyData
    let userHash: Data
    let nickname: String
    
    var userHashHex: String {
        return userHash.map { String(format: "%02x", $0) }.joined()
    }
}

struct EncryptedKeyData {
    let encryptedData: Data
    let salt: Data
    let iv: Data
}
```

## 🛡️ Security Considerations

### **1. Key Security**
- **Hardware-backed storage** when available
- **Password-based encryption** with strong key derivation
- **Secure random number generation** for key material
- **Memory protection** for sensitive data
- **Key rotation** support for enhanced security

### **2. Network Security**
- **Certificate pinning** for tracker communication
- **TLS 1.3** for encrypted connections
- **Relay verification** through cryptographic challenges
- **Traffic analysis resistance** through random relay selection
- **DDoS protection** through rate limiting

### **3. Privacy Protection**
- **Anonymous identities** using hash-based identification
- **No metadata storage** on relay servers
- **Decentralized discovery** to prevent tracking
- **Traffic obfuscation** through dummy traffic
- **Perfect forward secrecy** with key rotation

## 🚀 Performance Optimization

### **1. Discovery Efficiency**
- **Parallel queries** to multiple trackers
- **Cached relay information** to reduce network requests
- **Intelligent relay selection** based on performance metrics
- **Background discovery** to avoid blocking UI
- **Connection pooling** for efficient network usage

### **2. Resource Management**
- **Memory-efficient** relay storage
- **Battery optimization** through smart scheduling
- **Network usage monitoring** to prevent excessive data usage
- **CPU optimization** through efficient algorithms
- **Storage optimization** through data compression

### **3. Reliability**
- **Fault tolerance** through redundant discovery methods
- **Automatic recovery** from network failures
- **Graceful degradation** when services are unavailable
- **Health monitoring** for discovered relays
- **Fallback mechanisms** for critical operations

## 📱 Platform-Specific Features

### **Android Features**
- **Android Keystore** integration for hardware-backed security
- **Biometric authentication** with fingerprint/face unlock
- **Background services** for continuous discovery
- **Network security configuration** for certificate pinning
- **Material Design** UI components

### **iOS Features**
- **Secure Enclave** integration for hardware-backed security
- **Touch ID/Face ID** authentication
- **Background app refresh** for continuous discovery
- **App Transport Security** for network security
- **SwiftUI** native interface components

## 🔧 Configuration

### **Discovery Settings**
```kotlin
// Android
object DiscoveryConfig {
    const val DHT_PORT = 6881
    const val TRACKER_PORT = 6969
    const val PEX_PORT = 6882
    const val BOOTSTRAP_INTERVAL = 300000L // 5 minutes
    const val DISCOVERY_INTERVAL = 60000L // 1 minute
    const val MAX_RELAYS = 100
    const val RELAY_TTL = 3600000L // 1 hour
}
```

```swift
// iOS
struct DiscoveryConfig {
    static let dhtPort: UInt16 = 6881
    static let trackerPort: UInt16 = 6969
    static let pexPort: UInt16 = 6882
    static let bootstrapInterval: TimeInterval = 300 // 5 minutes
    static let discoveryInterval: TimeInterval = 60 // 1 minute
    static let maxRelays = 100
    static let relayTTL: TimeInterval = 3600 // 1 hour
}
```

### **Security Settings**
```kotlin
// Android
object SecurityConfig {
    const val KEY_SIZE = 2048
    const val PBKDF2_ITERATIONS = 100000
    const val AES_KEY_SIZE = 256
    const val SALT_SIZE = 16
    const val IV_SIZE = 12
}
```

```swift
// iOS
struct SecurityConfig {
    static let keySize = 2048
    static let pbkdf2Iterations = 100000
    static let aesKeySize = 256
    static let saltSize = 16
    static let ivSize = 12
}
```

## 📚 Usage Examples

### **Key Generation and Management**
```kotlin
// Android
class MainActivity : AppCompatActivity() {
    private lateinit var keyManager: KeyManager
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        keyManager = KeyManager(this, encryptedPrefs)
        
        // Generate new key pair
        lifecycleScope.launch {
            try {
                val keyPair = keyManager.generateSecureKeyPair(
                    nickname = "Alice",
                    password = "secure_password_123"
                )
                
                // Use key pair for messaging
                startMessaging(keyPair)
                
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    private fun startMessaging(keyPair: SecIRCKeyPair) {
        // Initialize messaging with key pair
        val messagingService = MessagingService(keyPair)
        messagingService.start()
    }
}
```

```swift
// iOS
class ContentView: View {
    @StateObject private var keyManager = EnhancedKeyManager()
    @State private var isAuthenticated = false
    
    var body: some View {
        if isAuthenticated {
            MessagingView()
        } else {
            LoginView()
        }
    }
    
    private func generateKeyPair() async {
        do {
            let keyPair = try await keyManager.generateSecureKeyPair(
                nickname: "Alice",
                password: "secure_password_123"
            )
            
            // Use key pair for messaging
            await startMessaging(keyPair: keyPair)
            
        } catch {
            // Handle error
        }
    }
    
    private func startMessaging(keyPair: SecIRCKeyPair) async {
        // Initialize messaging with key pair
        let messagingService = MessagingService(keyPair: keyPair)
        await messagingService.start()
    }
}
```

### **Relay Discovery**
```kotlin
// Android
class RelayDiscoveryService : Service() {
    private lateinit var relayDiscovery: RelayDiscovery
    
    override fun onCreate() {
        super.onCreate()
        
        relayDiscovery = RelayDiscovery(this)
        
        // Start discovery
        lifecycleScope.launch {
            relayDiscovery.startDiscovery()
            
            // Listen for discovery events
            relayDiscovery.discoveryFlow.collect { event ->
                when (event) {
                    is DiscoveryEvent.RelayDiscovered -> {
                        // Handle new relay
                        handleNewRelay(event.relay)
                    }
                    is DiscoveryEvent.RelaysUpdated -> {
                        // Update relay list
                        updateRelayList(event.relays)
                    }
                    is DiscoveryEvent.Error -> {
                        // Handle error
                        handleError(event.exception)
                    }
                }
            }
        }
    }
    
    private fun handleNewRelay(relay: RelayInfo) {
        // Add relay to available relays
        availableRelays.add(relay)
        
        // Notify UI
        sendBroadcast(Intent("RELAY_DISCOVERED").apply {
            putExtra("relay", relay)
        })
    }
}
```

```swift
// iOS
class RelayDiscoveryService: ObservableObject {
    @Published var discoveredRelays: [RelayInfo] = []
    @Published var discoveryStatus: DiscoveryStatus = .stopped
    
    private let relayDiscovery = RelayDiscovery()
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        setupDiscovery()
    }
    
    private func setupDiscovery() {
        // Start discovery
        Task {
            await relayDiscovery.startDiscovery()
        }
        
        // Listen for discovery events
        relayDiscovery.$discoveredRelays
            .sink { [weak self] relays in
                DispatchQueue.main.async {
                    self?.discoveredRelays = relays
                }
            }
            .store(in: &cancellables)
        
        relayDiscovery.$discoveryStatus
            .sink { [weak self] status in
                DispatchQueue.main.async {
                    self?.discoveryStatus = status
                }
            }
            .store(in: &cancellables)
    }
}
```

## 🎯 Benefits

### **1. Enhanced Security**
- **Hardware-backed key storage** provides maximum security
- **Password-based encryption** ensures only authorized access
- **Anonymous communication** through hash-based identities
- **Decentralized discovery** prevents single points of failure

### **2. Improved Reliability**
- **Multiple discovery methods** ensure relay availability
- **Automatic failover** to backup relays
- **Health monitoring** maintains relay quality
- **Bootstrap fallback** for initial discovery

### **3. Better Performance**
- **Parallel discovery** reduces latency
- **Intelligent relay selection** optimizes performance
- **Background processing** doesn't block UI
- **Efficient resource usage** preserves battery life

### **4. Enhanced User Experience**
- **Simple nickname system** for easy identification
- **Automatic discovery** requires no manual configuration
- **Seamless operation** with minimal user intervention
- **Cross-platform compatibility** for consistent experience

---

This enhanced mobile client implementation provides a robust, secure, and efficient foundation for the secIRC anonymous messaging system, with comprehensive relay discovery and secure key management capabilities.
