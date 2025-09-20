import SwiftUI

/**
 * Groups View - Group list and management
 * 
 * Displays list of groups with member count and last activity
 * Similar to WhatsApp's groups tab with create group functionality
 */
struct GroupsView: View {
    @State private var searchText = ""
    @State private var showingSearch = false
    
    // Sample groups data - in real app this would come from ViewModel
    let groups = [
        Group(
            id: "1",
            name: "Secure Group",
            description: "Private group for secure communication",
            memberCount: 5,
            lastActivity: Date().addingTimeInterval(-300),
            isPrivate: true,
            isOwner: true,
            unreadCount: 3
        ),
        Group(
            id: "2",
            name: "Project Team",
            description: "Team collaboration group",
            memberCount: 8,
            lastActivity: Date().addingTimeInterval(-1800),
            isPrivate: false,
            isOwner: false,
            unreadCount: 0
        ),
        Group(
            id: "3",
            name: "Friends",
            description: "Close friends group",
            memberCount: 12,
            lastActivity: Date().addingTimeInterval(-3600),
            isPrivate: true,
            isOwner: false,
            unreadCount: 7
        ),
        Group(
            id: "4",
            name: "Study Group",
            description: "Study and homework help",
            memberCount: 6,
            lastActivity: Date().addingTimeInterval(-86400),
            isPrivate: false,
            isOwner: true,
            unreadCount: 0
        )
    ]
    
    var filteredGroups: [Group] {
        if searchText.isEmpty {
            return groups
        } else {
            return groups.filter { $0.name.localizedCaseInsensitiveContains(searchText) }
        }
    }
    
    var ownedGroupsCount: Int {
        groups.filter { $0.isOwner }.count
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
                
                // Groups Summary
                GroupsSummaryCard(
                    totalGroups: groups.count,
                    ownedGroups: ownedGroupsCount
                )
                .padding(.horizontal)
                .padding(.top, 8)
                
                // Groups List
                List(filteredGroups) { group in
                    GroupRow(group: group)
                        .listRowInsets(EdgeInsets(top: 4, leading: 16, bottom: 4, trailing: 16))
                }
                .listStyle(PlainListStyle())
            }
            .navigationTitle("Groups")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack {
                        Button(action: { showingSearch.toggle() }) {
                            Image(systemName: showingSearch ? "xmark" : "magnifyingglass")
                        }
                        
                        Button(action: { /* Create group */ }) {
                            Image(systemName: "person.3.badge.plus")
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

struct GroupRow: View {
    let group: Group
    
    var body: some View {
        HStack(spacing: 12) {
            // Group Avatar with privacy indicator
            ZStack {
                Circle()
                    .fill(Color.green)
                    .frame(width: 56, height: 56)
                
                Image(systemName: "person.3")
                    .foregroundColor(.white)
                    .font(.title2)
                
                // Privacy indicator
                Circle()
                    .fill(group.isPrivate ? Color.blue : Color.gray)
                    .frame(width: 16, height: 16)
                    .overlay(
                        Image(systemName: group.isPrivate ? "lock.fill" : "globe")
                            .foregroundColor(.white)
                            .font(.caption2)
                    )
                    .offset(x: 20, y: 20)
            }
            
            // Group Info
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(group.name)
                        .font(.headline)
                        .fontWeight(.medium)
                        .lineLimit(1)
                    
                    Spacer()
                    
                    if group.unreadCount > 0 {
                        Text(group.unreadCount > 99 ? "99+" : "\(group.unreadCount)")
                            .font(.caption)
                            .fontWeight(.medium)
                            .foregroundColor(.white)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.blue)
                            .clipShape(Capsule())
                    }
                }
                
                Text(group.description)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .lineLimit(1)
                
                HStack {
                    Text("\(group.memberCount) members")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    Text("Last activity \(formatLastActivity(group.lastActivity))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                if group.isOwner {
                    Text("You own this group")
                        .font(.caption)
                        .foregroundColor(.blue)
                        .fontWeight(.medium)
                }
            }
        }
        .padding(.vertical, 8)
        .contentShape(Rectangle())
        .onTapGesture {
            // Navigate to group chat
        }
    }
}

struct GroupsSummaryCard: View {
    let totalGroups: Int
    let ownedGroups: Int
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Your Groups")
                    .font(.headline)
                    .fontWeight(.medium)
                
                Text("\(totalGroups) groups • \(ownedGroups) owned")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Image(systemName: "person.3")
                .font(.title2)
                .foregroundColor(.blue)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

struct Group: Identifiable {
    let id: String
    let name: String
    let description: String
    let memberCount: Int
    let lastActivity: Date
    let isPrivate: Bool
    let isOwner: Bool
    let unreadCount: Int
}

func formatLastActivity(_ date: Date) -> String {
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
    GroupsView()
}
