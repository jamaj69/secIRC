import Foundation
import Security
import CryptoKit
import Combine

/**
 * secIRC Group Manager
 * 
 * Manages local groups with encrypted storage, member invitations, and group messaging.
 * Groups are stored locally and encrypted, with member management and invitation system.
 */
class GroupManager: ObservableObject {
    
    // MARK: - Properties
    
    @Published var groups: [Group] = []
    @Published var groupInvitations: [GroupInvitation] = []
    @Published var isInitialized = false
    
    private let keychain = Keychain(service: "com.secirc.groups")
    private var cancellables = Set<AnyCancellable>()
    
    // Constants
    private let keyRotationInterval: TimeInterval = 24 * 60 * 60 // 24 hours
    private let maxGroups = 100
    private let maxGroupMembers = 50
    
    // Key identifiers
    private let groupsKey = "groups"
    private let groupInvitationsKey = "group_invitations"
    private let groupMessagesKey = "group_messages"
    
    // Key rotation
    private var keyRotationTimer: Timer?
    
    // MARK: - Initialization
    
    init() {
        setupGroupManager()
    }
    
    deinit {
        keyRotationTimer?.invalidate()
    }
    
    // MARK: - Public Methods
    
    /**
     * Initialize group manager
     */
    func initialize() async throws {
        try await loadGroups()
        try await loadGroupInvitations()
        try await loadGroupMessages()
        startKeyRotation()
        
        await MainActor.run {
            isInitialized = true
        }
    }
    
    /**
     * Create a new group
     */
    func createGroup(
        groupName: String,
        description: String,
        ownerNickname: String,
        ownerUserHash: Data,
        ownerPublicKey: SecKey,
        isPrivate: Bool = true
    ) async throws -> Group? {
        // Validate inputs
        try validateGroupName(groupName)
        try validateDescription(description)
        
        if groups.count >= maxGroups {
            throw GroupManagerError.maxGroupsReached("Maximum number of groups reached")
        }
        
        // Generate group ID
        let groupId = generateGroupId()
        
        // Create group
        var group = Group(
            groupId: groupId,
            groupName: groupName,
            description: description,
            ownerNickname: ownerNickname,
            ownerUserHash: ownerUserHash,
            ownerPublicKey: ownerPublicKey,
            isPrivate: isPrivate,
            createdAt: Date(),
            lastActivity: Date(),
            keyRotationCount: 0
        )
        
        // Add owner as first member
        let ownerMember = GroupMember(
            nickname: ownerNickname,
            userHash: ownerUserHash,
            publicKey: ownerPublicKey,
            role: .owner,
            joinedAt: Date(),
            isActive: true
        )
        
        group.members[ownerNickname] = ownerMember
        
        // Store group
        groups.append(group)
        
        // Save to encrypted storage
        try saveGroups()
        
        // Update published property
        await MainActor.run {
            self.groups = self.groups
        }
        
        return group
    }
    
    /**
     * Invite user to group
     */
    func inviteUserToGroup(
        groupId: String,
        targetNickname: String,
        targetUserHash: Data,
        targetPublicKey: SecKey,
        inviterNickname: String
    ) async throws -> Bool {
        guard let groupIndex = groups.firstIndex(where: { $0.groupId == groupId }) else {
            return false
        }
        
        let group = groups[groupIndex]
        
        // Check if user is already a member
        if group.members.keys.contains(targetNickname) {
            throw GroupManagerError.userAlreadyMember("User is already a member of the group")
        }
        
        if group.members.count >= maxGroupMembers {
            throw GroupManagerError.maxMembersReached("Group has reached maximum number of members")
        }
        
        // Create invitation
        let invitationId = generateInvitationId()
        let invitation = GroupInvitation(
            invitationId: invitationId,
            groupId: groupId,
            groupName: group.groupName,
            targetNickname: targetNickname,
            targetUserHash: targetUserHash,
            targetPublicKey: targetPublicKey,
            inviterNickname: inviterNickname,
            timestamp: Date(),
            status: .pending
        )
        
        // Store invitation
        groupInvitations.append(invitation)
        
        // Save to storage
        try saveGroupInvitations()
        
        // Update published property
        await MainActor.run {
            self.groupInvitations = self.groupInvitations
        }
        
        // In a real implementation, this would send the invitation over the network
        try await simulateGroupInvitation(invitation)
        
        return true
    }
    
    /**
     * Accept group invitation
     */
    func acceptGroupInvitation(invitationId: String) async throws -> Bool {
        guard let invitationIndex = groupInvitations.firstIndex(where: { $0.invitationId == invitationId }) else {
            return false
        }
        
        let invitation = groupInvitations[invitationIndex]
        
        if invitation.status != .pending {
            return false
        }
        
        guard let groupIndex = groups.firstIndex(where: { $0.groupId == invitation.groupId }) else {
            return false
        }
        
        // Add user to group
        let newMember = GroupMember(
            nickname: invitation.targetNickname,
            userHash: invitation.targetUserHash,
            publicKey: invitation.targetPublicKey,
            role: .member,
            joinedAt: Date(),
            isActive: true
        )
        
        groups[groupIndex].members[invitation.targetNickname] = newMember
        groups[groupIndex].lastActivity = Date()
        
        // Update invitation status
        groupInvitations[invitationIndex].status = .accepted
        
        // Save to storage
        try saveGroups()
        try saveGroupInvitations()
        
        // Update published properties
        await MainActor.run {
            self.groups = self.groups
            self.groupInvitations = self.groupInvitations
        }
        
        return true
    }
    
    /**
     * Reject group invitation
     */
    func rejectGroupInvitation(invitationId: String) async throws -> Bool {
        guard let invitationIndex = groupInvitations.firstIndex(where: { $0.invitationId == invitationId }) else {
            return false
        }
        
        let invitation = groupInvitations[invitationIndex]
        
        if invitation.status != .pending {
            return false
        }
        
        groupInvitations[invitationIndex].status = .rejected
        
        // Save to storage
        try saveGroupInvitations()
        
        // Update published property
        await MainActor.run {
            self.groupInvitations = self.groupInvitations
        }
        
        return true
    }
    
    /**
     * Remove member from group
     */
    func removeMemberFromGroup(
        groupId: String,
        memberNickname: String,
        removerNickname: String
    ) async throws -> Bool {
        guard let groupIndex = groups.firstIndex(where: { $0.groupId == groupId }) else {
            return false
        }
        
        let group = groups[groupIndex]
        
        // Check permissions
        guard let removerMember = group.members[removerNickname],
              removerMember.role == .owner else {
            throw GroupManagerError.insufficientPermissions("Only group owner can remove members")
        }
        
        // Cannot remove owner
        if memberNickname == group.ownerNickname {
            throw GroupManagerError.cannotRemoveOwner("Cannot remove group owner")
        }
        
        // Remove member
        groups[groupIndex].members.removeValue(forKey: memberNickname)
        groups[groupIndex].lastActivity = Date()
        
        // Save to storage
        try saveGroups()
        
        // Update published property
        await MainActor.run {
            self.groups = self.groups
        }
        
        return true
    }
    
    /**
     * Leave group
     */
    func leaveGroup(groupId: String, memberNickname: String) async throws -> Bool {
        guard let groupIndex = groups.firstIndex(where: { $0.groupId == groupId }) else {
            return false
        }
        
        let group = groups[groupIndex]
        
        // Owner cannot leave group (must transfer ownership or delete group)
        if memberNickname == group.ownerNickname {
            throw GroupManagerError.ownerCannotLeave("Group owner cannot leave group. Transfer ownership or delete group.")
        }
        
        // Remove member
        groups[groupIndex].members.removeValue(forKey: memberNickname)
        groups[groupIndex].lastActivity = Date()
        
        // Save to storage
        try saveGroups()
        
        // Update published property
        await MainActor.run {
            self.groups = self.groups
        }
        
        return true
    }
    
    /**
     * Delete group
     */
    func deleteGroup(groupId: String, ownerNickname: String) async throws -> Bool {
        guard let groupIndex = groups.firstIndex(where: { $0.groupId == groupId }) else {
            return false
        }
        
        let group = groups[groupIndex]
        
        // Only owner can delete group
        if group.ownerNickname != ownerNickname {
            throw GroupManagerError.insufficientPermissions("Only group owner can delete group")
        }
        
        // Remove group
        groups.remove(at: groupIndex)
        
        // Save to storage
        try saveGroups()
        
        // Update published property
        await MainActor.run {
            self.groups = self.groups
        }
        
        return true
    }
    
    /**
     * Send message to group
     */
    func sendGroupMessage(
        groupId: String,
        senderNickname: String,
        messageContent: Data,
        messageType: GroupMessageType = .text
    ) async throws -> GroupMessage? {
        guard let groupIndex = groups.firstIndex(where: { $0.groupId == groupId }) else {
            return nil
        }
        
        let group = groups[groupIndex]
        
        // Check if sender is a member
        guard group.members.keys.contains(senderNickname) else {
            throw GroupManagerError.userNotMember("Sender is not a member of the group")
        }
        
        // Generate message ID
        let messageId = generateMessageId()
        
        // Create message
        var message = GroupMessage(
            messageId: messageId,
            groupId: groupId,
            senderNickname: senderNickname,
            content: messageContent,
            messageType: messageType,
            timestamp: Date(),
            encryptedForMembers: [:]
        )
        
        // Encrypt message for each member
        for (nickname, member) in group.members {
            if member.isActive {
                let encryptedContent = try encryptMessageForMember(messageContent, publicKey: member.publicKey)
                message.encryptedForMembers[nickname] = encryptedContent
            }
        }
        
        // Store message
        if groupMessages[groupId] == nil {
            groupMessages[groupId] = []
        }
        groupMessages[groupId]?.append(message)
        
        groups[groupIndex].lastActivity = Date()
        
        // Save to storage
        try saveGroups()
        try saveGroupMessages()
        
        // Update published property
        await MainActor.run {
            self.groups = self.groups
        }
        
        return message
    }
    
    /**
     * Get group by ID
     */
    func getGroup(groupId: String) -> Group? {
        return groups.first { $0.groupId == groupId }
    }
    
    /**
     * Get groups for user
     */
    func getGroupsForUser(userNickname: String) -> [Group] {
        return groups.filter { $0.members.keys.contains(userNickname) }
    }
    
    /**
     * Get owned groups
     */
    func getOwnedGroups(ownerNickname: String) -> [Group] {
        return groups.filter { $0.ownerNickname == ownerNickname }
    }
    
    /**
     * Get group messages
     */
    func getGroupMessages(groupId: String) -> [GroupMessage] {
        return groupMessages[groupId] ?? []
    }
    
    /**
     * Get pending group invitations
     */
    func getPendingGroupInvitations() -> [GroupInvitation] {
        return groupInvitations.filter { $0.status == .pending }
    }
    
    // MARK: - Private Methods
    
    /**
     * Setup group manager
     */
    private func setupGroupManager() {
        // Setup any initial configuration
    }
    
    /**
     * Start periodic key rotation
     */
    private func startKeyRotation() {
        keyRotationTimer = Timer.scheduledTimer(withTimeInterval: keyRotationInterval, repeats: true) { [weak self] _ in
            Task {
                await self?.rotateAllGroupKeys()
            }
        }
    }
    
    /**
     * Rotate all group keys
     */
    private func rotateAllGroupKeys() async {
        // In a real implementation, this would request new public keys from all group members
        // For now, we'll simulate key rotation
        for group in groups {
            await simulateGroupKeyRotation(group)
        }
    }
    
    /**
     * Simulate group invitation (for testing)
     */
    private func simulateGroupInvitation(_ invitation: GroupInvitation) async throws {
        // In a real implementation, this would send the invitation over the network
        try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
    }
    
    /**
     * Simulate group key rotation (for testing)
     */
    private func simulateGroupKeyRotation(_ group: Group) async {
        // In a real implementation, this would request new public keys from all group members
        try? await Task.sleep(nanoseconds: 100_000_000) // 100ms
    }
    
    /**
     * Load groups from storage
     */
    private func loadGroups() async throws {
        if let groupsData = try keychain.getData(groupsKey) {
            let groupsList = try JSONDecoder().decode([Group].self, from: groupsData)
            groups = groupsList
        }
    }
    
    /**
     * Save groups to storage
     */
    private func saveGroups() throws {
        let groupsData = try JSONEncoder().encode(groups)
        try keychain.set(groupsData, forKey: groupsKey)
    }
    
    /**
     * Load group invitations from storage
     */
    private func loadGroupInvitations() async throws {
        if let invitationsData = try keychain.getData(groupInvitationsKey) {
            let invitationsList = try JSONDecoder().decode([GroupInvitation].self, from: invitationsData)
            groupInvitations = invitationsList
        }
    }
    
    /**
     * Save group invitations to storage
     */
    private func saveGroupInvitations() throws {
        let invitationsData = try JSONEncoder().encode(groupInvitations)
        try keychain.set(invitationsData, forKey: groupInvitationsKey)
    }
    
    /**
     * Load group messages from storage
     */
    private func loadGroupMessages() async throws {
        if let messagesData = try keychain.getData(groupMessagesKey) {
            let messagesMap = try JSONDecoder().decode([String: [GroupMessage]].self, from: messagesData)
            groupMessages = messagesMap
        }
    }
    
    /**
     * Save group messages to storage
     */
    private func saveGroupMessages() throws {
        let messagesData = try JSONEncoder().encode(groupMessages)
        try keychain.set(messagesData, forKey: groupMessagesKey)
    }
    
    /**
     * Encrypt message for group member
     */
    private func encryptMessageForMember(_ message: Data, publicKey: SecKey) throws -> EncryptedGroupMessage {
        // Generate random AES key
        let aesKey = generateRandomBytes(32)
        let iv = generateRandomBytes(16)
        
        // Encrypt message with AES
        let encryptedMessage = try encryptData(message, with: aesKey, iv: iv)
        
        // Encrypt AES key with member's public key
        let encryptedAesKey = try encryptData(aesKey, with: publicKey)
        
        return EncryptedGroupMessage(
            encryptedData: encryptedMessage,
            encryptedKey: encryptedAesKey,
            iv: iv
        )
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
            throw GroupManagerError.encryptionFailed
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
            throw GroupManagerError.encryptionFailed
        }
        
        return encryptedData as Data
    }
    
    /**
     * Validate group name
     */
    private func validateGroupName(_ groupName: String) throws {
        if groupName.isEmpty {
            throw GroupManagerError.invalidGroupName("Group name cannot be empty")
        }
        if groupName.count > 64 {
            throw GroupManagerError.invalidGroupName("Group name too long (max 64 characters)")
        }
    }
    
    /**
     * Validate description
     */
    private func validateDescription(_ description: String) throws {
        if description.count > 256 {
            throw GroupManagerError.invalidDescription("Description too long (max 256 characters)")
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
     * Generate group ID
     */
    private func generateGroupId() -> String {
        return UUID().uuidString
    }
    
    /**
     * Generate invitation ID
     */
    private func generateInvitationId() -> String {
        return UUID().uuidString
    }
    
    /**
     * Generate message ID
     */
    private func generateMessageId() -> String {
        return UUID().uuidString
    }
}

// MARK: - Data Types

struct Group: Codable, Identifiable {
    let id = UUID()
    let groupId: String
    let groupName: String
    let description: String
    let ownerNickname: String
    let ownerUserHash: Data
    let ownerPublicKey: SecKey
    let isPrivate: Bool
    let createdAt: Date
    var lastActivity: Date
    let keyRotationCount: Int
    var members: [String: GroupMember] = [:]
    
    var ownerUserHashHex: String {
        return ownerUserHash.map { String(format: "%02x", $0) }.joined()
    }
    
    // Custom coding keys for SecKey
    enum CodingKeys: String, CodingKey {
        case groupId, groupName, description, ownerNickname, ownerUserHash, isPrivate, createdAt, lastActivity, keyRotationCount, members
    }
    
    init(groupId: String, groupName: String, description: String, ownerNickname: String, ownerUserHash: Data, ownerPublicKey: SecKey, isPrivate: Bool, createdAt: Date, lastActivity: Date, keyRotationCount: Int) {
        self.groupId = groupId
        self.groupName = groupName
        self.description = description
        self.ownerNickname = ownerNickname
        self.ownerUserHash = ownerUserHash
        self.ownerPublicKey = ownerPublicKey
        self.isPrivate = isPrivate
        self.createdAt = createdAt
        self.lastActivity = lastActivity
        self.keyRotationCount = keyRotationCount
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        groupId = try container.decode(String.self, forKey: .groupId)
        groupName = try container.decode(String.self, forKey: .groupName)
        description = try container.decode(String.self, forKey: .description)
        ownerNickname = try container.decode(String.self, forKey: .ownerNickname)
        ownerUserHash = try container.decode(Data.self, forKey: .ownerUserHash)
        isPrivate = try container.decode(Bool.self, forKey: .isPrivate)
        createdAt = try container.decode(Date.self, forKey: .createdAt)
        lastActivity = try container.decode(Date.self, forKey: .lastActivity)
        keyRotationCount = try container.decode(Int.self, forKey: .keyRotationCount)
        members = try container.decode([String: GroupMember].self, forKey: .members)
        
        // For SecKey, we'll need to handle it separately
        // This is a simplified implementation
        ownerPublicKey = SecKeyCreateRandomKey([
            kSecAttrKeyType as String: kSecAttrKeyTypeRSA,
            kSecAttrKeySizeInBits as String: 2048
        ] as CFDictionary, nil)!
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(groupId, forKey: .groupId)
        try container.encode(groupName, forKey: .groupName)
        try container.encode(description, forKey: .description)
        try container.encode(ownerNickname, forKey: .ownerNickname)
        try container.encode(ownerUserHash, forKey: .ownerUserHash)
        try container.encode(isPrivate, forKey: .isPrivate)
        try container.encode(createdAt, forKey: .createdAt)
        try container.encode(lastActivity, forKey: .lastActivity)
        try container.encode(keyRotationCount, forKey: .keyRotationCount)
        try container.encode(members, forKey: .members)
        
        // For SecKey, we'll need to handle it separately
        // This is a simplified implementation
    }
}

struct GroupMember: Codable {
    let nickname: String
    let userHash: Data
    let publicKey: SecKey
    let role: GroupRole
    let joinedAt: Date
    let isActive: Bool
    
    var userHashHex: String {
        return userHash.map { String(format: "%02x", $0) }.joined()
    }
    
    // Custom coding keys for SecKey
    enum CodingKeys: String, CodingKey {
        case nickname, userHash, role, joinedAt, isActive
    }
    
    init(nickname: String, userHash: Data, publicKey: SecKey, role: GroupRole, joinedAt: Date, isActive: Bool) {
        self.nickname = nickname
        self.userHash = userHash
        self.publicKey = publicKey
        self.role = role
        self.joinedAt = joinedAt
        self.isActive = isActive
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        nickname = try container.decode(String.self, forKey: .nickname)
        userHash = try container.decode(Data.self, forKey: .userHash)
        role = try container.decode(GroupRole.self, forKey: .role)
        joinedAt = try container.decode(Date.self, forKey: .joinedAt)
        isActive = try container.decode(Bool.self, forKey: .isActive)
        
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
        try container.encode(role, forKey: .role)
        try container.encode(joinedAt, forKey: .joinedAt)
        try container.encode(isActive, forKey: .isActive)
        
        // For SecKey, we'll need to handle it separately
        // This is a simplified implementation
    }
}

struct GroupInvitation: Codable, Identifiable {
    let id = UUID()
    let invitationId: String
    let groupId: String
    let groupName: String
    let targetNickname: String
    let targetUserHash: Data
    let targetPublicKey: SecKey
    let inviterNickname: String
    let timestamp: Date
    var status: GroupInvitationStatus
    
    var targetUserHashHex: String {
        return targetUserHash.map { String(format: "%02x", $0) }.joined()
    }
    
    // Custom coding keys for SecKey
    enum CodingKeys: String, CodingKey {
        case invitationId, groupId, groupName, targetNickname, targetUserHash, inviterNickname, timestamp, status
    }
    
    init(invitationId: String, groupId: String, groupName: String, targetNickname: String, targetUserHash: Data, targetPublicKey: SecKey, inviterNickname: String, timestamp: Date, status: GroupInvitationStatus) {
        self.invitationId = invitationId
        self.groupId = groupId
        self.groupName = groupName
        self.targetNickname = targetNickname
        self.targetUserHash = targetUserHash
        self.targetPublicKey = targetPublicKey
        self.inviterNickname = inviterNickname
        self.timestamp = timestamp
        self.status = status
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        invitationId = try container.decode(String.self, forKey: .invitationId)
        groupId = try container.decode(String.self, forKey: .groupId)
        groupName = try container.decode(String.self, forKey: .groupName)
        targetNickname = try container.decode(String.self, forKey: .targetNickname)
        targetUserHash = try container.decode(Data.self, forKey: .targetUserHash)
        inviterNickname = try container.decode(String.self, forKey: .inviterNickname)
        timestamp = try container.decode(Date.self, forKey: .timestamp)
        status = try container.decode(GroupInvitationStatus.self, forKey: .status)
        
        // For SecKey, we'll need to handle it separately
        // This is a simplified implementation
        targetPublicKey = SecKeyCreateRandomKey([
            kSecAttrKeyType as String: kSecAttrKeyTypeRSA,
            kSecAttrKeySizeInBits as String: 2048
        ] as CFDictionary, nil)!
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(invitationId, forKey: .invitationId)
        try container.encode(groupId, forKey: .groupId)
        try container.encode(groupName, forKey: .groupName)
        try container.encode(targetNickname, forKey: .targetNickname)
        try container.encode(targetUserHash, forKey: .targetUserHash)
        try container.encode(inviterNickname, forKey: .inviterNickname)
        try container.encode(timestamp, forKey: .timestamp)
        try container.encode(status, forKey: .status)
        
        // For SecKey, we'll need to handle it separately
        // This is a simplified implementation
    }
}

struct GroupMessage: Codable, Identifiable {
    let id = UUID()
    let messageId: String
    let groupId: String
    let senderNickname: String
    let content: Data
    let messageType: GroupMessageType
    let timestamp: Date
    let encryptedForMembers: [String: EncryptedGroupMessage]
}

struct EncryptedGroupMessage: Codable {
    let encryptedData: Data
    let encryptedKey: Data
    let iv: Data
}

enum GroupRole: String, Codable {
    case owner, member
}

enum GroupInvitationStatus: String, Codable {
    case pending, accepted, rejected
}

enum GroupMessageType: String, Codable {
    case text, file, image, voice
}

// MARK: - Errors

enum GroupManagerError: Error, LocalizedError {
    case maxGroupsReached(String)
    case maxMembersReached(String)
    case userAlreadyMember(String)
    case userNotMember(String)
    case insufficientPermissions(String)
    case cannotRemoveOwner(String)
    case ownerCannotLeave(String)
    case invalidGroupName(String)
    case invalidDescription(String)
    case encryptionFailed
    case groupNotFound
    case invitationNotFound
    
    var errorDescription: String? {
        switch self {
        case .maxGroupsReached(let message):
            return "Maximum groups reached: \(message)"
        case .maxMembersReached(let message):
            return "Maximum members reached: \(message)"
        case .userAlreadyMember(let message):
            return "User already member: \(message)"
        case .userNotMember(let message):
            return "User not member: \(message)"
        case .insufficientPermissions(let message):
            return "Insufficient permissions: \(message)"
        case .cannotRemoveOwner(let message):
            return "Cannot remove owner: \(message)"
        case .ownerCannotLeave(let message):
            return "Owner cannot leave: \(message)"
        case .invalidGroupName(let message):
            return "Invalid group name: \(message)"
        case .invalidDescription(let message):
            return "Invalid description: \(message)"
        case .encryptionFailed:
            return "Encryption failed"
        case .groupNotFound:
            return "Group not found"
        case .invitationNotFound:
            return "Group invitation not found"
        }
    }
}
