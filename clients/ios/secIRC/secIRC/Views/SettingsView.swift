import SwiftUI

/**
 * Settings View - App settings and profile management
 * 
 * Displays user profile, app settings, and security options
 * Similar to WhatsApp's settings screen with profile and preferences
 */
struct SettingsView: View {
    @State private var showingLogoutAlert = false
    
    // Sample user data - in real app this would come from ViewModel
    let userProfile = UserProfile(
        nickname: "Alice",
        userHash: "a1b2c3d4e5f6g7h8",
        isOnline: true,
        keyRotationCount: 5,
        lastKeyRotation: Date().addingTimeInterval(-3600)
    )
    
    let settingsSections = [
        SettingsSection(
            title: "Account",
            items: [
                SettingsItem("Profile", "Manage your profile information", "person"),
                SettingsItem("Privacy", "Control your privacy settings", "hand.raised"),
                SettingsItem("Security", "Manage security and encryption", "lock.shield"),
                SettingsItem("Keys", "Manage your encryption keys", "key")
            ]
        ),
        SettingsSection(
            title: "App",
            items: [
                SettingsItem("Notifications", "Configure notification settings", "bell"),
                SettingsItem("Appearance", "Customize app appearance", "paintbrush"),
                SettingsItem("Storage", "Manage app storage and data", "internaldrive"),
                SettingsItem("About", "App information and version", "info.circle")
            ]
        ),
        SettingsSection(
            title: "Network",
            items: [
                SettingsItem("Relay Servers", "Manage relay server connections", "cloud"),
                SettingsItem("Discovery", "Configure server discovery", "magnifyingglass"),
                SettingsItem("Connection", "Network connection settings", "wifi")
            ]
        )
    ]
    
    var body: some View {
        NavigationView {
            List {
                // User Profile Section
                Section {
                    UserProfileCard(userProfile: userProfile)
                }
                .listRowInsets(EdgeInsets())
                .listRowBackground(Color.clear)
                
                // Settings Sections
                ForEach(settingsSections, id: \.title) { section in
                    Section(section.title) {
                        ForEach(section.items, id: \.title) { item in
                            SettingsItemRow(item: item)
                        }
                    }
                }
                
                // Logout Section
                Section {
                    Button(action: { showingLogoutAlert = true }) {
                        HStack {
                            Image(systemName: "rectangle.portrait.and.arrow.right")
                                .foregroundColor(.red)
                                .frame(width: 24, height: 24)
                            
                            Text("Logout")
                                .foregroundColor(.red)
                                .fontWeight(.medium)
                            
                            Spacer()
                        }
                    }
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.large)
            .alert("Logout", isPresented: $showingLogoutAlert) {
                Button("Cancel", role: .cancel) { }
                Button("Logout", role: .destructive) {
                    // Handle logout
                }
            } message: {
                Text("Are you sure you want to logout? You will need to enter your password again to access your messages.")
            }
        }
    }
}

struct UserProfileCard: View {
    let userProfile: UserProfile
    
    var body: some View {
        VStack(spacing: 16) {
            // Avatar
            Circle()
                .fill(Color.blue)
                .frame(width: 80, height: 80)
                .overlay(
                    Image(systemName: "person")
                        .foregroundColor(.white)
                        .font(.title)
                )
            
            // User Info
            VStack(spacing: 4) {
                Text(userProfile.nickname)
                    .font(.title2)
                    .fontWeight(.bold)
                
                Text("Hash: \(String(userProfile.userHash.prefix(8)))...")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            // Status
            HStack(spacing: 8) {
                Circle()
                    .fill(userProfile.isOnline ? Color.green : Color.gray)
                    .frame(width: 8, height: 8)
                
                Text(userProfile.isOnline ? "Online" : "Offline")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            // Edit Profile Button
            Button(action: { /* Edit profile */ }) {
                HStack {
                    Image(systemName: "pencil")
                    Text("Edit Profile")
                }
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundColor(.blue)
                .padding(.horizontal, 24)
                .padding(.vertical, 8)
                .overlay(
                    RoundedRectangle(cornerRadius: 20)
                        .stroke(Color.blue, lineWidth: 1)
                )
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 20)
        .background(Color(.systemGray6))
        .cornerRadius(12)
        .padding(.horizontal, 16)
    }
}

struct SettingsItemRow: View {
    let item: SettingsItem
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: item.icon)
                .foregroundColor(.blue)
                .frame(width: 24, height: 24)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(item.title)
                    .font(.body)
                    .fontWeight(.medium)
                
                if !item.description.isEmpty {
                    Text(item.description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .foregroundColor(.secondary)
                .font(.caption)
        }
        .padding(.vertical, 4)
        .contentShape(Rectangle())
        .onTapGesture {
            // Handle settings item tap
            handleSettingsItemTap(item)
        }
    }
    
    private func handleSettingsItemTap(_ item: SettingsItem) {
        switch item.title {
        case "Profile":
            // Navigate to profile
            break
        case "Privacy":
            // Navigate to privacy
            break
        case "Security":
            // Navigate to security
            break
        case "Keys":
            // Navigate to keys
            break
        case "Notifications":
            // Navigate to notifications
            break
        case "Appearance":
            // Navigate to appearance
            break
        case "Storage":
            // Navigate to storage
            break
        case "About":
            // Navigate to about
            break
        case "Relay Servers":
            // Navigate to relay servers
            break
        case "Discovery":
            // Navigate to discovery
            break
        case "Connection":
            // Navigate to connection
            break
        default:
            break
        }
    }
}

struct UserProfile {
    let nickname: String
    let userHash: String
    let isOnline: Bool
    let keyRotationCount: Int
    let lastKeyRotation: Date
}

struct SettingsSection {
    let title: String
    let items: [SettingsItem]
}

struct SettingsItem {
    let title: String
    let description: String
    let icon: String
}

#Preview {
    SettingsView()
}
