import SwiftUI

/**
 * Chat View - Individual chat conversation
 * 
 * Displays messages in a conversation with a contact or group
 * Similar to WhatsApp's chat interface with message bubbles
 */
struct ChatView: View {
    let chatId: String
    let chatName: String
    @State private var messageText = ""
    @State private var messages: [Message] = []
    
    // Sample messages - in real app this would come from ViewModel
    let sampleMessages = [
        Message(
            id: "1",
            content: "Hey! How are you doing?",
            timestamp: Date().addingTimeInterval(-3600),
            isFromMe: false,
            senderName: "Alice",
            messageType: .text
        ),
        Message(
            id: "2",
            content: "I'm doing great! Thanks for asking. How about you?",
            timestamp: Date().addingTimeInterval(-3500),
            isFromMe: true,
            senderName: "Me",
            messageType: .text
        ),
        Message(
            id: "3",
            content: "I'm good too! Just working on some new projects.",
            timestamp: Date().addingTimeInterval(-3400),
            isFromMe: false,
            senderName: "Alice",
            messageType: .text
        ),
        Message(
            id: "4",
            content: "That sounds exciting! What kind of projects?",
            timestamp: Date().addingTimeInterval(-3300),
            isFromMe: true,
            senderName: "Me",
            messageType: .text
        ),
        Message(
            id: "5",
            content: "I'm working on a secure messaging app. It's quite challenging but fun!",
            timestamp: Date().addingTimeInterval(-3200),
            isFromMe: false,
            senderName: "Alice",
            messageType: .text
        )
    ]
    
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

struct MessageInputView: View {
    @Binding var messageText: String
    let onSendMessage: () -> Void
    
    var body: some View {
        HStack(spacing: 12) {
            // Attachment button
            Button(action: { /* Show attachment options */ }) {
                Image(systemName: "paperclip")
                    .font(.title2)
                    .foregroundColor(.blue)
            }
            
            // Message input field
            HStack {
                TextField("Type a message...", text: $messageText, axis: .vertical)
                    .textFieldStyle(PlainTextFieldStyle())
                    .lineLimit(1...4)
                
                if !messageText.isEmpty {
                    Button(action: onSendMessage) {
                        Image(systemName: "arrow.up.circle.fill")
                            .font(.title2)
                            .foregroundColor(.blue)
                    }
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color(.systemGray6))
            .cornerRadius(20)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .background(Color(.systemBackground))
    }
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

func formatMessageTime(_ date: Date) -> String {
    let now = Date()
    let timeInterval = now.timeIntervalSince(date)
    
    if timeInterval < 60 {
        return "now"
    } else if timeInterval < 3600 {
        let formatter = DateFormatter()
        formatter.dateFormat = "mm:ss"
        return formatter.string(from: date)
    } else if timeInterval < 86400 {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: date)
    } else {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMM dd, HH:mm"
        return formatter.string(from: date)
    }
}

// Custom corner radius modifier
struct CornerRadiusModifier: ViewModifier {
    let radius: CGFloat
    let corners: UIRectCorner
    
    func body(content: Content) -> some View {
        content
            .clipShape(RoundedCorner(radius: radius, corners: corners))
    }
}

struct RoundedCorner: Shape {
    let radius: CGFloat
    let corners: UIRectCorner
    
    func path(in rect: CGRect) -> Path {
        let path = UIBezierPath(
            roundedRect: rect,
            byRoundingCorners: corners,
            cornerRadii: CGSize(width: radius, height: radius)
        )
        return Path(path.cgPath)
    }
}

#Preview {
    NavigationView {
        ChatView(chatId: "1", chatName: "Alice")
    }
}
