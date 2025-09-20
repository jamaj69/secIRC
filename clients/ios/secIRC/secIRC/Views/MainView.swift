import SwiftUI

/**
 * Main View with Tab Navigation
 * 
 * Provides navigation between Chats, Groups, Contacts, and Settings screens
 * Similar to WhatsApp's main interface with tab navigation
 */
struct MainView: View {
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            ChatsView()
                .tabItem {
                    Image(systemName: "message")
                    Text("Chats")
                }
                .tag(0)
            
            GroupsView()
                .tabItem {
                    Image(systemName: "person.3")
                    Text("Groups")
                }
                .tag(1)
            
            ContactsView()
                .tabItem {
                    Image(systemName: "person.2")
                    Text("Contacts")
                }
                .tag(2)
            
            SettingsView()
                .tabItem {
                    Image(systemName: "gear")
                    Text("Settings")
                }
                .tag(3)
        }
        .accentColor(.blue)
    }
}

#Preview {
    MainView()
}
