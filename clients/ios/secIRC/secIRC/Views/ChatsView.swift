import SwiftUI

/**
 * Chats View - Main chat list similar to WhatsApp
 * 
 * Displays list of recent conversations with contacts and groups
 * Shows last message, timestamp, and unread count
 */
struct ChatsView: View {
    @State private var searchText = ""
    @State private var showingSearch = false
    
    // Sample chat data - in real app this would come from ViewModel
    let chats = [
        ChatItem(
            id: "1",
            name: "Alice",
            lastMessage: "Hey, how are you doing?",
            timestamp: Date().addingTimeInterval(-300), // 5 minutes ago
            unreadCount: 2,
            isOnline: true,
            isGroup: false
        ),
        ChatItem(
            id: "2",
            name: "Bob",
            lastMessage: "Thanks for the help!",
            timestamp: Date().addingTimeInterval(-1800), // 30 minutes ago
            unreadCount: 0,
            isOnline: false,
            isGroup: false
        ),
        ChatItem(
            id: "3",
            name: "Secure Group",
            lastMessage: "Charlie: Meeting at 3 PM",
            timestamp: Date().addingTimeInterval(-3600), // 1 hour ago
            unreadCount: 5,
            isOnline: false,
            isGroup: true
        ),
        ChatItem(
            id: "4",
            name: "David",
            lastMessage: "See you tomorrow",
            timestamp: Date().addingTimeInterval(-86400), // 1 day ago
            unreadCount: 0,
            isOnline: true,
            isGroup: false
        )
    ]
    
    var filteredChats: [ChatItem] {
        if searchText.isEmpty {
            return chats
        } else {
            return chats.filter { $0.name.localizedCaseInsensitiveContains(searchText) }
        }
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Search Bar
                if showingSearch {
                    SearchBar(text: $searchText)
                        .padding(.horizontal)
                        .padding(.top, 8)
                }
                
                // Chats List
                List(filteredChats) { chat in
                    ChatRow(chat: chat)
                        .listRowInsets(EdgeInsets(top: 4, leading: 16, bottom: 4, trailing: 16))
                }
                .listStyle(PlainListStyle())
            }
            .navigationTitle("secIRC")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack {
                        Button(action: { showingSearch.toggle() }) {
                            Image(systemName: showingSearch ? "xmark" : "magnifyingglass")
                        }
                        
                        Button(action: { /* New chat */ }) {
                            Image(systemName: "square.and.pencil")
                        }
                        
                        Button(action: { /* More options */ }) {
                            Image(systemName: "ellipsis")
                        }
                    }
                }
            }
        }
    }
}

struct ChatRow: View {
    let chat: ChatItem
    
    var body: some View {
        HStack(spacing: 12) {
            // Avatar
            ZStack {
                Circle()
                    .fill(chat.isGroup ? Color.green : Color.blue)
                    .frame(width: 56, height: 56)
                
                Image(systemName: chat.isGroup ? "person.3" : "person")
                    .foregroundColor(.white)
                    .font(.title2)
            }
            
            // Chat Info
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(chat.name)
                        .font(.headline)
                        .fontWeight(.medium)
                        .lineLimit(1)
                    
                    Spacer()
                    
                    Text(formatTimestamp(chat.timestamp))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                HStack {
                    Text(chat.lastMessage)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                    
                    Spacer()
                    
                    if chat.unreadCount > 0 {
                        Text(chat.unreadCount > 99 ? "99+" : "\(chat.unreadCount)")
                            .font(.caption)
                            .fontWeight(.medium)
                            .foregroundColor(.white)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.blue)
                            .clipShape(Capsule())
                    }
                }
            }
        }
        .padding(.vertical, 8)
        .contentShape(Rectangle())
        .onTapGesture {
            // Navigate to chat
        }
    }
}

struct SearchBar: View {
    @Binding var text: String
    
    var body: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.secondary)
            
            TextField("Search chats...", text: $text)
                .textFieldStyle(PlainTextFieldStyle())
            
            if !text.isEmpty {
                Button("Clear") {
                    text = ""
                }
                .foregroundColor(.blue)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color(.systemGray6))
        .cornerRadius(20)
    }
}

struct ChatItem: Identifiable {
    let id: String
    let name: String
    let lastMessage: String
    let timestamp: Date
    let unreadCount: Int
    let isOnline: Bool
    let isGroup: Bool
}

func formatTimestamp(_ date: Date) -> String {
    let now = Date()
    let timeInterval = now.timeIntervalSince(date)
    
    if timeInterval < 60 {
        return "now"
    } else if timeInterval < 3600 {
        return "\(Int(timeInterval / 60))m"
    } else if timeInterval < 86400 {
        return "\(Int(timeInterval / 3600))h"
    } else if timeInterval < 604800 {
        return "\(Int(timeInterval / 86400))d"
    } else {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMM dd"
        return formatter.string(from: date)
    }
}

#Preview {
    ChatsView()
}
