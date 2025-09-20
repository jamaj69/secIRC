import SwiftUI
import Combine
import LocalAuthentication
import Security

/**
 * secIRC iOS Application
 * 
 * Main application class that initializes the secIRC client with security-first design.
 * Handles secure key management, network initialization, and security monitoring.
 */
@main
struct SecIRCApp: App {
    
    // Application state
    @StateObject private var appState = AppState()
    @StateObject private var keyManager = KeyManager()
    @StateObject private var securityMonitor = SecurityMonitor()
    @StateObject private var networkManager = NetworkManager()
    @StateObject private var groupManager = GroupManager()
    
    // Biometric authentication
    @State private var isBiometricAvailable = false
    @State private var isAuthenticated = false
    
    // Security status
    @State private var securityStatus = SecurityStatus()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appState)
                .environmentObject(keyManager)
                .environmentObject(securityMonitor)
                .environmentObject(networkManager)
                .environmentObject(groupManager)
                .onAppear {
                    initializeApp()
                }
                .onReceive(NotificationCenter.default.publisher(for: UIApplication.didBecomeActiveNotification)) { _ in
                    checkSecurityStatus()
                }
        }
    }
    
    /**
     * Initialize the application
     */
    private func initializeApp() {
        Task {
            do {
                // Initialize security components
                try await initializeSecurity()
                
                // Initialize network components
                try await initializeNetwork()
                
                // Start security monitoring
                try await startSecurityMonitoring()
                
                // Check biometric availability
                checkBiometricAvailability()
                
                // Update security status
                updateSecurityStatus()
                
            } catch {
                print("❌ Failed to initialize app: \(error)")
                appState.setError(error)
            }
        }
    }
    
    /**
     * Initialize security components
     */
    private func initializeSecurity() async throws {
        try await keyManager.initialize()
        try await securityMonitor.initialize()
    }
    
    /**
     * Initialize network components
     */
    private func initializeNetwork() async throws {
        try await networkManager.initialize(keyManager: keyManager)
        try await groupManager.initialize(keyManager: keyManager, networkManager: networkManager)
    }
    
    /**
     * Start security monitoring
     */
    private func startSecurityMonitoring() async throws {
        try await securityMonitor.startMonitoring()
    }
    
    /**
     * Check biometric availability
     */
    private func checkBiometricAvailability() {
        let context = LAContext()
        var error: NSError?
        
        isBiometricAvailable = context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error)
    }
    
    /**
     * Check security status
     */
    private func checkSecurityStatus() {
        Task {
            do {
                // Check if user needs to re-authenticate
                if appState.needsAuthentication {
                    try await authenticateUser()
                }
                
                // Update security status
                updateSecurityStatus()
                
            } catch {
                print("❌ Security check failed: \(error)")
                appState.setError(error)
            }
        }
    }
    
    /**
     * Authenticate user
     */
    private func authenticateUser() async throws {
        if isBiometricAvailable {
            let context = LAContext()
            let result = try await context.evaluatePolicy(
                .deviceOwnerAuthenticationWithBiometrics,
                localizedReason: "Authenticate to access secIRC"
            )
            isAuthenticated = result
        } else {
            // Fallback to device passcode
            let context = LAContext()
            let result = try await context.evaluatePolicy(
                .deviceOwnerAuthentication,
                localizedReason: "Authenticate to access secIRC"
            )
            isAuthenticated = result
        }
        
        appState.setAuthenticated(isAuthenticated)
    }
    
    /**
     * Update security status
     */
    private func updateSecurityStatus() {
        securityStatus = SecurityStatus(
            keyManagerInitialized: keyManager.isInitialized,
            securityMonitoring: securityMonitor.isMonitoring,
            networkConnected: networkManager.isConnected,
            biometricAvailable: isBiometricAvailable,
            hardwareSecurityAvailable: keyManager.isHardwareSecurityAvailable,
            isAuthenticated: isAuthenticated
        )
        
        appState.setSecurityStatus(securityStatus)
    }
}

/**
 * Application state management
 */
class AppState: ObservableObject {
    @Published var isAuthenticated = false
    @Published var needsAuthentication = true
    @Published var securityStatus = SecurityStatus()
    @Published var error: Error?
    @Published var isLoading = false
    
    func setAuthenticated(_ authenticated: Bool) {
        isAuthenticated = authenticated
        needsAuthentication = !authenticated
    }
    
    func setSecurityStatus(_ status: SecurityStatus) {
        securityStatus = status
    }
    
    func setError(_ error: Error) {
        self.error = error
    }
    
    func setLoading(_ loading: Bool) {
        isLoading = loading
    }
}

/**
 * Security status data structure
 */
struct SecurityStatus {
    let keyManagerInitialized: Bool
    let securityMonitoring: Bool
    let networkConnected: Bool
    let biometricAvailable: Bool
    let hardwareSecurityAvailable: Bool
    let isAuthenticated: Bool
    
    var isSecure: Bool {
        keyManagerInitialized && securityMonitoring && networkConnected && isAuthenticated
    }
    
    init(
        keyManagerInitialized: Bool = false,
        securityMonitoring: Bool = false,
        networkConnected: Bool = false,
        biometricAvailable: Bool = false,
        hardwareSecurityAvailable: Bool = false,
        isAuthenticated: Bool = false
    ) {
        self.keyManagerInitialized = keyManagerInitialized
        self.securityMonitoring = securityMonitoring
        self.networkConnected = networkConnected
        self.biometricAvailable = biometricAvailable
        self.hardwareSecurityAvailable = hardwareSecurityAvailable
        self.isAuthenticated = isAuthenticated
    }
}
