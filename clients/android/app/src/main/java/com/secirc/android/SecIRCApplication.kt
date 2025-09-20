package com.secirc.android

import android.app.Application
import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.secirc.android.di.appModule
import com.secirc.android.security.KeyManager
import com.secirc.android.security.SecurityMonitor
import com.secirc.android.protocol.NetworkManager
import com.secirc.android.protocol.GroupManager
import com.secirc.android.utils.CryptoUtils
import org.koin.android.ext.koin.androidContext
import org.koin.android.ext.koin.androidLogger
import org.koin.core.context.startKoin
import org.koin.core.logger.Level
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

/**
 * secIRC Android Application
 * 
 * Main application class that initializes the secIRC client with security-first design.
 * Handles secure key management, network initialization, and security monitoring.
 */
class SecIRCApplication : Application() {

    // Application scope for background operations
    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    // Core components
    private lateinit var keyManager: KeyManager
    private lateinit var securityMonitor: SecurityMonitor
    private lateinit var networkManager: NetworkManager
    private lateinit var groupManager: GroupManager

    // Encrypted shared preferences
    private lateinit var encryptedPrefs: EncryptedSharedPreferences

    override fun onCreate() {
        super.onCreate()
        
        // Initialize core components
        initializeSecurity()
        initializeNetwork()
        initializeDependencyInjection()
        
        // Start background services
        startBackgroundServices()
        
        // Initialize security monitoring
        startSecurityMonitoring()
    }

    /**
     * Initialize security components
     */
    private fun initializeSecurity() {
        try {
            // Initialize encrypted shared preferences
            val masterKey = MasterKey.Builder(this)
                .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                .build()

            encryptedPrefs = EncryptedSharedPreferences.create(
                this,
                "secirc_secure_prefs",
                masterKey,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
            )

            // Initialize key manager
            keyManager = KeyManager(this, encryptedPrefs)
            
            // Initialize security monitor
            securityMonitor = SecurityMonitor(this)
            
            // Initialize crypto utilities
            CryptoUtils.initialize(this)
            
        } catch (e: Exception) {
            // Log security initialization error
            android.util.Log.e("SecIRC", "Failed to initialize security components", e)
            throw SecurityException("Failed to initialize security components", e)
        }
    }

    /**
     * Initialize network components
     */
    private fun initializeNetwork() {
        try {
            // Initialize network manager
            networkManager = NetworkManager(this, keyManager)
            
            // Initialize group manager
            groupManager = GroupManager(this, keyManager, networkManager)
            
        } catch (e: Exception) {
            android.util.Log.e("SecIRC", "Failed to initialize network components", e)
            throw RuntimeException("Failed to initialize network components", e)
        }
    }

    /**
     * Initialize dependency injection
     */
    private fun initializeDependencyInjection() {
        startKoin {
            androidLogger(Level.INFO)
            androidContext(this@SecIRCApplication)
            modules(appModule)
        }
    }

    /**
     * Start background services
     */
    private fun startBackgroundServices() {
        applicationScope.launch {
            try {
                // Start network service
                networkManager.startNetworkService()
                
                // Start group management service
                groupManager.startGroupService()
                
            } catch (e: Exception) {
                android.util.Log.e("SecIRC", "Failed to start background services", e)
            }
        }
    }

    /**
     * Start security monitoring
     */
    private fun startSecurityMonitoring() {
        applicationScope.launch {
            try {
                // Start security monitoring
                securityMonitor.startMonitoring()
                
            } catch (e: Exception) {
                android.util.Log.e("SecIRC", "Failed to start security monitoring", e)
            }
        }
    }

    /**
     * Get key manager instance
     */
    fun getKeyManager(): KeyManager = keyManager

    /**
     * Get security monitor instance
     */
    fun getSecurityMonitor(): SecurityMonitor = securityMonitor

    /**
     * Get network manager instance
     */
    fun getNetworkManager(): NetworkManager = networkManager

    /**
     * Get group manager instance
     */
    fun getGroupManager(): GroupManager = groupManager

    /**
     * Get encrypted shared preferences
     */
    fun getEncryptedPrefs(): EncryptedSharedPreferences = encryptedPrefs

    /**
     * Check if application is secure
     */
    fun isSecure(): Boolean {
        return try {
            keyManager.isInitialized() && 
            securityMonitor.isMonitoring() && 
            networkManager.isConnected()
        } catch (e: Exception) {
            false
        }
    }

    /**
     * Get application security status
     */
    fun getSecurityStatus(): SecurityStatus {
        return SecurityStatus(
            keyManagerInitialized = keyManager.isInitialized(),
            securityMonitoring = securityMonitor.isMonitoring(),
            networkConnected = networkManager.isConnected(),
            biometricAvailable = keyManager.isBiometricAvailable(),
            hardwareSecurityAvailable = keyManager.isHardwareSecurityAvailable()
        )
    }

    override fun onTerminate() {
        super.onTerminate()
        
        // Stop background services
        applicationScope.launch {
            try {
                networkManager.stopNetworkService()
                groupManager.stopGroupService()
                securityMonitor.stopMonitoring()
            } catch (e: Exception) {
                android.util.Log.e("SecIRC", "Failed to stop services", e)
            }
        }
    }

    /**
     * Security status data class
     */
    data class SecurityStatus(
        val keyManagerInitialized: Boolean,
        val securityMonitoring: Boolean,
        val networkConnected: Boolean,
        val biometricAvailable: Boolean,
        val hardwareSecurityAvailable: Boolean
    ) {
        val isSecure: Boolean
            get() = keyManagerInitialized && securityMonitoring && networkConnected
    }

    companion object {
        /**
         * Get application instance
         */
        fun getInstance(context: Context): SecIRCApplication {
            return context.applicationContext as SecIRCApplication
        }
    }
}
