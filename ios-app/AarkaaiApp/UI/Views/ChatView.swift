import SwiftUI

struct ChatView: View {
    @StateObject var viewModel: ChatViewModel
    @EnvironmentObject var appSession: AppSession
    @Environment(\.colorScheme) var colorScheme
    
    @State private var inputText: String = ""
    @State private var isSidebarOpen: Bool = false
    
    var body: some View {
        ZStack {
            // Main Content
            VStack(spacing: 0) {
                // Custom Top Bar
                HeaderView(
                    title: viewModel.activeConversation.title,
                    onMenuClick: { withAnimation { isSidebarOpen.toggle() } },
                    onNewChat: { viewModel.createNewChat() }
                )
                
                // Message List
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: 8) {
                            if viewModel.activeConversation.messages.isEmpty {
                                WelcomeView()
                            } else {
                                ForEach(viewModel.activeConversation.messages) { message in
                                    ChatBubble(
                                        text: message.text,
                                        isUser: message.isUser,
                                        isLoading: message.isLoading
                                    )
                                    .id(message.id)
                                    
                                    if !message.isUser && !message.isLoading && !message.isError {
                                        FeedbackRow(
                                            rating: message.rlhfRating,
                                            onRate: { rating in
                                                Task { await viewModel.submitRLHF(messageId: message.id, rating: rating) }
                                            }
                                        )
                                        .padding(.leading, 60)
                                        .padding(.bottom, 8)
                                    }
                                }
                            }
                        }
                        .padding(.vertical, 20)
                    }
                    .onChange(of: viewModel.activeConversation.messages) { _, messages in
                        if let lastMessage = messages.last {
                            withAnimation {
                                proxy.scrollTo(lastMessage.id, anchor: .bottom)
                            }
                        }
                    }
                }
                .background(colorScheme == .dark ? AppTheme.bgDark : AppTheme.bgLight)
                
                // Input Bar
                PillInputBar(
                    text: $inputText,
                    isTyping: viewModel.isTyping,
                    onSend: {
                        let query = inputText
                        inputText = ""
                        Task { await viewModel.sendMessage(query) }
                    }
                )
            }
            .blur(radius: isSidebarOpen ? 5 : 0)
            .disabled(isSidebarOpen)
            
            // Sidebar Drawer Overlay
            if isSidebarOpen {
                Color.black.opacity(0.3)
                    .ignoresSafeArea()
                    .onTapGesture { withAnimation { isSidebarOpen = false } }
                
                HStack(spacing: 0) {
                    SidebarView(
                        conversations: viewModel.conversations,
                        activeId: viewModel.activeConversationId,
                        onSelect: { id in
                            viewModel.selectConversation(id)
                            withAnimation { isSidebarOpen = false }
                        },
                        onNewChat: {
                            viewModel.createNewChat()
                            withAnimation { isSidebarOpen = false }
                        },
                        onLogout: {
                            appSession.logout()
                        }
                    )
                    .frame(width: 280)
                    .transition(.move(edge: .leading))
                    
                    Spacer()
                }
            }
        }
    }
}

// MARK: - Subviews

struct HeaderView: View {
    let title: String
    let onMenuClick: () -> Void
    let onNewChat: () -> Void
    
    @Environment(\.colorScheme) var colorScheme
    
    var body: some View {
        HStack {
            Button(action: onMenuClick) {
                Image(systemName: "line.3.horizontal")
                    .font(.title2)
                    .foregroundColor(colorScheme == .dark ? .white : .black)
            }
            
            Spacer()
            
            Text("AARKAAI")
                .font(.headline)
                .fontWeight(.bold)
                .tracking(1)
            
            Spacer()
            
            Button(action: onNewChat) {
                Image(systemName: "square.and.pencil")
                    .font(.title2)
                    .foregroundColor(colorScheme == .dark ? .white : .black)
            }
        }
        .padding()
        .background(colorScheme == .dark ? AppTheme.bgDark : AppTheme.bgLight)
    }
}

struct WelcomeView: View {
    var body: some View {
        VStack(spacing: 16) {
            Spacer(minLength: 100)
            
            Circle()
                .fill(AppTheme.primary.opacity(0.1))
                .frame(width: 64, height: 64)
                .overlay(
                    Text("AI")
                        .font(.headline)
                        .foregroundColor(AppTheme.primary)
                )
            
            Text("How can I help you?")
                .font(.title2)
                .fontWeight(.bold)
            
            Text("I'm Aarkaai, your advanced intelligent agent.")
                .font(.subheadline)
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 40)
            
            Spacer()
        }
    }
}

struct FeedbackRow: View {
    let rating: Int?
    let onRate: (Int) -> Void
    
    var body: some View {
        HStack(spacing: 16) {
            Button(action: { onRate(1) }) {
                Image(systemName: rating == 1 ? "hand.thumbsup.fill" : "hand.thumbsup")
                    .foregroundColor(rating == 1 ? AppTheme.primary : .gray)
            }
            
            Button(action: { onRate(-1) }) {
                Image(systemName: rating == -1 ? "hand.thumbsdown.fill" : "hand.thumbsdown")
                    .foregroundColor(rating == -1 ? .red : .gray)
            }
        }
    }
}
