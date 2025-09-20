# secIRC Mobile UI Implementation

## Overview

This document describes the comprehensive mobile UI implementation for secIRC, featuring modern chat interfaces inspired by WhatsApp and IRC clients. The implementation includes both Android (Jetpack Compose) and iOS (SwiftUI) versions with consistent design patterns and user experience.

## 🎨 **Design Philosophy**

### **WhatsApp-Inspired Interface**
- **Familiar navigation patterns** with bottom tab navigation
- **Message bubbles** with sender/receiver distinction
- **Online status indicators** and last seen timestamps
- **Unread message counters** with badge notifications
- **Search functionality** across all screens

### **IRC Client Elements**
- **Nickname-based identification** for users
- **Channel/group management** similar to IRC channels
- **Real-time status updates** and presence indicators
- **Command-like interface** for advanced users

### **Security-Focused Design**
- **Encryption status indicators** throughout the interface
- **Key management visualization** with rotation tracking
- **Privacy controls** prominently displayed
- **Anonymous identity representation** using hashes

## 📱 **Android Implementation (Jetpack Compose)**

### **Theme and Styling**

#### **Color Palette**
```kotlin
// secIRC Color Palette
val SecIRCBlue = Color(0xFF1E88E5)
val SecIRCBlueDark = Color(0xFF1565C0)
val SecIRCGreen = Color(0xFF4CAF50)
val SecIRCGreenDark = Color(0xFF388E3C)
val SecIRCGray = Color(0xFF757575)
val SecIRCGrayLight = Color(0xFFE0E0E0)
val SecIRCGrayDark = Color(0xFF424242)
val SecIRCRed = Color(0xFFE53935)
```

#### **Typography System**
```kotlin
val SecIRCTypography = Typography(
    displayLarge = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Bold,
        fontSize = 57.sp,
        lineHeight = 64.sp,
        letterSpacing = (-0.25).sp,
    ),
    // ... additional text styles
)
```

### **Screen Architecture**

#### **Main Screen with Bottom Navigation**
```kotlin
@Composable
fun MainScreen(onNavigateToLogin: () -> Unit) {
    val navController = rememberNavController()
    
    Scaffold(
        bottomBar = {
            BottomNavigationBar(navController = navController)
        }
    ) { paddingValues ->
        NavHost(
            navController = navController,
            startDestination = "chats",
            modifier = Modifier.padding(paddingValues)
        ) {
            composable("chats") {
                ChatsScreen(navController = navController)
            }
            composable("groups") {
                GroupsScreen(navController = navController)
            }
            composable("contacts") {
                ContactsScreen(navController = navController)
            }
            composable("settings") {
                SettingsScreen(
                    navController = navController,
                    onNavigateToLogin = onNavigateToLogin
                )
            }
        }
    }
}
```

#### **Chats Screen - Main Conversation List**
```kotlin
@Composable
fun ChatsScreen(navController: NavController) {
    var searchQuery by remember { mutableStateOf("") }
    var showSearchBar by remember { mutableStateOf(false) }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        // Top App Bar with search functionality
        TopAppBar(
            title = {
                Text(
                    text = "secIRC",
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Bold
                )
            },
            actions = {
                IconButton(onClick = { showSearchBar = !showSearchBar }) {
                    Icon(
                        imageVector = if (showSearchBar) Icons.Default.Close else Icons.Default.Search,
                        contentDescription = if (showSearchBar) "Close Search" else "Search"
                    )
                }
                IconButton(onClick = { /* Navigate to new chat */ }) {
                    Icon(
                        imageVector = Icons.Default.Edit,
                        contentDescription = "New Chat"
                    )
                }
            }
        )
        
        // Search Bar
        if (showSearchBar) {
            SearchBar(
                query = searchQuery,
                onQueryChange = { searchQuery = it },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp)
            )
        }
        
        // Chats List
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(vertical = 8.dp)
        ) {
            items(filteredChats) { chat ->
                ChatItemRow(
                    chat = chat,
                    onClick = {
                        navController.navigate("chat/${chat.id}")
                    }
                )
            }
        }
    }
}
```

#### **Chat Screen - Individual Conversation**
```kotlin
@Composable
fun ChatScreen(
    navController: NavController,
    chatId: String,
    chatName: String
) {
    var messageText by remember { mutableStateOf("") }
    val listState = rememberLazyListState()
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        // Top App Bar
        TopAppBar(
            title = {
                Column {
                    Text(
                        text = chatName,
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Medium
                    )
                    Text(
                        text = "Online",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            },
            navigationIcon = {
                IconButton(onClick = { navController.popBackStack() }) {
                    Icon(
                        imageVector = Icons.Default.ArrowBack,
                        contentDescription = "Back"
                    )
                }
            },
            actions = {
                IconButton(onClick = { /* Video call */ }) {
                    Icon(
                        imageVector = Icons.Default.Videocam,
                        contentDescription = "Video Call"
                    )
                }
                IconButton(onClick = { /* Voice call */ }) {
                    Icon(
                        imageVector = Icons.Default.Call,
                        contentDescription = "Voice Call"
                    )
                }
            }
        )
        
        // Messages List
        LazyColumn(
            state = listState,
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(messages) { message ->
                MessageBubble(message = message)
            }
        }
        
        // Message Input
        MessageInput(
            messageText = messageText,
            onMessageTextChange = { messageText = it },
            onSendMessage = {
                if (messageText.isNotBlank()) {
                    // Send message logic here
                    messageText = ""
                }
            }
        )
    }
}
```

#### **Message Bubble Component**
```kotlin
@Composable
fun MessageBubble(message: Message) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (message.isFromMe) Arrangement.End else Arrangement.Start
    ) {
        if (!message.isFromMe) {
            // Avatar for received messages
            Box(
                modifier = Modifier
                    .size(32.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.primary),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Person,
                    contentDescription = "Avatar",
                    tint = MaterialTheme.colorScheme.onPrimary,
                    modifier = Modifier.size(16.dp)
                )
            }
            Spacer(modifier = Modifier.width(8.dp))
        }
        
        Column(
            horizontalAlignment = if (message.isFromMe) Alignment.End else Alignment.Start,
            modifier = Modifier.widthIn(max = 280.dp)
        ) {
            if (!message.isFromMe) {
                Text(
                    text = message.senderName,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(start = 16.dp, bottom = 2.dp)
                )
            }
            
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(
                    topStart = 16.dp,
                    topEnd = 16.dp,
                    bottomStart = if (message.isFromMe) 16.dp else 4.dp,
                    bottomEnd = if (message.isFromMe) 4.dp else 16.dp
                ),
                colors = CardDefaults.cardColors(
                    containerColor = if (message.isFromMe) 
                        MaterialTheme.colorScheme.primary 
                    else 
                        MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Text(
                    text = message.content,
                    style = MaterialTheme.typography.bodyMedium,
                    color = if (message.isFromMe) 
                        MaterialTheme.colorScheme.onPrimary 
                    else 
                        MaterialTheme.colorScheme.onSurface,
                    modifier = Modifier.padding(12.dp)
                )
            }
            
            Text(
                text = formatMessageTime(message.timestamp),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(
                    start = if (message.isFromMe) 0.dp else 16.dp,
                    end = if (message.isFromMe) 16.dp else 0.dp,
                    top = 2.dp
                )
            )
        }
        
        if (message.isFromMe) {
            Spacer(modifier = Modifier.width(8.dp))
            // Avatar for sent messages
            Box(
                modifier = Modifier
                    .size(32.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.secondary),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Person,
                    contentDescription = "Avatar",
                    tint = MaterialTheme.colorScheme.onSecondary,
                    modifier = Modifier.size(16.dp)
                )
            }
        }
    }
}
```

### **Data Models**

#### **Chat Item**
```kotlin
data class ChatItem(
    val id: String,
    val name: String,
    val lastMessage: String,
    val timestamp: Long,
    val unreadCount: Int,
    val isOnline: Boolean,
    val isGroup: Boolean,
    val avatar: String? = null
)
```

#### **Message**
```kotlin
data class Message(
    val id: String,
    val content: String,
    val timestamp: Long,
    val isFromMe: Boolean,
    val senderName: String,
    val messageType: MessageType
)

enum class MessageType {
    TEXT, IMAGE, FILE, VOICE
}
```

## 🍎 **iOS Implementation (SwiftUI)**

### **Main View with Tab Navigation**
```swift
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
```

### **Chats View - Main Conversation List**
```swift
struct ChatsView: View {
    @State private var searchText = ""
    @State private var showingSearch = false
    
    let chats = [
        ChatItem(
            id: "1",
            name: "Alice",
            lastMessage: "Hey, how are you doing?",
            timestamp: Date().addingTimeInterval(-300),
            unreadCount: 2,
            isOnline: true,
            isGroup: false
        ),
        // ... more sample data
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
```

### **Chat View - Individual Conversation**
```swift
struct ChatView: View {
    let chatId: String
    let chatName: String
    @State private var messageText = ""
    @State private var messages: [Message] = []
    
    var body: some View {
        VStack(spacing: 0) {
            // Messages List
            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(messages) { message in
                        MessageBubble(message: message)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
            }
            .onAppear {
                messages = sampleMessages
            }
            
            // Message Input
            MessageInputView(
                messageText: $messageText,
                onSendMessage: {
                    if !messageText.isEmpty {
                        let newMessage = Message(
                            id: UUID().uuidString,
                            content: messageText,
                            timestamp: Date(),
                            isFromMe: true,
                            senderName: "Me",
                            messageType: .text
                        )
                        messages.append(newMessage)
                        messageText = ""
                    }
                }
            )
        }
        .navigationTitle(chatName)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button("Back") {
                    // Navigate back
                }
            }
            
            ToolbarItem(placement: .navigationBarTrailing) {
                HStack {
                    Button(action: { /* Video call */ }) {
                        Image(systemName: "video")
                    }
                    
                    Button(action: { /* Voice call */ }) {
                        Image(systemName: "phone")
                    }
                    
                    Button(action: { /* More options */ }) {
                        Image(systemName: "ellipsis")
                    }
                }
            }
        }
    }
}
```

### **Message Bubble Component**
```swift
struct MessageBubble: View {
    let message: Message
    
    var body: some View {
        HStack {
            if message.isFromMe {
                Spacer()
            }
            
            VStack(alignment: message.isFromMe ? .trailing : .leading, spacing: 4) {
                if !message.isFromMe {
                    Text(message.senderName)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.leading, 16)
                }
                
                HStack {
                    if !message.isFromMe {
                        // Avatar for received messages
                        Circle()
                            .fill(Color.blue)
                            .frame(width: 32, height: 32)
                            .overlay(
                                Image(systemName: "person")
                                    .foregroundColor(.white)
                                    .font(.caption)
                            )
                    }
                    
                    Text(message.content)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)
                        .background(
                            message.isFromMe ? Color.blue : Color(.systemGray5)
                        )
                        .foregroundColor(
                            message.isFromMe ? .white : .primary
                        )
                        .clipShape(
                            RoundedRectangle(cornerRadius: 16)
                                .modifier(
                                    CornerRadiusModifier(
                                        radius: 16,
                                        corners: message.isFromMe ? 
                                            [.topLeft, .topRight, .bottomLeft] : 
                                            [.topLeft, .topRight, .bottomRight]
                                    )
                                )
                        )
                    
                    if message.isFromMe {
                        // Avatar for sent messages
                        Circle()
                            .fill(Color.gray)
                            .frame(width: 32, height: 32)
                            .overlay(
                                Image(systemName: "person")
                                    .foregroundColor(.white)
                                    .font(.caption)
                            )
                    }
                }
                
                Text(formatMessageTime(message.timestamp))
                    .font(.caption2)
                    .foregroundColor(.secondary)
                    .padding(.horizontal, message.isFromMe ? 0 : 16)
            }
            
            if !message.isFromMe {
                Spacer()
            }
        }
    }
}
```

### **Data Models**
```swift
struct ChatItem: Identifiable {
    let id: String
    let name: String
    let lastMessage: String
    let timestamp: Date
    let unreadCount: Int
    let isOnline: Bool
    let isGroup: Bool
}

struct Message: Identifiable {
    let id: String
    let content: String
    let timestamp: Date
    let isFromMe: Bool
    let senderName: String
    let messageType: MessageType
}

enum MessageType {
    case text, image, file, voice
}
```

## 🔐 **Security-Focused UI Elements**

### **Encryption Status Indicators**
- **Lock icons** next to encrypted messages
- **Key rotation notifications** in settings
- **Security badges** on contacts and groups
- **Encryption strength indicators** in profile

### **Privacy Controls**
- **Anonymous identity display** using hash prefixes
- **Online status toggles** for privacy
- **Message deletion options** with confirmation
- **Key management interface** with rotation controls

### **Trust Indicators**
- **Relay server status** in network settings
- **Connection security badges** in chat headers
- **Verification status** for contacts
- **Network health indicators** in status bar

## 🎯 **User Experience Features**

### **Navigation Patterns**
- **Bottom tab navigation** for main sections
- **Back navigation** with proper state management
- **Deep linking** support for direct chat access
- **Gesture navigation** for message actions

### **Search and Discovery**
- **Global search** across chats, contacts, and groups
- **Filter options** by type, status, and date
- **Recent searches** with quick access
- **Smart suggestions** based on usage patterns

### **Real-time Updates**
- **Live typing indicators** in chat
- **Online status updates** with smooth transitions
- **Message delivery status** with read receipts
- **Connection status** with automatic reconnection

### **Accessibility**
- **Screen reader support** with proper labels
- **High contrast mode** for better visibility
- **Large text support** with dynamic sizing
- **Voice control** for hands-free operation

## 📊 **Performance Optimizations**

### **Android Optimizations**
- **LazyColumn** for efficient list rendering
- **Remember** for state preservation
- **CompositionLocal** for theme and context
- **Modifier reuse** for consistent styling

### **iOS Optimizations**
- **LazyVStack** for efficient vertical layouts
- **@State** and **@Binding** for reactive updates
- **ViewModifier** for reusable styling
- **AsyncImage** for efficient image loading

## 🧪 **Testing and Quality Assurance**

### **UI Testing**
- **Screenshot testing** for visual regression
- **Accessibility testing** with automated tools
- **Performance testing** for smooth animations
- **Cross-device testing** for consistency

### **User Testing**
- **Usability testing** with real users
- **A/B testing** for feature optimization
- **Beta testing** with community feedback
- **Accessibility testing** with disabled users

## 🚀 **Future Enhancements**

### **Advanced Features**
- **Voice messages** with waveform visualization
- **File sharing** with progress indicators
- **Video calls** with end-to-end encryption
- **Screen sharing** for collaboration

### **Customization**
- **Theme customization** with user preferences
- **Layout options** for different screen sizes
- **Gesture customization** for power users
- **Plugin system** for extensibility

### **Integration**
- **System notifications** with rich content
- **Share extensions** for content sharing
- **Widget support** for quick access
- **Siri integration** for voice commands

---

This comprehensive UI implementation provides a modern, secure, and user-friendly interface for the secIRC anonymous messaging system, combining the best aspects of popular chat applications with the security requirements of anonymous communication! 🚀📱🔐
