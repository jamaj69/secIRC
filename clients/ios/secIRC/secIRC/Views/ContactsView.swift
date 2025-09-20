import SwiftUI

/**
 * Contacts View - Contact list and management
 * 
 * Displays list of contacts with online status and management options
 * Similar to WhatsApp's contacts tab with search and add contact functionality
 */
struct ContactsView: View {
    @State private var searchText = ""
    @State private var showingSearch = false
    
    // Sample contacts data - in real app this would come from ViewModel
    let contacts = [
        Contact(
            id: "1",
            nickname: "Alice",
            userHash: "a1b2c3d4e5f6g7h8",
            isOnline: true,
            lastSeen: Date().addingTimeInterval(-300),
            keyRotationCount: 5
        ),
        Contact(
            id: "2",
            nickname: "Bob",
            userHash: "b2c3d4e5f6g7h8i9",
            isOnline: false,
            lastSeen: Date().addingTimeInterval(-1800),
            keyRotationCount: 3
        ),
        Contact(
            id: "3",
            nickname: "Charlie",
            userHash: "c3d4e5f6g7h8i9j0",
            isOnline: true,
            lastSeen: Date().addingTimeInterval(-600),
            keyRotationCount: 7
        ),
        Contact(
            id: "4",
            nickname: "David",
            userHash: "d4e5f6g7h8i9j0k1",
            isOnline: false,
            lastSeen: Date().addingTimeInterval(-86400),
            keyRotationCount: 2
        ),
        Contact(
            id: "5",
            nickname: "Eve",
            userHash: "e5f6g7h8i9j0k1l2",
            isOnline: true,
            lastSeen: Date().addingTimeInterval(-120),
            keyRotationCount: 4
        )
    ]
    
    var filteredContacts: [Contact] {
        if searchText.isEmpty {
            return contacts
        } else {
            return contacts.filter { $0.nickname.localizedCaseInsensitiveContains(searchText) }
        }
    }
    
    var onlineContactsCount: Int {
        contacts.filter { $0.isOnline }.count
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
                
                // Online Status Summary
                OnlineStatusCard(
                    onlineCount: onlineContactsCount,
                    totalCount: contacts.count
                )
                .padding(.horizontal)
                .padding(.top, 8)
                
                // Contacts List
                List(filteredContacts) { contact in
                    ContactRow(contact: contact)
                        .listRowInsets(EdgeInsets(top: 4, leading: 16, bottom: 4, trailing: 16))
                }
                .listStyle(PlainListStyle())
            }
            .navigationTitle("Contacts")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack {
                        Button(action: { showingSearch.toggle() }) {
                            Image(systemName: showingSearch ? "xmark" : "magnifyingglass")
                        }
                        
                        Button(action: { /* Add contact */ }) {
                            Image(systemName: "person.badge.plus")
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

struct ContactRow: View {
    let contact: Contact
    
    var body: some View {
        HStack(spacing: 12) {
            // Avatar with online status
            ZStack {
                Circle()
                    .fill(Color.blue)
                    .frame(width: 56, height: 56)
                
                Image(systemName: "person")
                    .foregroundColor(.white)
                    .font(.title2)
                
                // Online status indicator
                if contact.isOnline {
                    Circle()
                        .fill(Color.green)
                        .frame(width: 16, height: 16)
                        .overlay(
                            Circle()
                                .stroke(Color.white, lineWidth: 2)
                        )
                        .offset(x: 20, y: 20)
                }
            }
            
            // Contact Info
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(contact.nickname)
                        .font(.headline)
                        .fontWeight(.medium)
                        .lineLimit(1)
                    
                    Spacer()
                    
                    if contact.isOnline {
                        Text("Online")
                            .font(.caption)
                            .foregroundColor(.green)
                            .fontWeight(.medium)
                    }
                }
                
                Text("Hash: \(String(contact.userHash.prefix(8)))...")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(1)
                
                HStack {
                    Text(contact.isOnline ? "Active now" : "Last seen \(formatLastSeen(contact.lastSeen))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    Text("Keys: \(contact.keyRotationCount)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.vertical, 8)
        .contentShape(Rectangle())
        .onTapGesture {
            // Navigate to contact details or start chat
        }
    }
}

struct OnlineStatusCard: View {
    let onlineCount: Int
    let totalCount: Int
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Online Contacts")
                    .font(.headline)
                    .fontWeight(.medium)
                
                Text("\(onlineCount) of \(totalCount) contacts online")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Circle()
                .fill(Color.blue)
                .frame(width: 12, height: 12)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

struct Contact: Identifiable {
    let id: String
    let nickname: String
    let userHash: String
    let isOnline: Bool
    let lastSeen: Date
    let keyRotationCount: Int
}

func formatLastSeen(_ date: Date) -> String {
    let now = Date()
    let timeInterval = now.timeIntervalSince(date)
    
    if timeInterval < 60 {
        return "just now"
    } else if timeInterval < 3600 {
        return "\(Int(timeInterval / 60)) minutes ago"
    } else if timeInterval < 86400 {
        return "\(Int(timeInterval / 3600)) hours ago"
    } else if timeInterval < 604800 {
        return "\(Int(timeInterval / 86400)) days ago"
    } else {
        return "a long time ago"
    }
}

#Preview {
    ContactsView()
}
