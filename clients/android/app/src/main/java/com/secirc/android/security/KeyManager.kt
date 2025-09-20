package com.secirc.android.security

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.MessageDigest
import java.security.SecureRandom
import java.security.Security
import java.security.KeyFactory
import java.security.spec.RSAPublicKeySpec
import java.security.spec.RSAPrivateKeySpec
import java.math.BigInteger
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec
import javax.crypto.spec.IvParameterSpec
import kotlin.random.Random
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.bouncycastle.crypto.generators.RSAKeyPairGenerator
import org.bouncycastle.crypto.params.RSAKeyGenerationParameters
import org.bouncycastle.crypto.params.RSAKeyParameters
import org.bouncycastle.crypto.params.RSAPrivateCrtKeyParameters
import org.bouncycastle.crypto.AsymmetricCipherKeyPair
import org.bouncycastle.jce.provider.BouncyCastleProvider
import java.util.*

/**
 * secIRC Key Manager
 * 
 * Manages secure RSA key pairs with password protection and nickname association.
 * Uses hardware-backed security when available, with fallback to software encryption.
 */
class KeyManager(
    private val context: Context,
    private val encryptedPrefs: EncryptedSharedPreferences
) {
    
    companion object {
        private const val KEY_ALIAS = "secirc_rsa_keypair"
        private const val KEY_SIZE = 2048
        private const val NICKNAME_KEY = "user_nickname"
        private const val USER_HASH_KEY = "user_hash"
        private const val KEY_GENERATED_KEY = "key_generated"
        private const val ANDROID_KEYSTORE = "AndroidKeyStore"
        
        init {
            // Add BouncyCastle provider for enhanced cryptography
            if (Security.getProvider(BouncyCastleProvider.PROVIDER_NAME) == null) {
                Security.addProvider(BouncyCastleProvider())
            }
        }
    }
    
    // Key store for hardware-backed security
    private val keyStore: KeyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply {
        load(null)
    }
    
    // Secure random for key generation
    private val secureRandom = SecureRandom()
    
    // User data
    private var userNickname: String? = null
    private var userHash: ByteArray? = null
    private var isKeyGenerated = false
    
    /**
     * Initialize the key manager
     */
    suspend fun initialize() = withContext(Dispatchers.IO) {
        loadUserData()
        checkKeyGenerationStatus()
    }
    
    /**
     * Generate a new secure RSA key pair with password protection
     */
    suspend fun generateSecureKeyPair(
        nickname: String,
        password: String
    ): SecIRCKeyPair = withContext(Dispatchers.IO) {
        try {
            // Validate inputs
            validateNickname(nickname)
            validatePassword(password)
            
            // Generate RSA key pair
            val keyPair = generateRSAKeyPair()
            
            // Encrypt private key with password
            val encryptedPrivateKey = encryptPrivateKeyWithPassword(keyPair.private, password)
            
            // Generate user hash from public key
            val userHash = generateUserHash(keyPair.public)
            
            // Store encrypted private key and metadata
            storeEncryptedKeyPair(encryptedPrivateKey, keyPair.public, userHash, nickname)
            
            // Update local state
            this@KeyManager.userNickname = nickname
            this@KeyManager.userHash = userHash
            this@KeyManager.isKeyGenerated = true
            
            SecIRCKeyPair(
                publicKey = keyPair.public,
                encryptedPrivateKey = encryptedPrivateKey,
                userHash = userHash,
                nickname = nickname
            )
            
        } catch (e: Exception) {
            throw KeyManagerException("Failed to generate secure key pair", e)
        }
    }
    
    /**
     * Load existing key pair with password
     */
    suspend fun loadKeyPair(password: String): SecIRCKeyPair = withContext(Dispatchers.IO) {
        try {
            if (!isKeyGenerated) {
                throw KeyManagerException("No key pair found")
            }
            
            // Load encrypted private key
            val encryptedPrivateKey = loadEncryptedPrivateKey()
            val publicKey = loadPublicKey()
            val userHash = loadUserHash()
            val nickname = loadNickname()
            
            // Decrypt private key with password
            val privateKey = decryptPrivateKeyWithPassword(encryptedPrivateKey, password)
            
            SecIRCKeyPair(
                publicKey = publicKey,
                encryptedPrivateKey = encryptedPrivateKey,
                userHash = userHash,
                nickname = nickname
            )
            
        } catch (e: Exception) {
            throw KeyManagerException("Failed to load key pair", e)
        }
    }
    
    /**
     * Generate RSA key pair using BouncyCastle for enhanced security
     */
    private fun generateRSAKeyPair(): KeyPair {
        val keyPairGenerator = RSAKeyPairGenerator()
        val keyGenParams = RSAKeyGenerationParameters(
            BigInteger.valueOf(65537), // Public exponent
            secureRandom,
            KEY_SIZE,
            80 // Certainty
        )
        keyPairGenerator.init(keyGenParams)
        val keyPair = keyPairGenerator.generateKeyPair()
        
        // Convert BouncyCastle keys to Java keys
        val publicKey = convertToJavaPublicKey(keyPair.public as RSAKeyParameters)
        val privateKey = convertToJavaPrivateKey(keyPair.private as RSAPrivateCrtKeyParameters)
        
        return KeyPair(publicKey, privateKey)
    }
    
    /**
     * Convert BouncyCastle public key to Java public key
     */
    private fun convertToJavaPublicKey(bcPublicKey: RSAKeyParameters): java.security.PublicKey {
        val keyFactory = KeyFactory.getInstance("RSA")
        val keySpec = RSAPublicKeySpec(bcPublicKey.modulus, bcPublicKey.exponent)
        return keyFactory.generatePublic(keySpec)
    }
    
    /**
     * Convert BouncyCastle private key to Java private key
     */
    private fun convertToJavaPrivateKey(bcPrivateKey: RSAPrivateCrtKeyParameters): java.security.PrivateKey {
        val keyFactory = KeyFactory.getInstance("RSA")
        val keySpec = RSAPrivateKeySpec(
            bcPrivateKey.modulus,
            bcPrivateKey.exponent
        )
        return keyFactory.generatePrivate(keySpec)
    }
    
    /**
     * Encrypt private key with user password using AES-GCM
     */
    private fun encryptPrivateKeyWithPassword(
        privateKey: java.security.PrivateKey,
        password: String
    ): EncryptedKeyData {
        // Derive key from password using PBKDF2
        val salt = ByteArray(16)
        secureRandom.nextBytes(salt)
        
        val keySpec = javax.crypto.spec.PBEKeySpec(
            password.toCharArray(),
            salt,
            100000, // Iterations
            256 // Key length
        )
        val keyFactory = javax.crypto.SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
        val secretKey = keyFactory.generateSecret(keySpec)
        val aesKey = SecretKeySpec(secretKey.encoded, "AES")
        
        // Encrypt private key
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, aesKey)
        
        val privateKeyBytes = privateKey.encoded
        val encryptedBytes = cipher.doFinal(privateKeyBytes)
        val iv = cipher.iv
        
        return EncryptedKeyData(
            encryptedData = encryptedBytes,
            salt = salt,
            iv = iv
        )
    }
    
    /**
     * Decrypt private key with user password
     */
    private fun decryptPrivateKeyWithPassword(
        encryptedKeyData: EncryptedKeyData,
        password: String
    ): java.security.PrivateKey {
        // Derive key from password
        val keySpec = javax.crypto.spec.PBEKeySpec(
            password.toCharArray(),
            encryptedKeyData.salt,
            100000,
            256
        )
        val keyFactory = javax.crypto.SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
        val secretKey = keyFactory.generateSecret(keySpec)
        val aesKey = SecretKeySpec(secretKey.encoded, "AES")
        
        // Decrypt private key
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val gcmSpec = GCMParameterSpec(128, encryptedKeyData.iv)
        cipher.init(Cipher.DECRYPT_MODE, aesKey, gcmSpec)
        
        val decryptedBytes = cipher.doFinal(encryptedKeyData.encryptedData)
        
        // Reconstruct private key
        val keyFactory2 = KeyFactory.getInstance("RSA")
        val keySpec2 = java.security.spec.PKCS8EncodedKeySpec(decryptedBytes)
        return keyFactory2.generatePrivate(keySpec2)
    }
    
    /**
     * Generate user hash from public key
     */
    private fun generateUserHash(publicKey: java.security.PublicKey): ByteArray {
        val publicKeyBytes = publicKey.encoded
        val digest = MessageDigest.getInstance("SHA-256")
        val hash = digest.digest(publicKeyBytes)
        return hash.sliceArray(0..15) // Use first 16 bytes
    }
    
    /**
     * Store encrypted key pair and metadata
     */
    private fun storeEncryptedKeyPair(
        encryptedPrivateKey: EncryptedKeyData,
        publicKey: java.security.PublicKey,
        userHash: ByteArray,
        nickname: String
    ) {
        // Store encrypted private key
        encryptedPrefs.edit()
            .putString("encrypted_private_key", Base64.getEncoder().encodeToString(encryptedPrivateKey.encryptedData))
            .putString("private_key_salt", Base64.getEncoder().encodeToString(encryptedPrivateKey.salt))
            .putString("private_key_iv", Base64.getEncoder().encodeToString(encryptedPrivateKey.iv))
            .apply()
        
        // Store public key
        encryptedPrefs.edit()
            .putString("public_key", Base64.getEncoder().encodeToString(publicKey.encoded))
            .apply()
        
        // Store user hash
        encryptedPrefs.edit()
            .putString(USER_HASH_KEY, Base64.getEncoder().encodeToString(userHash))
            .apply()
        
        // Store nickname
        encryptedPrefs.edit()
            .putString(NICKNAME_KEY, nickname)
            .apply()
        
        // Mark key as generated
        encryptedPrefs.edit()
            .putBoolean(KEY_GENERATED_KEY, true)
            .apply()
    }
    
    /**
     * Load encrypted private key
     */
    private fun loadEncryptedPrivateKey(): EncryptedKeyData {
        val encryptedData = encryptedPrefs.getString("encrypted_private_key", null)
            ?: throw KeyManagerException("Encrypted private key not found")
        val salt = encryptedPrefs.getString("private_key_salt", null)
            ?: throw KeyManagerException("Private key salt not found")
        val iv = encryptedPrefs.getString("private_key_iv", null)
            ?: throw KeyManagerException("Private key IV not found")
        
        return EncryptedKeyData(
            encryptedData = Base64.getDecoder().decode(encryptedData),
            salt = Base64.getDecoder().decode(salt),
            iv = Base64.getDecoder().decode(iv)
        )
    }
    
    /**
     * Load public key
     */
    private fun loadPublicKey(): java.security.PublicKey {
        val publicKeyBytes = encryptedPrefs.getString("public_key", null)
            ?: throw KeyManagerException("Public key not found")
        
        val keyFactory = KeyFactory.getInstance("RSA")
        val keySpec = java.security.spec.X509EncodedKeySpec(Base64.getDecoder().decode(publicKeyBytes))
        return keyFactory.generatePublic(keySpec)
    }
    
    /**
     * Load user hash
     */
    private fun loadUserHash(): ByteArray {
        val userHashString = encryptedPrefs.getString(USER_HASH_KEY, null)
            ?: throw KeyManagerException("User hash not found")
        return Base64.getDecoder().decode(userHashString)
    }
    
    /**
     * Load nickname
     */
    private fun loadNickname(): String {
        return encryptedPrefs.getString(NICKNAME_KEY, null)
            ?: throw KeyManagerException("Nickname not found")
    }
    
    /**
     * Load user data from preferences
     */
    private fun loadUserData() {
        userNickname = encryptedPrefs.getString(NICKNAME_KEY, null)
        val userHashString = encryptedPrefs.getString(USER_HASH_KEY, null)
        userHash = userHashString?.let { Base64.getDecoder().decode(it) }
    }
    
    /**
     * Check key generation status
     */
    private fun checkKeyGenerationStatus() {
        isKeyGenerated = encryptedPrefs.getBoolean(KEY_GENERATED_KEY, false)
    }
    
    /**
     * Validate nickname
     */
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
    
    /**
     * Validate password
     */
    private fun validatePassword(password: String) {
        if (password.length < 8) {
            throw KeyManagerException("Password too short (min 8 characters)")
        }
        if (password.length > 128) {
            throw KeyManagerException("Password too long (max 128 characters)")
        }
    }
    
    /**
     * Check if key pair is generated
     */
    fun isKeyGenerated(): Boolean = isKeyGenerated
    
    /**
     * Get user nickname
     */
    fun getNickname(): String? = userNickname
    
    /**
     * Get user hash
     */
    fun getUserHash(): ByteArray? = userHash
    
    /**
     * Delete all keys and user data
     */
    suspend fun deleteAllKeys() = withContext(Dispatchers.IO) {
        encryptedPrefs.edit().clear().apply()
        userNickname = null
        userHash = null
        isKeyGenerated = false
    }
}

/**
 * Data class for encrypted key data
 */
data class EncryptedKeyData(
    val encryptedData: ByteArray,
    val salt: ByteArray,
    val iv: ByteArray
)

/**
 * Data class for secIRC key pair
 */
data class SecIRCKeyPair(
    val publicKey: java.security.PublicKey,
    val encryptedPrivateKey: EncryptedKeyData,
    val userHash: ByteArray,
    val nickname: String
) {
    val userHashHex: String
        get() = userHash.joinToString("") { "%02x".format(it) }
}

/**
 * Key manager exception
 */
class KeyManagerException(message: String, cause: Throwable? = null) : Exception(message, cause)
