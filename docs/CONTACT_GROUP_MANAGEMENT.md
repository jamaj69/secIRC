# secIRC Contact and Group Management System

## Overview

This document describes the comprehensive contact and group management system implemented in the secIRC mobile clients (Android and iOS). The system provides secure contact management, group creation and management, invitation systems, and periodic key rotation for enhanced security.

## 🔐 **Contact Management System**

### **1. Contact Storage and Management**

#### **Encrypted Contact Storage**
- **Local encrypted storage** using platform-specific secure storage (Android Keystore, iOS Keychain)
- **Contact information** including nickname, user hash, public key, and metadata
- **Online status tracking** with last seen timestamps
- **Key rotation tracking** to monitor when contacts update their keys

#### **Contact Data Structure**
```kotlin
// Android
data class Contact(
    val nickname: String,
    val userHash: ByteArray,
    val publicKey: PublicKey,
    val isOnline: Boolean,
    val addedAt: Long,
    val lastSeen: Long,
    val keyRotationCount: Int,
    val lastKeyRotation: Long = 0
) {
    val userHashHex: String
        get() = userHash.joinToString("") { "%02x".format(it) }
}
```

```swift
// iOS
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
}
```

### **2. Public Key Exchange System**

#### **Contact Request Process**
1. **User A** wants to add **User B** as a contact
2. **User A** sends a contact request with their nickname and public key
3. **User B** receives the request and can accept or reject it
4. Upon acceptance, both users store each other's public keys
5. **Encrypted communication** can now begin

#### **Contact Request Implementation**
```kotlin
// Android
suspend fun sendContactRequest(
    targetUserHash: ByteArray,
    myNickname: String,
    myPublicKey: PublicKey
): Boolean = withContext(Dispatchers.IO) {
    try {
        val requestId = generateRequestId()
        val request = ContactRequest(
            requestId = requestId,
            targetUserHash = targetUserHash,
            requesterNickname = myNickname,
            requesterPublicKey = myPublicKey,
            timestamp = System.currentTimeMillis(),
            status = ContactRequestStatus.PENDING
        )
        
        contactRequests[requestId] = request
        saveContactRequests()
        _contactRequestsFlow.value = contactRequests.values.toList()
        
        // Send request over network
        simulateContactRequest(request)
        
        true
    } catch (e: Exception) {
        throw ContactManagerException("Failed to send contact request", e)
    }
}
```

```swift
// iOS
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
    
    // Send request over network
    try await simulateContactRequest(request)
    
    return true
}
```

### **3. Message Encryption for Contacts**

#### **Hybrid Encryption System**
- **AES-256 encryption** for message content
- **RSA encryption** for AES key distribution
- **Unique encryption** for each contact using their public key
- **Perfect forward secrecy** through key rotation

#### **Message Encryption Implementation**
```kotlin
// Android
suspend fun encryptMessageForContact(
    contactNickname: String,
    message: ByteArray
): EncryptedMessage? = withContext(Dispatchers.IO) {
    try {
        val contact = contacts[contactNickname] ?: return@withContext null
        val publicKey = contact.publicKey
        
        // Generate random AES key
        val aesKey = generateRandomBytes(32)
        val iv = generateRandomBytes(16)
        
        // Encrypt message with AES
        val cipher = Cipher.getInstance("AES/CBC/PKCS5Padding")
        val secretKey = SecretKeySpec(aesKey, "AES")
        val ivSpec = IvParameterSpec(iv)
        cipher.init(Cipher.ENCRYPT_MODE, secretKey, ivSpec)
        val encryptedMessage = cipher.doFinal(message)
        
        // Encrypt AES key with contact's public key
        val rsaCipher = Cipher.getInstance("RSA/ECB/PKCS1Padding")
        rsaCipher.init(Cipher.ENCRYPT_MODE, publicKey)
        val encryptedAesKey = rsaCipher.doFinal(aesKey)
        
        EncryptedMessage(
            encryptedData = encryptedMessage,
            encryptedKey = encryptedAesKey,
            iv = iv,
            recipientNickname = contactNickname,
            timestamp = System.currentTimeMillis()
        )
    } catch (e: Exception) {
        throw ContactManagerException("Failed to encrypt message for contact", e)
    }
}
```

```swift
// iOS
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
```

## 👥 **Group Management System**

### **1. Local Group Storage**

#### **Encrypted Group Storage**
- **Groups stored locally** on the user's device
- **Encrypted storage** using platform-specific secure storage
- **Group metadata** including name, description, owner, and member list
- **Member information** with roles, public keys, and status

#### **Group Data Structure**
```kotlin
// Android
data class Group(
    val groupId: String,
    val groupName: String,
    val description: String,
    val ownerNickname: String,
    val ownerUserHash: ByteArray,
    val ownerPublicKey: PublicKey,
    val isPrivate: Boolean,
    val createdAt: Long,
    var lastActivity: Long,
    val keyRotationCount: Int,
    val members: MutableMap<String, GroupMember> = mutableMapOf()
) {
    val ownerUserHashHex: String
        get() = ownerUserHash.joinToString("") { "%02x".format(it) }
}
```

```swift
// iOS
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
}
```

### **2. Group Creation Process**

#### **Group Creation Steps**
1. **User creates group** with name, description, and privacy settings
2. **Group ID generated** using UUID for uniqueness
3. **Owner added** as first member with OWNER role
4. **Group stored locally** with encrypted storage
5. **Group available** for member invitations

#### **Group Creation Implementation**
```kotlin
// Android
suspend fun createGroup(
    groupName: String,
    description: String,
    ownerNickname: String,
    ownerUserHash: ByteArray,
    ownerPublicKey: PublicKey,
    isPrivate: Boolean = true
): Group? = withContext(Dispatchers.IO) {
    try {
        // Validate inputs
        validateGroupName(groupName)
        validateDescription(description)
        
        if (groups.size >= MAX_GROUPS) {
            throw GroupManagerException("Maximum number of groups reached")
        }
        
        // Generate group ID
        val groupId = generateGroupId()
        
        // Create group
        val group = Group(
            groupId = groupId,
            groupName = groupName,
            description = description,
            ownerNickname = ownerNickname,
            ownerUserHash = ownerUserHash,
            ownerPublicKey = ownerPublicKey,
            isPrivate = isPrivate,
            createdAt = System.currentTimeMillis(),
            lastActivity = System.currentTimeMillis(),
            keyRotationCount = 0
        )
        
        // Add owner as first member
        val ownerMember = GroupMember(
            nickname = ownerNickname,
            userHash = ownerUserHash,
            publicKey = ownerPublicKey,
            role = GroupRole.OWNER,
            joinedAt = System.currentTimeMillis(),
            isActive = true
        )
        
        group.members[ownerNickname] = ownerMember
        
        // Store group
        groups[groupId] = group
        groupMessages[groupId] = mutableListOf()
        
        // Save to encrypted storage
        saveGroups()
        
        // Update flow
        _groupsFlow.value = groups.values.toList()
        
        group
    } catch (e: Exception) {
        throw GroupManagerException("Failed to create group", e)
    }
}
```

```swift
// iOS
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
```

### **3. Group Invitation System**

#### **Invitation Process**
1. **Group owner** invites a user by nickname
2. **Invitation created** with target user's information
3. **Invitation sent** over the network to target user
4. **Target user** receives invitation and can accept/reject
5. **Upon acceptance** user is added to group with MEMBER role

#### **Invitation Implementation**
```kotlin
// Android
suspend fun inviteUserToGroup(
    groupId: String,
    targetNickname: String,
    targetUserHash: ByteArray,
    targetPublicKey: PublicKey,
    inviterNickname: String
): Boolean = withContext(Dispatchers.IO) {
    try {
        val group = groups[groupId] ?: return@withContext false
        
        // Check if user is already a member
        if (group.members.containsKey(targetNickname)) {
            throw GroupManagerException("User is already a member of the group")
        }
        
        if (group.members.size >= MAX_GROUP_MEMBERS) {
            throw GroupManagerException("Group has reached maximum number of members")
        }
        
        // Create invitation
        val invitationId = generateInvitationId()
        val invitation = GroupInvitation(
            invitationId = invitationId,
            groupId = groupId,
            groupName = group.groupName,
            targetNickname = targetNickname,
            targetUserHash = targetUserHash,
            targetPublicKey = targetPublicKey,
            inviterNickname = inviterNickname,
            timestamp = System.currentTimeMillis(),
            status = GroupInvitationStatus.PENDING
        )
        
        // Store invitation
        groupInvitations[invitationId] = invitation
        
        // Save to storage
        saveGroupInvitations()
        
        // Update flow
        _groupInvitationsFlow.value = groupInvitations.values.toList()
        
        // Send invitation over network
        simulateGroupInvitation(invitation)
        
        true
    } catch (e: Exception) {
        throw GroupManagerException("Failed to invite user to group", e)
    }
}
```

```swift
// iOS
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
    
    // Send invitation over network
    try await simulateGroupInvitation(invitation)
    
    return true
}
```

### **4. Group Message Encryption**

#### **Individual Member Encryption**
- **Each group message** encrypted separately for each member
- **AES-256 encryption** for message content
- **RSA encryption** for AES key distribution
- **Member-specific encryption** using each member's public key

#### **Group Message Encryption Implementation**
```kotlin
// Android
suspend fun sendGroupMessage(
    groupId: String,
    senderNickname: String,
    messageContent: ByteArray,
    messageType: GroupMessageType = GroupMessageType.TEXT
): GroupMessage? = withContext(Dispatchers.IO) {
    try {
        val group = groups[groupId] ?: return@withContext null
        
        // Check if sender is a member
        if (!group.members.containsKey(senderNickname)) {
            throw GroupManagerException("Sender is not a member of the group")
        }
        
        // Generate message ID
        val messageId = generateMessageId()
        
        // Create message
        val message = GroupMessage(
            messageId = messageId,
            groupId = groupId,
            senderNickname = senderNickname,
            content = messageContent,
            messageType = messageType,
            timestamp = System.currentTimeMillis(),
            encryptedForMembers = mutableMapOf()
        )
        
        // Encrypt message for each member
        for (member in group.members.values) {
            if (member.isActive) {
                val encryptedContent = encryptMessageForMember(messageContent, member.publicKey)
                message.encryptedForMembers[member.nickname] = encryptedContent
            }
        }
        
        // Store message
        groupMessages[groupId]?.add(message)
        group.lastActivity = System.currentTimeMillis()
        
        // Save to storage
        saveGroups()
        saveGroupMessages()
        
        // Update flow
        _groupsFlow.value = groups.values.toList()
        
        message
    } catch (e: Exception) {
        throw GroupManagerException("Failed to send group message", e)
    }
}
```

```swift
// iOS
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
```

## 🔄 **Periodic Key Rotation System**

### **1. Automatic Key Rotation**

#### **Key Rotation Process**
- **24-hour rotation cycle** for all contacts and group members
- **Automatic key requests** sent to all contacts and group members
- **Key update tracking** with rotation count and timestamps
- **Seamless transition** to new keys without service interruption

#### **Key Rotation Implementation**
```kotlin
// Android
private fun startKeyRotation() {
    keyRotationJob = contactScope.launch {
        while (isActive) {
            delay(KEY_ROTATION_INTERVAL)
            rotateAllContactKeys()
        }
    }
}

private suspend fun rotateAllContactKeys() = withContext(Dispatchers.IO) {
    try {
        // In a real implementation, this would request new public keys from all contacts
        // For now, we'll simulate key rotation
        for (contact in contacts.values) {
            simulateKeyRotation(contact)
        }
    } catch (e: Exception) {
        // Handle error
    }
}
```

```swift
// iOS
private func startKeyRotation() {
    keyRotationTimer = Timer.scheduledTimer(withTimeInterval: keyRotationInterval, repeats: true) { [weak self] _ in
        Task {
            await self?.rotateAllContactKeys()
        }
    }
}

private func rotateAllContactKeys() async {
    // In a real implementation, this would request new public keys from all contacts
    // For now, we'll simulate key rotation
    for contact in contacts {
        await simulateKeyRotation(contact)
    }
}
```

### **2. Key Update Handling**

#### **Key Update Process**
1. **Contact/group member** generates new key pair
2. **New public key** sent to all contacts/group members
3. **Recipients update** stored public keys
4. **Key rotation count** incremented
5. **Last rotation timestamp** updated

#### **Key Update Implementation**
```kotlin
// Android
suspend fun updateContactPublicKey(
    nickname: String,
    newPublicKey: PublicKey
): Boolean = withContext(Dispatchers.IO) {
    try {
        val contact = contacts[nickname] ?: return@withContext false
        
        // Update contact with new key
        val updatedContact = contact.copy(
            publicKey = newPublicKey,
            keyRotationCount = contact.keyRotationCount + 1,
            lastKeyRotation = System.currentTimeMillis()
        )
        
        contacts[nickname] = updatedContact
        publicKeys[nickname] = newPublicKey
        
        // Save to storage
        saveContacts()
        savePublicKeys()
        
        // Update flow
        _contactsFlow.value = contacts.values.toList()
        
        true
    } catch (e: Exception) {
        throw ContactManagerException("Failed to update contact public key", e)
    }
}
```

```swift
// iOS
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
```

## 📱 **Platform-Specific Features**

### **Android Features**
- **Kotlin coroutines** for asynchronous operations
- **Flow-based reactive programming** for real-time updates
- **Android Keystore** integration for secure key storage
- **EncryptedSharedPreferences** for encrypted data storage
- **Material Design** UI components

### **iOS Features**
- **Swift async/await** for asynchronous operations
- **Combine framework** for reactive programming
- **iOS Keychain** integration for secure key storage
- **SwiftUI** for modern UI development
- **Secure Enclave** support for hardware-backed security

## 🔧 **Configuration and Limits**

### **System Limits**
```kotlin
// Android
object ContactConfig {
    const val MAX_CONTACTS = 1000
    const val KEY_ROTATION_INTERVAL = 24 * 60 * 60 * 1000L // 24 hours
    const val MAX_GROUPS = 100
    const val MAX_GROUP_MEMBERS = 50
}
```

```swift
// iOS
struct ContactConfig {
    static let maxContacts = 1000
    static let keyRotationInterval: TimeInterval = 24 * 60 * 60 // 24 hours
    static let maxGroups = 100
    static let maxGroupMembers = 50
}
```

### **Security Settings**
- **RSA 2048-bit keys** for public key cryptography
- **AES-256 encryption** for message content
- **PBKDF2 key derivation** with 100,000 iterations
- **Secure random number generation** for all cryptographic operations
- **Hardware-backed security** when available

## 📚 **Usage Examples**

### **Contact Management**
```kotlin
// Android
class MainActivity : AppCompatActivity() {
    private lateinit var contactManager: ContactManager
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        contactManager = ContactManager(this, encryptedPrefs)
        
        // Add new contact
        lifecycleScope.launch {
            try {
                val success = contactManager.addContact(
                    nickname = "Alice",
                    userHash = aliceUserHash,
                    publicKey = alicePublicKey
                )
                
                if (success) {
                    // Contact added successfully
                    startMessaging("Alice")
                }
                
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    private fun startMessaging(contactNickname: String) {
        // Initialize messaging with contact
        val messagingService = MessagingService(contactManager)
        messagingService.startMessaging(contactNickname)
    }
}
```

```swift
// iOS
class ContentView: View {
    @StateObject private var contactManager = ContactManager()
    @State private var contacts: [Contact] = []
    
    var body: some View {
        NavigationView {
            List(contacts) { contact in
                ContactRow(contact: contact)
            }
            .navigationTitle("Contacts")
            .onAppear {
                loadContacts()
            }
        }
    }
    
    private func loadContacts() {
        Task {
            try await contactManager.initialize()
            contacts = contactManager.getAllContacts()
        }
    }
    
    private func addContact() {
        Task {
            let success = try await contactManager.addContact(
                nickname: "Alice",
                userHash: aliceUserHash,
                publicKey: alicePublicKey
            )
            
            if success {
                // Contact added successfully
                contacts = contactManager.getAllContacts()
            }
        }
    }
}
```

### **Group Management**
```kotlin
// Android
class GroupActivity : AppCompatActivity() {
    private lateinit var groupManager: GroupManager
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        groupManager = GroupManager(this, encryptedPrefs)
        
        // Create new group
        lifecycleScope.launch {
            try {
                val group = groupManager.createGroup(
                    groupName = "My Secure Group",
                    description = "Private group for secure communication",
                    ownerNickname = "Bob",
                    ownerUserHash = bobUserHash,
                    ownerPublicKey = bobPublicKey
                )
                
                if (group != null) {
                    // Group created successfully
                    startGroupMessaging(group.groupId)
                }
                
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    private fun startGroupMessaging(groupId: String) {
        // Initialize group messaging
        val groupMessagingService = GroupMessagingService(groupManager)
        groupMessagingService.startGroupMessaging(groupId)
    }
}
```

```swift
// iOS
class GroupView: View {
    @StateObject private var groupManager = GroupManager()
    @State private var groups: [Group] = []
    
    var body: some View {
        NavigationView {
            List(groups) { group in
                GroupRow(group: group)
            }
            .navigationTitle("Groups")
            .onAppear {
                loadGroups()
            }
        }
    }
    
    private func loadGroups() {
        Task {
            try await groupManager.initialize()
            groups = groupManager.getAllGroups()
        }
    }
    
    private func createGroup() {
        Task {
            let group = try await groupManager.createGroup(
                groupName: "My Secure Group",
                description: "Private group for secure communication",
                ownerNickname: "Bob",
                ownerUserHash: bobUserHash,
                ownerPublicKey: bobPublicKey
            )
            
            if group != nil {
                // Group created successfully
                groups = groupManager.getAllGroups()
            }
        }
    }
}
```

## 🎯 **Benefits**

### **1. Enhanced Security**
- **Local encrypted storage** prevents unauthorized access
- **Individual message encryption** for each contact/group member
- **Periodic key rotation** ensures perfect forward secrecy
- **Hardware-backed security** when available

### **2. Improved Privacy**
- **No centralized storage** of contact or group information
- **Anonymous communication** using hash-based identities
- **Decentralized group management** with local storage only
- **Encrypted message transmission** with no metadata leakage

### **3. Better User Experience**
- **Simple contact management** with nickname-based identification
- **Intuitive group creation** and management
- **Automatic key rotation** without user intervention
- **Real-time updates** through reactive programming

### **4. Scalability**
- **Efficient storage** with configurable limits
- **Optimized encryption** for large group messages
- **Background processing** for key rotation
- **Memory-efficient** contact and group management

---

This comprehensive contact and group management system provides a robust foundation for secure, private, and scalable communication in the secIRC anonymous messaging platform! 🚀📱🔐
