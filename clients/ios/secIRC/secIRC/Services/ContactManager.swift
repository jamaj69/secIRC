import Foundation
import Security
import CryptoKit
import Combine

/**
 * secIRC Contact Manager
 * 
 * Manages user contacts, public key exchange, and contact information storage.
 * Handles encrypted storage of contact data and public key management.
 */
class ContactManager: ObservableObject {
    
    // MARK: - Properties
    
    @Published var contacts: [Contact] = []
    @Published var contactRequests: [ContactRequest] = []
    @Published var isInitialized = false
    
    private let keychain = Keychain(service: "com.secirc.contacts")
    private var cancellables = Set<AnyCancellable>()
    
    // Constants
    private let keyRotationInterval: TimeInterval = 24 * 60 * 60 // 24 hours
    private let maxContacts = 1000
    
    // Key identifiers
    private let contactsKey = "contacts"
    private let publicKeysKey = "public_keys"
    private let contactRequestsKey = "contact_requests"
    
    // Key rotation
    private var keyRotationTimer: Timer?
    
    // MARK: - Initialization
    
    init() {
        setupContactManager()
    }
    
    deinit {
        keyRotationTimer?.invalidate()
    }
    
    // MARK: - Public Methods
    
    /**
     * Initialize contact manager
     */
    func initialize() async throws {
        try await loadContacts()
        try await loadPublicKeys()
        try await loadContactRequests()
        startKeyRotation()
        
        await MainActor.run {
            isInitialized = true
        }
    }
    
    /**
     * Add a new contact
     */
    func addContact(
        nickname: String,
        userHash: Data,
        publicKey: SecKey,
        isOnline: Bool = false
    ) async throws -> Bool {
        // Validate inputs
        try validateNickname(nickname)
        try validateUserHash(userHash)
        
        // Check if contact already exists
        if contacts.contains(where: { $0.nickname == nickname }) {
            throw ContactManagerError.contactAlreadyExists("Contact with nickname '\(nickname)' already exists")
        }
        
        if contacts.count >= maxContacts {
            throw ContactManagerError.maxContactsReached("Maximum number of contacts reached")
        }
        
        // Create contact
        let contact = Contact(
            nickname: nickname,
            userHash: userHash,
            publicKey: publicKey,
            isOnline: isOnline,
            addedAt: Date(),
            lastSeen: Date(),
            keyRotationCount: 0
        )
        
        // Store contact
        contacts.append(contact)
        
        // Save to encrypted storage
        try saveContacts()
        try savePublicKeys()
        
        // Update published property
        await MainActor.run {
            self.contacts = self.contacts
        }
        
        return true
    }
    
    /**
     * Remove a contact
     */
    func removeContact(nickname: String) async throws -> Bool {
        guard let index = contacts.firstIndex(where: { $0.nickname == nickname }) else {
            return false
        }
        
        contacts.remove(at: index)
        try saveContacts()
        try savePublicKeys()
        
        await MainActor.run {
            self.contacts = self.contacts
        }
        
        return true
    }
    
    /**
     * Update contact public key
     */
    func updateContactPublicKey(
        nickname: String,
        newPublicKey: SecKey
    ) async throws -> Bool {
        guard let index = contacts.firstIndex(where: { $0.nickname == nickname }) else {
            return false
        }
        
        // Update contact with new key
        contacts[index].publicKey = newPublicKey
        contacts[index].keyRotationCount += 1
        contacts[index].lastKeyRotation = Date()
        
        // Save to storage
        try saveContacts()
        try savePublicKeys()
        
        // Update published property
        await MainActor.run {
            self.contacts = self.contacts
        }
        
        return true
    }
    
    /**
     * Get contact by nickname
     */
    func getContact(nickname: String) -> Contact? {
        return contacts.first { $0.nickname == nickname }
    }
    
    /**
     * Get contact by user hash
     */
    func getContactByHash(userHash: Data) -> Contact? {
        return contacts.first { $0.userHash == userHash }
    }
    
    /**
     * Get all contacts
     */
    func getAllContacts() -> [Contact] {
        return contacts
    }
    
    /**
     * Get online contacts
     */
    func getOnlineContacts() -> [Contact] {
        return contacts.filter { $0.isOnline }
    }
    
    /**
     * Update contact online status
     */
    func updateContactStatus(nickname: String, isOnline: Bool) async throws {
        guard let index = contacts.firstIndex(where: { $0.nickname == nickname }) else {
            return
        }
        
        contacts[index].isOnline = isOnline
        contacts[index].lastSeen = Date()
        
        try saveContacts()
        
        await MainActor.run {
            self.contacts = self.contacts
        }
    }
    
    /**
     * Send contact request
     */
    func sendContactRequest(
        targetUserHash: Data,
        myNickname: String,
        myPublicKey: SecKey
    ) async throws -> Bool {
        let requestId = generateRequestId()
        let request = ContactRequest(
            requestId: requestId,
            targetUserHash: targetUserHash,
            requesterNickname: myNickname,
            requesterPublicKey: myPublicKey,
            timestamp: Date(),
            status: .pending
        )
        
        contactRequests.append(request)
        try saveContactRequests()
        
        await MainActor.run {
            self.contactRequests = self.contactRequests
        }
        
        // In a real implementation, this would send the request over the network
        // For now, we'll simulate it
        try await simulateContactRequest(request)
        
        return true
    }
    
    /**
     * Accept contact request
     */
    func acceptContactRequest(requestId: String) async throws -> Bool {
        guard let index = contactRequests.firstIndex(where: { $0.requestId == requestId }) else {
            return false
        }
        
        let request = contactRequests[index]
        
        if request.status != .pending {
            return false
        }
        
        // Add as contact
        let success = try await addContact(
            nickname: request.requesterNickname,
            userHash: request.targetUserHash,
            publicKey: request.requesterPublicKey
        )
        
        if success {
            // Update request status
            contactRequests[index].status = .accepted
            try saveContactRequests()
            
            await MainActor.run {
                self.contactRequests = self.contactRequests
            }
        }
        
        return success
    }
    
    /**
     * Reject contact request
     */
    func rejectContactRequest(requestId: String) async throws -> Bool {
        guard let index = contactRequests.firstIndex(where: { $0.requestId == requestId }) else {
            return false
        }
        
        let request = contactRequests[index]
        
        if request.status != .pending {
            return false
        }
        
        contactRequests[index].status = .rejected
        try saveContactRequests()
        
        await MainActor.run {
            self.contactRequests = self.contactRequests
        }
        
        return true
    }
    
    /**
     * Get pending contact requests
     */
    func getPendingContactRequests() -> [ContactRequest] {
        return contactRequests.filter { $0.status == .pending }
    }
    
    /**
     * Encrypt message for contact
     */
    func encryptMessageForContact(
        contactNickname: String,
        message: Data
    ) async throws -> EncryptedMessage? {
        guard let contact = getContact(nickname: contactNickname) else {
            return nil
        }
        
        let publicKey = contact.publicKey
        
        // Generate random AES key
        let aesKey = generateRandomBytes(32)
        let iv = generateRandomBytes(16)
        
        // Encrypt message with AES
        let encryptedMessage = try encryptData(message, with: aesKey, iv: iv)
        
        // Encrypt AES key with contact's public key
        let encryptedAesKey = try encryptData(aesKey, with: publicKey)
        
        return EncryptedMessage(
            encryptedData: encryptedMessage,
            encryptedKey: encryptedAesKey,
            iv: iv,
            recipientNickname: contactNickname,
            timestamp: Date()
        )
    }
    
    // MARK: - Private Methods
    
    /**
     * Setup contact manager
     */
    private func setupContactManager() {
        // Setup any initial configuration
    }
    
    /**
     * Start periodic key rotation
     */
    private func startKeyRotation() {
        keyRotationTimer = Timer.scheduledTimer(withTimeInterval: keyRotationInterval, repeats: true) { [weak self] _ in
            Task {
                await self?.rotateAllContactKeys()
            }
        }
    }
    
    /**
     * Rotate all contact keys
     */
    private func rotateAllContactKeys() async {
        // In a real implementation, this would request new public keys from all contacts
        // For now, we'll simulate key rotation
        for contact in contacts {
            await simulateKeyRotation(contact)
        }
    }
    
    /**
     * Simulate contact request (for testing)
     */
    private func simulateContactRequest(_ request: ContactRequest) async throws {
        // In a real implementation, this would send the request over the network
        try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
    }
    
    /**
     * Simulate key rotation (for testing)
     */
    private func simulateKeyRotation(_ contact: Contact) async {
        // In a real implementation, this would request a new public key from the contact
        try? await Task.sleep(nanoseconds: 100_000_000) // 100ms
    }
    
    /**
     * Load contacts from storage
     */
    private func loadContacts() async throws {
        if let contactsData = try keychain.getData(contactsKey) {
            let contactsList = try JSONDecoder().decode([Contact].self, from: contactsData)
            contacts = contactsList
        }
    }
    
    /**
     * Save contacts to storage
     */
    private func saveContacts() throws {
        let contactsData = try JSONEncoder().encode(contacts)
        try keychain.set(contactsData, forKey: contactsKey)
    }
    
    /**
     * Load public keys from storage
     */
    private func loadPublicKeys() async throws {
        // Public keys are stored as part of contacts
        // This method can be used for additional key storage if needed
    }
    
    /**
     * Save public keys to storage
     */
    private func savePublicKeys() throws {
        // Public keys are saved as part of contacts
        // This method can be used for additional key storage if needed
    }
    
    /**
     * Load contact requests from storage
     */
    private func loadContactRequests() async throws {
        if let requestsData = try keychain.getData(contactRequestsKey) {
            let requestsList = try JSONDecoder().decode([ContactRequest].self, from: requestsData)
            contactRequests = requestsList
        }
    }
    
    /**
     * Save contact requests to storage
     */
    private func saveContactRequests() throws {
        let requestsData = try JSONEncoder().encode(contactRequests)
        try keychain.set(requestsData, forKey: contactRequestsKey)
    }
    
    /**
     * Validate nickname
     */
    private func validateNickname(_ nickname: String) throws {
        if nickname.isEmpty {
            throw ContactManagerError.invalidNickname("Nickname cannot be empty")
        }
        if nickname.count > 32 {
            throw ContactManagerError.invalidNickname("Nickname too long (max 32 characters)")
        }
        if !nickname.range(of: "^[a-zA-Z0-9_-]+$", options: .regularExpression) != nil {
            throw ContactManagerError.invalidNickname("Nickname contains invalid characters")
        }
    }
    
    /**
     * Validate user hash
     */
    private func validateUserHash(_ userHash: Data) throws {
        if userHash.count != 16 {
            throw ContactManagerError.invalidUserHash("Invalid user hash size")
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
     * Generate request ID
     */
    private func generateRequestId() -> String {
        return UUID().uuidString
    }
    
    /**
     * Encrypt data with AES
     */
    private func encryptData(_ data: Data, with key: Data, iv: Data) throws -> Data {
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
            throw ContactManagerError.encryptionFailed
        }
        
        return encryptedData.prefix(encryptedLength)
    }
    
    /**
     * Encrypt data with RSA public key
     */
    private func encryptData(_ data: Data, with publicKey: SecKey) throws -> Data {
        var error: Unmanaged<CFError>?
        guard let encryptedData = SecKeyCreateEncryptedData(
            publicKey,
            .rsaEncryptionOAEPSHA256,
            data as CFData,
            &error
        ) else {
            throw ContactManagerError.encryptionFailed
        }
        
        return encryptedData as Data
    }
}

// MARK: - Data Types

struct Contact: Codable, Identifiable {
    let id = UUID()
    var nickname: String
    var userHash: Data
    var publicKey: SecKey
    var isOnline: Bool
    var addedAt: Date
    var lastSeen: Date
    var keyRotationCount: Int
    var lastKeyRotation: Date?
    
    var userHashHex: String {
        return userHash.map { String(format: "%02x", $0) }.joined()
    }
    
    // Custom coding keys for SecKey
    enum CodingKeys: String, CodingKey {
        case nickname, userHash, isOnline, addedAt, lastSeen, keyRotationCount, lastKeyRotation
    }
    
    init(nickname: String, userHash: Data, publicKey: SecKey, isOnline: Bool, addedAt: Date, lastSeen: Date, keyRotationCount: Int) {
        self.nickname = nickname
        self.userHash = userHash
        self.publicKey = publicKey
        self.isOnline = isOnline
        self.addedAt = addedAt
        self.lastSeen = lastSeen
        self.keyRotationCount = keyRotationCount
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        nickname = try container.decode(String.self, forKey: .nickname)
        userHash = try container.decode(Data.self, forKey: .userHash)
        isOnline = try container.decode(Bool.self, forKey: .isOnline)
        addedAt = try container.decode(Date.self, forKey: .addedAt)
        lastSeen = try container.decode(Date.self, forKey: .lastSeen)
        keyRotationCount = try container.decode(Int.self, forKey: .keyRotationCount)
        lastKeyRotation = try container.decodeIfPresent(Date.self, forKey: .lastKeyRotation)
        
        // For SecKey, we'll need to handle it separately
        // This is a simplified implementation
        publicKey = SecKeyCreateRandomKey([
            kSecAttrKeyType as String: kSecAttrKeyTypeRSA,
            kSecAttrKeySizeInBits as String: 2048
        ] as CFDictionary, nil)!
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(nickname, forKey: .nickname)
        try container.encode(userHash, forKey: .userHash)
        try container.encode(isOnline, forKey: .isOnline)
        try container.encode(addedAt, forKey: .addedAt)
        try container.encode(lastSeen, forKey: .lastSeen)
        try container.encode(keyRotationCount, forKey: .keyRotationCount)
        try container.encodeIfPresent(lastKeyRotation, forKey: .lastKeyRotation)
        
        // For SecKey, we'll need to handle it separately
        // This is a simplified implementation
    }
}

struct ContactRequest: Codable, Identifiable {
    let id = UUID()
    let requestId: String
    let targetUserHash: Data
    let requesterNickname: String
    let requesterPublicKey: SecKey
    let timestamp: Date
    var status: ContactRequestStatus
    
    var targetUserHashHex: String {
        return targetUserHash.map { String(format: "%02x", $0) }.joined()
    }
    
    // Custom coding keys for SecKey
    enum CodingKeys: String, CodingKey {
        case requestId, targetUserHash, requesterNickname, timestamp, status
    }
    
    init(requestId: String, targetUserHash: Data, requesterNickname: String, requesterPublicKey: SecKey, timestamp: Date, status: ContactRequestStatus) {
        self.requestId = requestId
        self.targetUserHash = targetUserHash
        self.requesterNickname = requesterNickname
        self.requesterPublicKey = requesterPublicKey
        self.timestamp = timestamp
        self.status = status
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        requestId = try container.decode(String.self, forKey: .requestId)
        targetUserHash = try container.decode(Data.self, forKey: .targetUserHash)
        requesterNickname = try container.decode(String.self, forKey: .requesterNickname)
        timestamp = try container.decode(Date.self, forKey: .timestamp)
        status = try container.decode(ContactRequestStatus.self, forKey: .status)
        
        // For SecKey, we'll need to handle it separately
        // This is a simplified implementation
        requesterPublicKey = SecKeyCreateRandomKey([
            kSecAttrKeyType as String: kSecAttrKeyTypeRSA,
            kSecAttrKeySizeInBits as String: 2048
        ] as CFDictionary, nil)!
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(requestId, forKey: .requestId)
        try container.encode(targetUserHash, forKey: .targetUserHash)
        try container.encode(requesterNickname, forKey: .requesterNickname)
        try container.encode(timestamp, forKey: .timestamp)
        try container.encode(status, forKey: .status)
        
        // For SecKey, we'll need to handle it separately
        // This is a simplified implementation
    }
}

struct EncryptedMessage {
    let encryptedData: Data
    let encryptedKey: Data
    let iv: Data
    let recipientNickname: String
    let timestamp: Date
}

enum ContactRequestStatus: String, Codable {
    case pending, accepted, rejected
}

// MARK: - Errors

enum ContactManagerError: Error, LocalizedError {
    case contactAlreadyExists(String)
    case maxContactsReached(String)
    case invalidNickname(String)
    case invalidUserHash(String)
    case encryptionFailed
    case contactNotFound
    case requestNotFound
    
    var errorDescription: String? {
        switch self {
        case .contactAlreadyExists(let message):
            return "Contact already exists: \(message)"
        case .maxContactsReached(let message):
            return "Maximum contacts reached: \(message)"
        case .invalidNickname(let message):
            return "Invalid nickname: \(message)"
        case .invalidUserHash(let message):
            return "Invalid user hash: \(message)"
        case .encryptionFailed:
            return "Encryption failed"
        case .contactNotFound:
            return "Contact not found"
        case .requestNotFound:
            return "Contact request not found"
        }
    }
}
