import SwiftUI

/**
 * Login View - User authentication and key management
 * 
 * Handles user login with password and key pair management
 * Similar to secure messaging app login screens
 */
struct LoginView: View {
    let onLoginSuccess: () -> Void
    
    @State private var nickname = ""
    @State private var password = ""
    @State private var showPassword = false
    @State private var isLoading = false
    @State private var errorMessage = ""
    @State private var isNewUser = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    Spacer(minLength: 40)
                    
                    // App Logo/Icon
                    Image(systemName: "lock.shield")
                        .font(.system(size: 80))
                        .foregroundColor(.blue)
                    
                    // App Title
                    Text("secIRC")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .foregroundColor(.blue)
                    
                    Text("Secure Anonymous Messaging")
                        .font(.title3)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                    
                    Spacer(minLength: 40)
                    
                    // Login Form
                    VStack(spacing: 16) {
                        Text(isNewUser ? "Create Account" : "Login")
                            .font(.title2)
                            .fontWeight(.bold)
                        
                        // Nickname Field
                        HStack {
                            Image(systemName: "person")
                                .foregroundColor(.secondary)
                                .frame(width: 20)
                            
                            TextField("Enter your nickname", text: $nickname)
                                .textFieldStyle(PlainTextFieldStyle())
                        }
                        .padding()
                        .background(Color(.systemGray6))
                        .cornerRadius(12)
                        
                        // Password Field
                        HStack {
                            Image(systemName: "lock")
                                .foregroundColor(.secondary)
                                .frame(width: 20)
                            
                            if showPassword {
                                TextField("Enter your password", text: $password)
                                    .textFieldStyle(PlainTextFieldStyle())
                            } else {
                                SecureField("Enter your password", text: $password)
                                    .textFieldStyle(PlainTextFieldStyle())
                            }
                            
                            Button(action: { showPassword.toggle() }) {
                                Image(systemName: showPassword ? "eye.slash" : "eye")
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding()
                        .background(Color(.systemGray6))
                        .cornerRadius(12)
                        
                        // Error Message
                        if !errorMessage.isEmpty {
                            Text(errorMessage)
                                .foregroundColor(.red)
                                .font(.caption)
                        }
                        
                        // Login/Create Button
                        Button(action: {
                            if nickname.isEmpty || password.isEmpty {
                                errorMessage = "Please fill in all fields"
                            } else {
                                isLoading = true
                                errorMessage = ""
                                
                                // Simulate login process
                                simulateLogin(nickname: nickname, password: password, isNewUser: isNewUser) { success, message in
                                    DispatchQueue.main.async {
                                        isLoading = false
                                        if success {
                                            onLoginSuccess()
                                        } else {
                                            errorMessage = message
                                        }
                                    }
                                }
                            }
                        }) {
                            HStack {
                                if isLoading {
                                    ProgressView()
                                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                        .scaleEffect(0.8)
                                } else {
                                    Text(isNewUser ? "Create Account" : "Login")
                                        .fontWeight(.medium)
                                }
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.blue)
                            .foregroundColor(.white)
                            .cornerRadius(12)
                        }
                        .disabled(isLoading)
                        
                        // Toggle New User/Existing User
                        Button(action: {
                            isNewUser.toggle()
                            errorMessage = ""
                        }) {
                            Text(isNewUser ? "Already have an account? Login" : "New user? Create account")
                                .foregroundColor(.blue)
                        }
                    }
                    .padding()
                    .background(Color(.systemBackground))
                    .cornerRadius(16)
                    .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 5)
                    
                    Spacer(minLength: 40)
                    
                    // Security Info
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Security Features")
                            .font(.headline)
                            .fontWeight(.medium)
                        
                        SecurityFeatureRow(
                            icon: "lock.shield",
                            title: "End-to-End Encryption",
                            description: "All messages are encrypted with your keys"
                        )
                        
                        SecurityFeatureRow(
                            icon: "person.crop.circle.badge.questionmark",
                            title: "Anonymous Communication",
                            description: "Your identity is protected with cryptographic hashes"
                        )
                        
                        SecurityFeatureRow(
                            icon: "network",
                            title: "Decentralized Network",
                            description: "No central servers can access your data"
                        )
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
                    
                    Spacer(minLength: 40)
                }
                .padding(.horizontal, 24)
            }
            .navigationBarHidden(true)
        }
    }
}

struct SecurityFeatureRow: View {
    let icon: String
    let title: String
    let description: String
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(.blue)
                .frame(width: 20)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
    }
}

// Simulate login process
private func simulateLogin(
    nickname: String,
    password: String,
    isNewUser: Bool,
    completion: @escaping (Bool, String) -> Void
) {
    DispatchQueue.global().asyncAfter(deadline: .now() + 2) {
        if isNewUser {
            // Simulate account creation
            if nickname.count < 3 {
                completion(false, "Nickname must be at least 3 characters")
            } else if password.count < 8 {
                completion(false, "Password must be at least 8 characters")
            } else {
                completion(true, "Account created successfully")
            }
        } else {
            // Simulate login
            if nickname == "test" && password == "password" {
                completion(true, "Login successful")
            } else {
                completion(false, "Invalid nickname or password")
            }
        }
    }
}

#Preview {
    LoginView(onLoginSuccess: {})
}
