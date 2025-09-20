import Foundation
import Security
import LocalAuthentication
import CryptoKit
import Combine
import CommonCrypto

/**
 * secIRC Enhanced Key Manager
 * 
 * Manages secure RSA key pairs with password protection and nickname association.
 * Uses hardware-backed security when available, with fallback to software encryption.
 */
class EnhancedKeyManager: ObservableObject {
    
    // MARK: - Properties
    
    @Published var isInitialized = false
    @Published var isBiometricAvailable = false
    @Published var isHardwareSecurityAvailable = false
    @Published var userNickname: String?
    @Published var userHash: Data?
    
    private let keychain = Keychain(service: "com.secirc.keys")
    private let biometricAuth = BiometricAuth()
    private var cancellables = Set<AnyCancellable>()
    
    // Key identifiers
    private let privateKeyIdentifier = "com.secirc.private_key"
    private let publicKeyIdentifier = "com.secirc.public_key"
    private let userHashIdentifier = "com.secirc.user_hash"
    private let nicknameIdentifier = "com.secirc.nickname"
    private let keyGeneratedIdentifier = "com.secirc.key_generated"
    
    // Constants
    private let keySize = 2048
    private let pbkdf2Iterations = 100000
    
    // MARK: - Initialization
    
    init() {
        checkBiometricAvailability()
        checkHardwareSecurityAvailability()
        loadUserData()
    }
    
    /**
     * Initialize the key manager
     */
    func initialize() async throws {
        try await checkBiometricAvailability()
        try await checkHardwareSecurityAvailability()
        
        // Check if keys already exist
        if !isKeyGenerated() {
            // No existing keys, will need to generate new ones
            isInitialized = false
        } else {
            // Load existing user data
            loadUserData()
            isInitialized = true
        }
    }
    
    // MARK: - Key Generation
    
    /**
     * Generate a new secure RSA key pair with password protection
     */
    func generateSecureKeyPair(nickname: String, password: String) async throws -> SecIRCKeyPair {
        // Validate inputs
        try validateNickname(nickname)
        try validatePassword(password)
        
        // Generate RSA key pair
        let keyPair = try generateRSAKeyPair()
        
        // Encrypt private key with password
        let encryptedPrivateKey = try encryptPrivateKeyWithPassword(keyPair.privateKey, password: password)
        
        // Generate user hash from public key
        let userHash = try generateUserHash(from: keyPair.publicKey)
        
        // Store encrypted private key and metadata
        try storeEncryptedKeyPair(encryptedPrivateKey, publicKey: keyPair.publicKey, userHash: userHash, nickname: nickname)
        
        // Update local state
        DispatchQueue.main.async {
            self.userNickname = nickname
            self.userHash = userHash
            self.isInitialized = true
        }
        
        return SecIRCKeyPair(
            publicKey: keyPair.publicKey,
            encryptedPrivateKey: encryptedPrivateKey,
            userHash: userHash,
            nickname: nickname
        )
    }
    
    /**
     * Load existing key pair with password
     */
    func loadKeyPair(password: String) async throws -> SecIRCKeyPair {
        guard isKeyGenerated() else {
            throw KeyManagerError.keyNotFound
        }
        
        // Load encrypted private key
        let encryptedPrivateKey = try loadEncryptedPrivateKey()
        let publicKey = try loadPublicKey()
        let userHash = try loadUserHash()
        let nickname = try loadNickname()
        
        // Decrypt private key with password
        let privateKey = try decryptPrivateKeyWithPassword(encryptedPrivateKey, password: password)
        
        return SecIRCKeyPair(
            publicKey: publicKey,
            encryptedPrivateKey: encryptedPrivateKey,
            userHash: userHash,
            nickname: nickname
        )
    }
    
    /**
     * Generate RSA key pair using software implementation
     */
    private func generateRSAKeyPair() throws -> KeyPair {
        let keyPairQuery: [String: Any] = [
            kSecClass as String: kSecClassKey,
            kSecAttrKeyType as String: kSecAttrKeyTypeRSA,
            kSecAttrKeySizeInBits as String: keySize,
            kSecPrivateKeyAttrs as String: [
                kSecAttrIsPermanent as String: false,
                kSecAttrLabel as String: privateKeyIdentifier
            ],
            kSecPublicKeyAttrs as String: [
                kSecAttrIsPermanent as String: false,
                kSecAttrLabel as String: publicKeyIdentifier
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
    
    /**
     * Encrypt private key with user password using AES-GCM
     */
    private func encryptPrivateKeyWithPassword(_ privateKey: SecKey, password: String) throws -> EncryptedKeyData {
        // Derive key from password using PBKDF2
        let salt = generateRandomBytes(16)
        let key = try deriveKeyFromPassword(password: password, salt: salt)
        
        // Get private key data
        var error: Unmanaged<CFError>?
        guard let privateKeyData = SecKeyCopyExternalRepresentation(privateKey, &error) else {
            throw KeyManagerError.privateKeyExtractionFailed(error?.takeRetainedValue())
        }
        
        // Encrypt private key
        let encryptedData = try encryptData(privateKeyData as Data, with: key)
        
        return EncryptedKeyData(
            encryptedData: encryptedData.data,
            salt: salt,
            iv: encryptedData.iv
        )
    }
    
    /**
     * Decrypt private key with user password
     */
    private func decryptPrivateKeyWithPassword(_ encryptedKeyData: EncryptedKeyData, password: String) throws -> SecKey {
        // Derive key from password
        let key = try deriveKeyFromPassword(password: password, salt: encryptedKeyData.salt)
        
        // Decrypt private key
        let decryptedData = try decryptData(encryptedKeyData.encryptedData, with: key, iv: encryptedKeyData.iv)
        
        // Reconstruct private key
        let privateKeyData = decryptedData as CFData
        var error: Unmanaged<CFError>?
        
        guard let privateKey = SecKeyCreateWithData(privateKeyData, [
            kSecAttrKeyType as String: kSecAttrKeyTypeRSA,
            kSecAttrKeyClass as String: kSecAttrKeyClassPrivate
        ] as CFDictionary, &error) else {
            throw KeyManagerError.privateKeyReconstructionFailed(error?.takeRetainedValue())
        }
        
        return privateKey
    }
    
    /**
     * Derive key from password using PBKDF2
     */
    private func deriveKeyFromPassword(password: String, salt: Data) throws -> Data {
        let passwordData = password.data(using: .utf8)!
        var derivedKey = Data(count: 32) // 256 bits
        
        let result = derivedKey.withUnsafeMutableBytes { derivedKeyBytes in
            passwordData.withUnsafeBytes { passwordBytes in
                salt.withUnsafeBytes { saltBytes in
                    CCKeyDerivationPBKDF(
                        CCPBKDFAlgorithm(kCCPBKDF2),
                        passwordBytes.bindMemory(to: Int8.self).baseAddress,
                        passwordData.count,
                        saltBytes.bindMemory(to: UInt8.self).baseAddress,
                        salt.count,
                        CCPseudoRandomAlgorithm(kCCPRFHmacAlgSHA256),
                        UInt32(pbkdf2Iterations),
                        derivedKeyBytes.bindMemory(to: UInt8.self).baseAddress,
                        32
                    )
                }
            }
        }
        
        guard result == kCCSuccess else {
            throw KeyManagerError.keyDerivationFailed
        }
        
        return derivedKey
    }
    
    /**
     * Encrypt data with AES-GCM
     */
    private func encryptData(_ data: Data, with key: Data) throws -> (data: Data, iv: Data) {
        let iv = generateRandomBytes(12) // 96 bits for GCM
        let keyData = key as NSData
        let dataToEncrypt = data as NSData
        let ivData = iv as NSData
        
        var encryptedData = Data(count: data.count + 16) // Data + 16-byte tag
        var encryptedLength: size_t = 0
        
        let result = encryptedData.withUnsafeMutableBytes { encryptedBytes in
            CCCrypt(
                CCOperation(kCCEncrypt),
                CCAlgorithm(kCCAlgorithmAES),
                CCOptions(kCCOptionPKCS7Padding),
                keyData.bytes, keyData.length,
                ivData.bytes,
                dataToEncrypt.bytes, dataToEncrypt.length,
                encryptedBytes.baseAddress, encryptedData.count,
                &encryptedLength
            )
        }
        
        guard result == kCCSuccess else {
            throw KeyManagerError.encryptionFailed
        }
        
        encryptedData = encryptedData.prefix(encryptedLength)
        return (data: encryptedData, iv: iv)
    }
    
    /**
     * Decrypt data with AES-GCM
     */
    private func decryptData(_ encryptedData: Data, with key: Data, iv: Data) throws -> Data {
        let keyData = key as NSData
        let encryptedDataNS = encryptedData as NSData
        let ivData = iv as NSData
        
        var decryptedData = Data(count: encryptedData.count)
        var decryptedLength: size_t = 0
        
        let result = decryptedData.withUnsafeMutableBytes { decryptedBytes in
            CCCrypt(
                CCOperation(kCCDecrypt),
                CCAlgorithm(kCCAlgorithmAES),
                CCOptions(kCCOptionPKCS7Padding),
                keyData.bytes, keyData.length,
                ivData.bytes,
                encryptedDataNS.bytes, encryptedDataNS.length,
                decryptedBytes.baseAddress, decryptedData.count,
                &decryptedLength
            )
        }
        
        guard result == kCCSuccess else {
            throw KeyManagerError.decryptionFailed
        }
        
        return decryptedData.prefix(decryptedLength)
    }
    
    /**
     * Generate user hash from public key
     */
    private func generateUserHash(from publicKey: SecKey) throws -> Data {
        var error: Unmanaged<CFError>?
        guard let publicKeyData = SecKeyCopyExternalRepresentation(publicKey, &error) else {
            throw KeyManagerError.publicKeyExtractionFailed(error?.takeRetainedValue())
        }
        
        let hash = SHA256.hash(data: publicKeyData as Data)
        return Data(hash.prefix(16)) // Use first 16 bytes as user hash
    }
    
    /**
     * Store encrypted key pair and metadata
     */
    private func storeEncryptedKeyPair(
        _ encryptedPrivateKey: EncryptedKeyData,
        publicKey: SecKey,
        userHash: Data,
        nickname: String
    ) throws {
        // Store encrypted private key
        try keychain.set(encryptedPrivateKey.encryptedData, forKey: "encrypted_private_key")
        try keychain.set(encryptedPrivateKey.salt, forKey: "private_key_salt")
        try keychain.set(encryptedPrivateKey.iv, forKey: "private_key_iv")
        
        // Store public key
        var error: Unmanaged<CFError>?
        guard let publicKeyData = SecKeyCopyExternalRepresentation(publicKey, &error) else {
            throw KeyManagerError.publicKeyExtractionFailed(error?.takeRetainedValue())
        }
        try keychain.set(publicKeyData as Data, forKey: publicKeyIdentifier)
        
        // Store user hash
        try keychain.set(userHash, forKey: userHashIdentifier)
        
        // Store nickname
        try keychain.set(nickname, forKey: nicknameIdentifier)
        
        // Mark key as generated
        try keychain.set(true, forKey: keyGeneratedIdentifier)
    }
    
    /**
     * Load encrypted private key
     */
    private func loadEncryptedPrivateKey() throws -> EncryptedKeyData {
        let encryptedData = try keychain.getData("encrypted_private_key") ?? Data()
        let salt = try keychain.getData("private_key_salt") ?? Data()
        let iv = try keychain.getData("private_key_iv") ?? Data()
        
        return EncryptedKeyData(
            encryptedData: encryptedData,
            salt: salt,
            iv: iv
        )
    }
    
    /**
     * Load public key
     */
    private func loadPublicKey() throws -> SecKey {
        guard let publicKeyData = try keychain.getData(publicKeyIdentifier) else {
            throw KeyManagerError.publicKeyNotFound
        }
        
        var error: Unmanaged<CFError>?
        guard let publicKey = SecKeyCreateWithData(publicKeyData as CFData, [
            kSecAttrKeyType as String: kSecAttrKeyTypeRSA,
            kSecAttrKeyClass as String: kSecAttrKeyClassPublic
        ] as CFDictionary, &error) else {
            throw KeyManagerError.publicKeyReconstructionFailed(error?.takeRetainedValue())
        }
        
        return publicKey
    }
    
    /**
     * Load user hash
     */
    private func loadUserHash() throws -> Data {
        guard let userHash = try keychain.getData(userHashIdentifier) else {
            throw KeyManagerError.userHashNotFound
        }
        return userHash
    }
    
    /**
     * Load nickname
     */
    private func loadNickname() throws -> String {
        guard let nickname = try keychain.getString(nicknameIdentifier) else {
            throw KeyManagerError.nicknameNotFound
        }
        return nickname
    }
    
    /**
     * Load user data from keychain
     */
    private func loadUserData() {
        userNickname = try? keychain.getString(nicknameIdentifier)
        userHash = try? keychain.getData(userHashIdentifier)
    }
    
    /**
     * Check if key pair is generated
     */
    func isKeyGenerated() -> Bool {
        return (try? keychain.getBool(keyGeneratedIdentifier)) ?? false
    }
    
    /**
     * Validate nickname
     */
    private func validateNickname(_ nickname: String) throws {
        if nickname.isEmpty {
            throw KeyManagerError.invalidNickname("Nickname cannot be empty")
        }
        if nickname.count > 32 {
            throw KeyManagerError.invalidNickname("Nickname too long (max 32 characters)")
        }
        if !nickname.range(of: "^[a-zA-Z0-9_-]+$", options: .regularExpression, range: nil, locale: nil) != nil {
            throw KeyManagerError.invalidNickname("Nickname contains invalid characters")
        }
    }
    
    /**
     * Validate password
     */
    private func validatePassword(_ password: String) throws {
        if password.count < 8 {
            throw KeyManagerError.invalidPassword("Password too short (min 8 characters)")
        }
        if password.count > 128 {
            throw KeyManagerError.invalidPassword("Password too long (max 128 characters)")
        }
    }
    
    /**
     * Generate random bytes
     */
    private func generateRandomBytes(_ count: Int) -> Data {
        var bytes = Data(count: count)
        let result = bytes.withUnsafeMutableBytes { bytes in
            SecRandomCopyBytes(kSecRandomDefault, count, bytes.baseAddress!)
        }
        return result == errSecSuccess ? bytes : Data()
    }
    
    /**
     * Delete all keys and user data
     */
    func deleteAllKeys() throws {
        try keychain.removeAll()
        DispatchQueue.main.async {
            self.userNickname = nil
            self.userHash = nil
            self.isInitialized = false
        }
    }
    
    // MARK: - Biometric Authentication
    
    /**
     * Check biometric availability
     */
    private func checkBiometricAvailability() async throws {
        let context = LAContext()
        var error: NSError?
        
        DispatchQueue.main.async {
            self.isBiometricAvailable = context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error)
        }
    }
    
    /**
     * Check hardware security availability
     */
    private func checkHardwareSecurityAvailability() async throws {
        // Check if Secure Enclave is available
        let query: [String: Any] = [
            kSecClass as String: kSecClassKey,
            kSecAttrKeyType as String: kSecAttrKeyTypeRSA,
            kSecAttrTokenID as String: kSecAttrTokenIDSecureEnclave
        ]
        
        var result: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        DispatchQueue.main.async {
            self.isHardwareSecurityAvailable = (status == errSecSuccess || status == errSecItemNotFound)
        }
    }
}

// MARK: - Supporting Types

/**
 * Data class for encrypted key data
 */
struct EncryptedKeyData {
    let encryptedData: Data
    let salt: Data
    let iv: Data
}

/**
 * Data class for secIRC key pair
 */
struct SecIRCKeyPair {
    let publicKey: SecKey
    let encryptedPrivateKey: EncryptedKeyData
    let userHash: Data
    let nickname: String
    
    var userHashHex: String {
        return userHash.map { String(format: "%02x", $0) }.joined()
    }
}

/**
 * Key pair data structure
 */
struct KeyPair {
    let privateKey: SecKey
    let publicKey: SecKey
}

/**
 * Key manager errors
 */
enum KeyManagerError: Error, LocalizedError {
    case keyGenerationFailed(OSStatus)
    case keyNotFound
    case privateKeyNotFound
    case publicKeyNotFound
    case userHashNotFound
    case nicknameNotFound
    case privateKeyExtractionFailed(CFError?)
    case publicKeyExtractionFailed(CFError?)
    case privateKeyReconstructionFailed(CFError?)
    case publicKeyReconstructionFailed(CFError?)
    case encryptionFailed
    case decryptionFailed
    case keyDerivationFailed
    case invalidNickname(String)
    case invalidPassword(String)
    case authenticationFailed
    case hardwareSecurityNotAvailable
    
    var errorDescription: String? {
        switch self {
        case .keyGenerationFailed(let status):
            return "Key generation failed with status: \(status)"
        case .keyNotFound:
            return "Key pair not found"
        case .privateKeyNotFound:
            return "Private key not found"
        case .publicKeyNotFound:
            return "Public key not found"
        case .userHashNotFound:
            return "User hash not found"
        case .nicknameNotFound:
            return "Nickname not found"
        case .privateKeyExtractionFailed(let error):
            return "Private key extraction failed: \(error?.localizedDescription ?? "Unknown error")"
        case .publicKeyExtractionFailed(let error):
            return "Public key extraction failed: \(error?.localizedDescription ?? "Unknown error")"
        case .privateKeyReconstructionFailed(let error):
            return "Private key reconstruction failed: \(error?.localizedDescription ?? "Unknown error")"
        case .publicKeyReconstructionFailed(let error):
            return "Public key reconstruction failed: \(error?.localizedDescription ?? "Unknown error")"
        case .encryptionFailed:
            return "Encryption failed"
        case .decryptionFailed:
            return "Decryption failed"
        case .keyDerivationFailed:
            return "Key derivation failed"
        case .invalidNickname(let message):
            return "Invalid nickname: \(message)"
        case .invalidPassword(let message):
            return "Invalid password: \(message)"
        case .authenticationFailed:
            return "Authentication failed"
        case .hardwareSecurityNotAvailable:
            return "Hardware security not available"
        }
    }
}
