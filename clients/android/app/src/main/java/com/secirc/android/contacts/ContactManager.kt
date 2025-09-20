package com.secirc.android.contacts

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.security.PublicKey
import java.security.KeyFactory
import java.security.spec.X509EncodedKeySpec
import java.util.*
import java.util.concurrent.ConcurrentHashMap
import javax.crypto.Cipher
import javax.crypto.spec.SecretKeySpec
import javax.crypto.spec.IvParameterSpec
import kotlin.random.Random

/**
 * secIRC Contact Manager
 * 
 * Manages user contacts, public key exchange, and contact information storage.
 * Handles encrypted storage of contact data and public key management.
 */
class ContactManager(
    private val context: Context,
    private val encryptedPrefs: EncryptedSharedPreferences
) {
    
    companion object {
        private const val CONTACTS_KEY = "contacts"
        private const val PUBLIC_KEYS_KEY = "public_keys"
        private const val CONTACT_REQUESTS_KEY = "contact_requests"
        private const val KEY_ROTATION_INTERVAL = 24 * 60 * 60 * 1000L // 24 hours
        private const val MAX_CONTACTS = 1000
    }
    
    // Contact storage
    private val contacts = ConcurrentHashMap<String, Contact>()
    private val publicKeys = ConcurrentHashMap<String, PublicKey>()
    private val contactRequests = ConcurrentHashMap<String, ContactRequest>()
    
    // Coroutine scope
    private val contactScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    // Contact flow
    private val _contactsFlow = MutableStateFlow<List<Contact>>(emptyList())
    val contactsFlow: StateFlow<List<Contact>> = _contactsFlow.asSharedFlow()
    
    private val _contactRequestsFlow = MutableStateFlow<List<ContactRequest>>(emptyList())
    val contactRequestsFlow: StateFlow<List<ContactRequest>> = _contactRequestsFlow.asSharedFlow()
    
    // Key rotation
    private var keyRotationJob: Job? = null
    
    /**
     * Initialize contact manager
     */
    suspend fun initialize() = withContext(Dispatchers.IO) {
        loadContacts()
        loadPublicKeys()
        loadContactRequests()
        startKeyRotation()
    }
    
    /**
     * Add a new contact
     */
    suspend fun addContact(
        nickname: String,
        userHash: ByteArray,
        publicKey: PublicKey,
        isOnline: Boolean = false
    ): Boolean = withContext(Dispatchers.IO) {
        try {
            // Validate inputs
            validateNickname(nickname)
            validateUserHash(userHash)
            
            // Check if contact already exists
            if (contacts.containsKey(nickname)) {
                throw ContactManagerException("Contact with nickname '$nickname' already exists")
            }
            
            if (contacts.size >= MAX_CONTACTS) {
                throw ContactManagerException("Maximum number of contacts reached")
            }
            
            // Create contact
            val contact = Contact(
                nickname = nickname,
                userHash = userHash,
                publicKey = publicKey,
                isOnline = isOnline,
                addedAt = System.currentTimeMillis(),
                lastSeen = System.currentTimeMillis(),
                keyRotationCount = 0
            )
            
            // Store contact
            contacts[nickname] = contact
            publicKeys[nickname] = publicKey
            
            // Save to encrypted storage
            saveContacts()
            savePublicKeys()
            
            // Update flow
            _contactsFlow.value = contacts.values.toList()
            
            true
            
        } catch (e: Exception) {
            throw ContactManagerException("Failed to add contact", e)
        }
    }
    
    /**
     * Remove a contact
     */
    suspend fun removeContact(nickname: String): Boolean = withContext(Dispatchers.IO) {
        try {
            if (contacts.remove(nickname) != null) {
                publicKeys.remove(nickname)
                saveContacts()
                savePublicKeys()
                _contactsFlow.value = contacts.values.toList()
                true
            } else {
                false
            }
        } catch (e: Exception) {
            throw ContactManagerException("Failed to remove contact", e)
        }
    }
    
    /**
     * Update contact public key
     */
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
    
    /**
     * Get contact by nickname
     */
    fun getContact(nickname: String): Contact? {
        return contacts[nickname]
    }
    
    /**
     * Get contact by user hash
     */
    fun getContactByHash(userHash: ByteArray): Contact? {
        return contacts.values.find { it.userHash.contentEquals(userHash) }
    }
    
    /**
     * Get all contacts
     */
    fun getAllContacts(): List<Contact> {
        return contacts.values.toList()
    }
    
    /**
     * Get online contacts
     */
    fun getOnlineContacts(): List<Contact> {
        return contacts.values.filter { it.isOnline }
    }
    
    /**
     * Update contact online status
     */
    suspend fun updateContactStatus(nickname: String, isOnline: Boolean) = withContext(Dispatchers.IO) {
        val contact = contacts[nickname] ?: return@withContext
        
        val updatedContact = contact.copy(
            isOnline = isOnline,
            lastSeen = System.currentTimeMillis()
        )
        
        contacts[nickname] = updatedContact
        saveContacts()
        _contactsFlow.value = contacts.values.toList()
    }
    
    /**
     * Send contact request
     */
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
            
            // In a real implementation, this would send the request over the network
            // For now, we'll simulate it
            simulateContactRequest(request)
            
            true
            
        } catch (e: Exception) {
            throw ContactManagerException("Failed to send contact request", e)
        }
    }
    
    /**
     * Accept contact request
     */
    suspend fun acceptContactRequest(requestId: String): Boolean = withContext(Dispatchers.IO) {
        try {
            val request = contactRequests[requestId] ?: return@withContext false
            
            if (request.status != ContactRequestStatus.PENDING) {
                return@withContext false
            }
            
            // Add as contact
            val success = addContact(
                nickname = request.requesterNickname,
                userHash = request.targetUserHash,
                publicKey = request.requesterPublicKey
            )
            
            if (success) {
                // Update request status
                val updatedRequest = request.copy(status = ContactRequestStatus.ACCEPTED)
                contactRequests[requestId] = updatedRequest
                saveContactRequests()
                _contactRequestsFlow.value = contactRequests.values.toList()
            }
            
            success
            
        } catch (e: Exception) {
            throw ContactManagerException("Failed to accept contact request", e)
        }
    }
    
    /**
     * Reject contact request
     */
    suspend fun rejectContactRequest(requestId: String): Boolean = withContext(Dispatchers.IO) {
        try {
            val request = contactRequests[requestId] ?: return@withContext false
            
            if (request.status != ContactRequestStatus.PENDING) {
                return@withContext false
            }
            
            val updatedRequest = request.copy(status = ContactRequestStatus.REJECTED)
            contactRequests[requestId] = updatedRequest
            saveContactRequests()
            _contactRequestsFlow.value = contactRequests.values.toList()
            
            true
            
        } catch (e: Exception) {
            throw ContactManagerException("Failed to reject contact request", e)
        }
    }
    
    /**
     * Get pending contact requests
     */
    fun getPendingContactRequests(): List<ContactRequest> {
        return contactRequests.values.filter { it.status == ContactRequestStatus.PENDING }
    }
    
    /**
     * Encrypt message for contact
     */
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
    
    /**
     * Start periodic key rotation
     */
    private fun startKeyRotation() {
        keyRotationJob = contactScope.launch {
            while (isActive) {
                delay(KEY_ROTATION_INTERVAL)
                rotateAllContactKeys()
            }
        }
    }
    
    /**
     * Rotate all contact keys
     */
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
    
    /**
     * Simulate contact request (for testing)
     */
    private suspend fun simulateContactRequest(request: ContactRequest) {
        // In a real implementation, this would send the request over the network
        delay(1000) // Simulate network delay
    }
    
    /**
     * Simulate key rotation (for testing)
     */
    private suspend fun simulateKeyRotation(contact: Contact) {
        // In a real implementation, this would request a new public key from the contact
        delay(100) // Simulate network delay
    }
    
    /**
     * Load contacts from storage
     */
    private fun loadContacts() {
        try {
            val contactsJson = encryptedPrefs.getString(CONTACTS_KEY, null)
            if (contactsJson != null) {
                val contactsList = Contact.fromJsonList(contactsJson)
                contacts.clear()
                contactsList.forEach { contact ->
                    contacts[contact.nickname] = contact
                }
                _contactsFlow.value = contacts.values.toList()
            }
        } catch (e: Exception) {
            // Handle error
        }
    }
    
    /**
     * Save contacts to storage
     */
    private fun saveContacts() {
        try {
            val contactsJson = Contact.toJsonList(contacts.values.toList())
            encryptedPrefs.edit()
                .putString(CONTACTS_KEY, contactsJson)
                .apply()
        } catch (e: Exception) {
            // Handle error
        }
    }
    
    /**
     * Load public keys from storage
     */
    private fun loadPublicKeys() {
        try {
            val keysJson = encryptedPrefs.getString(PUBLIC_KEYS_KEY, null)
            if (keysJson != null) {
                val keysMap = PublicKey.fromJsonMap(keysJson)
                publicKeys.clear()
                publicKeys.putAll(keysMap)
            }
        } catch (e: Exception) {
            // Handle error
        }
    }
    
    /**
     * Save public keys to storage
     */
    private fun savePublicKeys() {
        try {
            val keysJson = PublicKey.toJsonMap(publicKeys)
            encryptedPrefs.edit()
                .putString(PUBLIC_KEYS_KEY, keysJson)
                .apply()
        } catch (e: Exception) {
            // Handle error
        }
    }
    
    /**
     * Load contact requests from storage
     */
    private fun loadContactRequests() {
        try {
            val requestsJson = encryptedPrefs.getString(CONTACT_REQUESTS_KEY, null)
            if (requestsJson != null) {
                val requestsList = ContactRequest.fromJsonList(requestsJson)
                contactRequests.clear()
                requestsList.forEach { request ->
                    contactRequests[request.requestId] = request
                }
                _contactRequestsFlow.value = contactRequests.values.toList()
            }
        } catch (e: Exception) {
            // Handle error
        }
    }
    
    /**
     * Save contact requests to storage
     */
    private fun saveContactRequests() {
        try {
            val requestsJson = ContactRequest.toJsonList(contactRequests.values.toList())
            encryptedPrefs.edit()
                .putString(CONTACT_REQUESTS_KEY, requestsJson)
                .apply()
        } catch (e: Exception) {
            // Handle error
        }
    }
    
    /**
     * Validate nickname
     */
    private fun validateNickname(nickname: String) {
        if (nickname.isBlank()) {
            throw ContactManagerException("Nickname cannot be empty")
        }
        if (nickname.length > 32) {
            throw ContactManagerException("Nickname too long (max 32 characters)")
        }
        if (!nickname.matches(Regex("^[a-zA-Z0-9_-]+$"))) {
            throw ContactManagerException("Nickname contains invalid characters")
        }
    }
    
    /**
     * Validate user hash
     */
    private fun validateUserHash(userHash: ByteArray) {
        if (userHash.size != 16) {
            throw ContactManagerException("Invalid user hash size")
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
     * Generate request ID
     */
    private fun generateRequestId(): String {
        return UUID.randomUUID().toString()
    }
    
    /**
     * Cleanup resources
     */
    fun cleanup() {
        keyRotationJob?.cancel()
        contactScope.cancel()
    }
}

// Data Classes

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
    
    companion object {
        fun fromJsonList(json: String): List<Contact> {
            // Implementation for JSON deserialization
            return emptyList()
        }
        
        fun toJsonList(contacts: List<Contact>): String {
            // Implementation for JSON serialization
            return "[]"
        }
    }
}

data class ContactRequest(
    val requestId: String,
    val targetUserHash: ByteArray,
    val requesterNickname: String,
    val requesterPublicKey: PublicKey,
    val timestamp: Long,
    val status: ContactRequestStatus
) {
    val targetUserHashHex: String
        get() = targetUserHash.joinToString("") { "%02x".format(it) }
    
    companion object {
        fun fromJsonList(json: String): List<ContactRequest> {
            // Implementation for JSON deserialization
            return emptyList()
        }
        
        fun toJsonList(requests: List<ContactRequest>): String {
            // Implementation for JSON serialization
            return "[]"
        }
    }
}

data class EncryptedMessage(
    val encryptedData: ByteArray,
    val encryptedKey: ByteArray,
    val iv: ByteArray,
    val recipientNickname: String,
    val timestamp: Long
)

enum class ContactRequestStatus {
    PENDING, ACCEPTED, REJECTED
}

// Extension functions for PublicKey serialization
fun PublicKey.toJsonMap(keys: Map<String, PublicKey>): String {
    // Implementation for JSON serialization
    return "{}"
}

fun PublicKey.fromJsonMap(json: String): Map<String, PublicKey> {
    // Implementation for JSON deserialization
    return emptyMap()
}

class ContactManagerException(message: String, cause: Throwable? = null) : Exception(message, cause)
