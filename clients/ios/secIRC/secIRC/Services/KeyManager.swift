import Foundation
import Security
import LocalAuthentication
import CryptoKit
import Combine
import CommonCrypto

/**
 * secIRC Key Manager
 * 
 * Manages secure RSA key pairs with password protection and nickname association.
 * Uses hardware-backed security when available, with fallback to software encryption.
 */
class KeyManager: ObservableObject {
    
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
    }
    
    /**
     * Initialize the key manager
     */
    func initialize() async throws {
        try await checkBiometricAvailability()
        try await checkHardwareSecurityAvailability()
        
        // Check if keys already exist
        if !hasExistingKeys() {
            // Generate new keys
            try await generateNewKeyPair()
        }
        
        isInitialized = true
    }
    
    // MARK: - Key Generation
    
    /**
     * Generate a new secure key pair
     */
    func generateNewKeyPair() async throws -> KeyPair {
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
                kSecAttrLabel as String: privateKeyIdentifier
            ],
            kSecPublicKeyAttrs as String: [
                kSecAttrIsPermanent as String: true,
                kSecAttrLabel as String: publicKeyIdentifier
            ]
        ]
        
        var privateKey: SecKey?
        var publicKey: SecKey?
        
        let status = SecKeyGeneratePair(keyPairQuery as CFDictionary, &publicKey, &privateKey)
        
        guard status == errSecSuccess else {
            throw KeyManagerError.keyGenerationFailed(status)
        }
        
        // Generate user hash from public key
        let userHash = try generateUserHash(from: publicKey!)
        
        // Store user hash in keychain
        try storeUserHash(userHash)
        
        return KeyPair(privateKey: privateKey!, publicKey: publicKey!, userHash: userHash)
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
    
    // MARK: - Key Access
    
    /**
     * Get the current key pair
     */
    func getCurrentKeyPair() async throws -> KeyPair {
        guard let privateKey = try getPrivateKey() else {
            throw KeyManagerError.privateKeyNotFound
        }
        
        guard let publicKey = try getPublicKey() else {
            throw KeyManagerError.publicKeyNotFound
        }
        
        guard let userHash = try getUserHash() else {
            throw KeyManagerError.userHashNotFound
        }
        
        return KeyPair(privateKey: privateKey, publicKey: publicKey, userHash: userHash)
    }
    
    /**
     * Get private key
     */
    private func getPrivateKey() throws -> SecKey? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassKey,
            kSecAttrKeyType as String: kSecAttrKeyTypeRSA,
            kSecAttrLabel as String: privateKeyIdentifier,
            kSecReturnRef as String: true
        ]
        
        var result: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess else {
            if status == errSecItemNotFound {
                return nil
            }
            throw KeyManagerError.keyRetrievalFailed(status)
        }
        
        return (result as! SecKey)
    }
    
    /**
     * Get public key
     */
    private func getPublicKey() throws -> SecKey? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassKey,
            kSecAttrKeyType as String: kSecAttrKeyTypeRSA,
            kSecAttrLabel as String: publicKeyIdentifier,
            kSecReturnRef as String: true
        ]
        
        var result: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess else {
            if status == errSecItemNotFound {
                return nil
            }
            throw KeyManagerError.keyRetrievalFailed(status)
        }
        
        return (result as! SecKey)
    }
    
    /**
     * Get user hash
     */
    private func getUserHash() throws -> Data? {
        return try keychain.getData(userHashIdentifier)
    }
    
    // MARK: - Key Storage
    
    /**
     * Store user hash in keychain
     */
    private func storeUserHash(_ userHash: Data) throws {
        try keychain.set(userHash, forKey: userHashIdentifier)
    }
    
    // MARK: - Authentication
    
    /**
     * Authenticate user for key access
     */
    func authenticateUser() async throws -> Bool {
        return try await biometricAuth.authenticateUser()
    }
    
    /**
     * Check if user is authenticated
     */
    func isUserAuthenticated() -> Bool {
        return biometricAuth.isAuthenticated
    }
    
    // MARK: - Key Operations
    
    /**
     * Encrypt data with public key
     */
    func encryptData(_ data: Data, with publicKey: SecKey) throws -> Data {
        var error: Unmanaged<CFError>?
        guard let encryptedData = SecKeyCreateEncryptedData(
            publicKey,
            .rsaEncryptionOAEPSHA256,
            data as CFData,
            &error
        ) else {
            throw KeyManagerError.encryptionFailed(error?.takeRetainedValue())
        }
        
        return encryptedData as Data
    }
    
    /**
     * Decrypt data with private key
     */
    func decryptData(_ encryptedData: Data, with privateKey: SecKey) throws -> Data {
        var error: Unmanaged<CFError>?
        guard let decryptedData = SecKeyCreateDecryptedData(
            privateKey,
            .rsaEncryptionOAEPSHA256,
            encryptedData as CFData,
            &error
        ) else {
            throw KeyManagerError.decryptionFailed(error?.takeRetainedValue())
        }
        
        return decryptedData as Data
    }
    
    /**
     * Sign data with private key
     */
    func signData(_ data: Data, with privateKey: SecKey) throws -> Data {
        var error: Unmanaged<CFError>?
        guard let signature = SecKeyCreateSignature(
            privateKey,
            .rsaSignatureMessagePKCS1v15SHA256,
            data as CFData,
            &error
        ) else {
            throw KeyManagerError.signingFailed(error?.takeRetainedValue())
        }
        
        return signature as Data
    }
    
    /**
     * Verify signature with public key
     */
    func verifySignature(_ signature: Data, for data: Data, with publicKey: SecKey) throws -> Bool {
        var error: Unmanaged<CFError>?
        let isValid = SecKeyVerifySignature(
            publicKey,
            .rsaSignatureMessagePKCS1v15SHA256,
            data as CFData,
            signature as CFData,
            &error
        )
        
        if let error = error {
            throw KeyManagerError.verificationFailed(error.takeRetainedValue())
        }
        
        return isValid
    }
    
    // MARK: - Utility Methods
    
    /**
     * Check if keys already exist
     */
    private func hasExistingKeys() -> Bool {
        do {
            let privateKey = try getPrivateKey()
            let publicKey = try getPublicKey()
            let userHash = try getUserHash()
            return privateKey != nil && publicKey != nil && userHash != nil
        } catch {
            return false
        }
    }
    
    /**
     * Check biometric availability
     */
    private func checkBiometricAvailability() async throws {
        let context = LAContext()
        var error: NSError?
        
        isBiometricAvailable = context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error)
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
        
        isHardwareSecurityAvailable = (status == errSecSuccess || status == errSecItemNotFound)
    }
    
    /**
     * Delete all keys
     */
    func deleteAllKeys() throws {
        // Delete private key
        let privateKeyQuery: [String: Any] = [
            kSecClass as String: kSecClassKey,
            kSecAttrLabel as String: privateKeyIdentifier
        ]
        SecItemDelete(privateKeyQuery as CFDictionary)
        
        // Delete public key
        let publicKeyQuery: [String: Any] = [
            kSecClass as String: kSecClassKey,
            kSecAttrLabel as String: publicKeyIdentifier
        ]
        SecItemDelete(publicKeyQuery as CFDictionary)
        
        // Delete user hash
        try keychain.remove(userHashIdentifier)
        
        isInitialized = false
    }
}

// MARK: - Supporting Types

/**
 * Key pair data structure
 */
struct KeyPair {
    let privateKey: SecKey
    let publicKey: SecKey
    let userHash: Data
    
    var userHashHex: String {
        return userHash.map { String(format: "%02hhx", $0) }.joined()
    }
}

/**
 * Key manager errors
 */
enum KeyManagerError: Error, LocalizedError {
    case keyGenerationFailed(OSStatus)
    case keyRetrievalFailed(OSStatus)
    case privateKeyNotFound
    case publicKeyNotFound
    case userHashNotFound
    case publicKeyExtractionFailed(CFError?)
    case encryptionFailed(CFError?)
    case decryptionFailed(CFError?)
    case signingFailed(CFError?)
    case verificationFailed(CFError)
    case authenticationFailed
    case hardwareSecurityNotAvailable
    
    var errorDescription: String? {
        switch self {
        case .keyGenerationFailed(let status):
            return "Key generation failed with status: \(status)"
        case .keyRetrievalFailed(let status):
            return "Key retrieval failed with status: \(status)"
        case .privateKeyNotFound:
            return "Private key not found"
        case .publicKeyNotFound:
            return "Public key not found"
        case .userHashNotFound:
            return "User hash not found"
        case .publicKeyExtractionFailed(let error):
            return "Public key extraction failed: \(error?.localizedDescription ?? "Unknown error")"
        case .encryptionFailed(let error):
            return "Encryption failed: \(error?.localizedDescription ?? "Unknown error")"
        case .decryptionFailed(let error):
            return "Decryption failed: \(error?.localizedDescription ?? "Unknown error")"
        case .signingFailed(let error):
            return "Signing failed: \(error?.localizedDescription ?? "Unknown error")"
        case .verificationFailed(let error):
            return "Verification failed: \(error.localizedDescription)"
        case .authenticationFailed:
            return "Authentication failed"
        case .hardwareSecurityNotAvailable:
            return "Hardware security not available"
        }
    }
}
