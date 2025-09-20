package com.secirc.android.groups

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.security.PublicKey
import java.util.*
import java.util.concurrent.ConcurrentHashMap
import javax.crypto.Cipher
import javax.crypto.spec.SecretKeySpec
import javax.crypto.spec.IvParameterSpec
import kotlin.random.Random

/**
 * secIRC Group Manager
 * 
 * Manages local groups with encrypted storage, member invitations, and group messaging.
 * Groups are stored locally and encrypted, with member management and invitation system.
 */
class GroupManager(
    private val context: Context,
    private val encryptedPrefs: EncryptedSharedPreferences
) {
    
    companion object {
        private const val GROUPS_KEY = "groups"
        private const val GROUP_INVITATIONS_KEY = "group_invitations"
        private const val GROUP_MESSAGES_KEY = "group_messages"
        private const val KEY_ROTATION_INTERVAL = 24 * 60 * 60 * 1000L // 24 hours
        private const val MAX_GROUPS = 100
        private const val MAX_GROUP_MEMBERS = 50
    }
    
    // Group storage
    private val groups = ConcurrentHashMap<String, Group>()
    private val groupInvitations = ConcurrentHashMap<String, GroupInvitation>()
    private val groupMessages = ConcurrentHashMap<String, MutableList<GroupMessage>>()
    
    // Coroutine scope
    private val groupScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    // Group flows
    private val _groupsFlow = MutableStateFlow<List<Group>>(emptyList())
    val groupsFlow: StateFlow<List<Group>> = _groupsFlow.asSharedFlow()
    
    private val _groupInvitationsFlow = MutableStateFlow<List<GroupInvitation>>(emptyList())
    val groupInvitationsFlow: StateFlow<List<GroupInvitation>> = _groupInvitationsFlow.asSharedFlow()
    
    // Key rotation
    private var keyRotationJob: Job? = null
    
    /**
     * Initialize group manager
     */
    suspend fun initialize() = withContext(Dispatchers.IO) {
        loadGroups()
        loadGroupInvitations()
        loadGroupMessages()
        startKeyRotation()
    }
    
    /**
     * Create a new group
     */
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
    
    /**
     * Invite user to group
     */
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
            
            // In a real implementation, this would send the invitation over the network
            simulateGroupInvitation(invitation)
            
            true
            
        } catch (e: Exception) {
            throw GroupManagerException("Failed to invite user to group", e)
        }
    }
    
    /**
     * Accept group invitation
     */
    suspend fun acceptGroupInvitation(invitationId: String): Boolean = withContext(Dispatchers.IO) {
        try {
            val invitation = groupInvitations[invitationId] ?: return@withContext false
            
            if (invitation.status != GroupInvitationStatus.PENDING) {
                return@withContext false
            }
            
            val group = groups[invitation.groupId] ?: return@withContext false
            
            // Add user to group
            val newMember = GroupMember(
                nickname = invitation.targetNickname,
                userHash = invitation.targetUserHash,
                publicKey = invitation.targetPublicKey,
                role = GroupRole.MEMBER,
                joinedAt = System.currentTimeMillis(),
                isActive = true
            )
            
            group.members[invitation.targetNickname] = newMember
            group.lastActivity = System.currentTimeMillis()
            
            // Update invitation status
            val updatedInvitation = invitation.copy(status = GroupInvitationStatus.ACCEPTED)
            groupInvitations[invitationId] = updatedInvitation
            
            // Save to storage
            saveGroups()
            saveGroupInvitations()
            
            // Update flows
            _groupsFlow.value = groups.values.toList()
            _groupInvitationsFlow.value = groupInvitations.values.toList()
            
            true
            
        } catch (e: Exception) {
            throw GroupManagerException("Failed to accept group invitation", e)
        }
    }
    
    /**
     * Reject group invitation
     */
    suspend fun rejectGroupInvitation(invitationId: String): Boolean = withContext(Dispatchers.IO) {
        try {
            val invitation = groupInvitations[invitationId] ?: return@withContext false
            
            if (invitation.status != GroupInvitationStatus.PENDING) {
                return@withContext false
            }
            
            val updatedInvitation = invitation.copy(status = GroupInvitationStatus.REJECTED)
            groupInvitations[invitationId] = updatedInvitation
            
            // Save to storage
            saveGroupInvitations()
            
            // Update flow
            _groupInvitationsFlow.value = groupInvitations.values.toList()
            
            true
            
        } catch (e: Exception) {
            throw GroupManagerException("Failed to reject group invitation", e)
        }
    }
    
    /**
     * Remove member from group
     */
    suspend fun removeMemberFromGroup(
        groupId: String,
        memberNickname: String,
        removerNickname: String
    ): Boolean = withContext(Dispatchers.IO) {
        try {
            val group = groups[groupId] ?: return@withContext false
            
            // Check permissions
            val removerMember = group.members[removerNickname]
            if (removerMember?.role != GroupRole.OWNER) {
                throw GroupManagerException("Only group owner can remove members")
            }
            
            // Cannot remove owner
            if (memberNickname == group.ownerNickname) {
                throw GroupManagerException("Cannot remove group owner")
            }
            
            // Remove member
            group.members.remove(memberNickname)
            group.lastActivity = System.currentTimeMillis()
            
            // Save to storage
            saveGroups()
            
            // Update flow
            _groupsFlow.value = groups.values.toList()
            
            true
            
        } catch (e: Exception) {
            throw GroupManagerException("Failed to remove member from group", e)
        }
    }
    
    /**
     * Leave group
     */
    suspend fun leaveGroup(groupId: String, memberNickname: String): Boolean = withContext(Dispatchers.IO) {
        try {
            val group = groups[groupId] ?: return@withContext false
            
            // Owner cannot leave group (must transfer ownership or delete group)
            if (memberNickname == group.ownerNickname) {
                throw GroupManagerException("Group owner cannot leave group. Transfer ownership or delete group.")
            }
            
            // Remove member
            group.members.remove(memberNickname)
            group.lastActivity = System.currentTimeMillis()
            
            // Save to storage
            saveGroups()
            
            // Update flow
            _groupsFlow.value = groups.values.toList()
            
            true
            
        } catch (e: Exception) {
            throw GroupManagerException("Failed to leave group", e)
        }
    }
    
    /**
     * Delete group
     */
    suspend fun deleteGroup(groupId: String, ownerNickname: String): Boolean = withContext(Dispatchers.IO) {
        try {
            val group = groups[groupId] ?: return@withContext false
            
            // Only owner can delete group
            if (group.ownerNickname != ownerNickname) {
                throw GroupManagerException("Only group owner can delete group")
            }
            
            // Remove group
            groups.remove(groupId)
            groupMessages.remove(groupId)
            
            // Save to storage
            saveGroups()
            saveGroupMessages()
            
            // Update flow
            _groupsFlow.value = groups.values.toList()
            
            true
            
        } catch (e: Exception) {
            throw GroupManagerException("Failed to delete group", e)
        }
    }
    
    /**
     * Send message to group
     */
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
    
    /**
     * Get group by ID
     */
    fun getGroup(groupId: String): Group? {
        return groups[groupId]
    }
    
    /**
     * Get groups for user
     */
    fun getGroupsForUser(userNickname: String): List<Group> {
        return groups.values.filter { it.members.containsKey(userNickname) }
    }
    
    /**
     * Get owned groups
     */
    fun getOwnedGroups(ownerNickname: String): List<Group> {
        return groups.values.filter { it.ownerNickname == ownerNickname }
    }
    
    /**
     * Get group messages
     */
    fun getGroupMessages(groupId: String): List<GroupMessage> {
        return groupMessages[groupId] ?: emptyList()
    }
    
    /**
     * Get pending group invitations
     */
    fun getPendingGroupInvitations(): List<GroupInvitation> {
        return groupInvitations.values.filter { it.status == GroupInvitationStatus.PENDING }
    }
    
    /**
     * Encrypt message for group member
     */
    private fun encryptMessageForMember(message: ByteArray, publicKey: PublicKey): EncryptedGroupMessage {
        // Generate random AES key
        val aesKey = generateRandomBytes(32)
        val iv = generateRandomBytes(16)
        
        // Encrypt message with AES
        val cipher = Cipher.getInstance("AES/CBC/PKCS5Padding")
        val secretKey = SecretKeySpec(aesKey, "AES")
        val ivSpec = IvParameterSpec(iv)
        cipher.init(Cipher.ENCRYPT_MODE, secretKey, ivSpec)
        val encryptedMessage = cipher.doFinal(message)
        
        // Encrypt AES key with member's public key
        val rsaCipher = Cipher.getInstance("RSA/ECB/PKCS1Padding")
        rsaCipher.init(Cipher.ENCRYPT_MODE, publicKey)
        val encryptedAesKey = rsaCipher.doFinal(aesKey)
        
        return EncryptedGroupMessage(
            encryptedData = encryptedMessage,
            encryptedKey = encryptedAesKey,
            iv = iv
        )
    }
    
    /**
     * Start periodic key rotation
     */
    private fun startKeyRotation() {
        keyRotationJob = groupScope.launch {
            while (isActive) {
                delay(KEY_ROTATION_INTERVAL)
                rotateAllGroupKeys()
            }
        }
    }
    
    /**
     * Rotate all group keys
     */
    private suspend fun rotateAllGroupKeys() = withContext(Dispatchers.IO) {
        try {
            // In a real implementation, this would request new public keys from all group members
            // For now, we'll simulate key rotation
            for (group in groups.values) {
                simulateGroupKeyRotation(group)
            }
        } catch (e: Exception) {
            // Handle error
        }
    }
    
    /**
     * Simulate group invitation (for testing)
     */
    private suspend fun simulateGroupInvitation(invitation: GroupInvitation) {
        // In a real implementation, this would send the invitation over the network
        delay(1000) // Simulate network delay
    }
    
    /**
     * Simulate group key rotation (for testing)
     */
    private suspend fun simulateGroupKeyRotation(group: Group) {
        // In a real implementation, this would request new public keys from all group members
        delay(100) // Simulate network delay
    }
    
    /**
     * Load groups from storage
     */
    private fun loadGroups() {
        try {
            val groupsJson = encryptedPrefs.getString(GROUPS_KEY, null)
            if (groupsJson != null) {
                val groupsList = Group.fromJsonList(groupsJson)
                groups.clear()
                groupsList.forEach { group ->
                    groups[group.groupId] = group
                }
                _groupsFlow.value = groups.values.toList()
            }
        } catch (e: Exception) {
            // Handle error
        }
    }
    
    /**
     * Save groups to storage
     */
    private fun saveGroups() {
        try {
            val groupsJson = Group.toJsonList(groups.values.toList())
            encryptedPrefs.edit()
                .putString(GROUPS_KEY, groupsJson)
                .apply()
        } catch (e: Exception) {
            // Handle error
        }
    }
    
    /**
     * Load group invitations from storage
     */
    private fun loadGroupInvitations() {
        try {
            val invitationsJson = encryptedPrefs.getString(GROUP_INVITATIONS_KEY, null)
            if (invitationsJson != null) {
                val invitationsList = GroupInvitation.fromJsonList(invitationsJson)
                groupInvitations.clear()
                invitationsList.forEach { invitation ->
                    groupInvitations[invitation.invitationId] = invitation
                }
                _groupInvitationsFlow.value = groupInvitations.values.toList()
            }
        } catch (e: Exception) {
            // Handle error
        }
    }
    
    /**
     * Save group invitations to storage
     */
    private fun saveGroupInvitations() {
        try {
            val invitationsJson = GroupInvitation.toJsonList(groupInvitations.values.toList())
            encryptedPrefs.edit()
                .putString(GROUP_INVITATIONS_KEY, invitationsJson)
                .apply()
        } catch (e: Exception) {
            // Handle error
        }
    }
    
    /**
     * Load group messages from storage
     */
    private fun loadGroupMessages() {
        try {
            val messagesJson = encryptedPrefs.getString(GROUP_MESSAGES_KEY, null)
            if (messagesJson != null) {
                val messagesMap = GroupMessage.fromJsonMap(messagesJson)
                groupMessages.clear()
                groupMessages.putAll(messagesMap)
            }
        } catch (e: Exception) {
            // Handle error
        }
    }
    
    /**
     * Save group messages to storage
     */
    private fun saveGroupMessages() {
        try {
            val messagesJson = GroupMessage.toJsonMap(groupMessages)
            encryptedPrefs.edit()
                .putString(GROUP_MESSAGES_KEY, messagesJson)
                .apply()
        } catch (e: Exception) {
            // Handle error
        }
    }
    
    /**
     * Validate group name
     */
    private fun validateGroupName(groupName: String) {
        if (groupName.isBlank()) {
            throw GroupManagerException("Group name cannot be empty")
        }
        if (groupName.length > 64) {
            throw GroupManagerException("Group name too long (max 64 characters)")
        }
    }
    
    /**
     * Validate description
     */
    private fun validateDescription(description: String) {
        if (description.length > 256) {
            throw GroupManagerException("Description too long (max 256 characters)")
        }
    }
    
    /**
     * Generate random bytes
     */
    private fun generateRandomBytes(size: Int): ByteArray {
        val bytes = ByteArray(size)
        Random.nextBytes(bytes)
        return bytes
    }
    
    /**
     * Generate group ID
     */
    private fun generateGroupId(): String {
        return UUID.randomUUID().toString()
    }
    
    /**
     * Generate invitation ID
     */
    private fun generateInvitationId(): String {
        return UUID.randomUUID().toString()
    }
    
    /**
     * Generate message ID
     */
    private fun generateMessageId(): String {
        return UUID.randomUUID().toString()
    }
    
    /**
     * Cleanup resources
     */
    fun cleanup() {
        keyRotationJob?.cancel()
        groupScope.cancel()
    }
}

// Data Classes

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
    
    companion object {
        fun fromJsonList(json: String): List<Group> {
            // Implementation for JSON deserialization
            return emptyList()
        }
        
        fun toJsonList(groups: List<Group>): String {
            // Implementation for JSON serialization
            return "[]"
        }
    }
}

data class GroupMember(
    val nickname: String,
    val userHash: ByteArray,
    val publicKey: PublicKey,
    val role: GroupRole,
    val joinedAt: Long,
    val isActive: Boolean
) {
    val userHashHex: String
        get() = userHash.joinToString("") { "%02x".format(it) }
    
    companion object {
        fun fromJsonList(json: String): List<GroupMember> {
            // Implementation for JSON deserialization
            return emptyList()
        }
        
        fun toJsonList(members: List<GroupMember>): String {
            // Implementation for JSON serialization
            return "[]"
        }
    }
}

data class GroupInvitation(
    val invitationId: String,
    val groupId: String,
    val groupName: String,
    val targetNickname: String,
    val targetUserHash: ByteArray,
    val targetPublicKey: PublicKey,
    val inviterNickname: String,
    val timestamp: Long,
    val status: GroupInvitationStatus
) {
    val targetUserHashHex: String
        get() = targetUserHash.joinToString("") { "%02x".format(it) }
    
    companion object {
        fun fromJsonList(json: String): List<GroupInvitation> {
            // Implementation for JSON deserialization
            return emptyList()
        }
        
        fun toJsonList(invitations: List<GroupInvitation>): String {
            // Implementation for JSON serialization
            return "[]"
        }
    }
}

data class GroupMessage(
    val messageId: String,
    val groupId: String,
    val senderNickname: String,
    val content: ByteArray,
    val messageType: GroupMessageType,
    val timestamp: Long,
    val encryptedForMembers: MutableMap<String, EncryptedGroupMessage>
) {
    companion object {
        fun fromJsonMap(json: String): Map<String, MutableList<GroupMessage>> {
            // Implementation for JSON deserialization
            return emptyMap()
        }
        
        fun toJsonMap(messages: Map<String, MutableList<GroupMessage>>): String {
            // Implementation for JSON serialization
            return "{}"
        }
    }
}

data class EncryptedGroupMessage(
    val encryptedData: ByteArray,
    val encryptedKey: ByteArray,
    val iv: ByteArray
)

enum class GroupRole {
    OWNER, MEMBER
}

enum class GroupInvitationStatus {
    PENDING, ACCEPTED, REJECTED
}

enum class GroupMessageType {
    TEXT, FILE, IMAGE, VOICE
}

class GroupManagerException(message: String, cause: Throwable? = null) : Exception(message, cause)
