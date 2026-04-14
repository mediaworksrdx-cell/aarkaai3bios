import SwiftUI
import Combine

class Message: Identifiable, ObservableObject, Equatable {
    let id = UUID()
    @Published var text: String
    let isUser: Bool
    @Published var isLoading: Bool = false
    @Published var isError: Bool = false
    @Published var responseDetails: PromptResponse? = nil
    @Published var rlhfRating: Int? = nil 

    init(text: String, isUser: Bool, isLoading: Bool = false, isError: Bool = false, responseDetails: PromptResponse? = nil, rlhfRating: Int? = nil) {
        self.text = text
        self.isUser = isUser
        self.isLoading = isLoading
        self.isError = isError
        self.responseDetails = responseDetails
        self.rlhfRating = rlhfRating
    }

    static func == (lhs: Message, rhs: Message) -> Bool {
        lhs.id == rhs.id && lhs.text == rhs.text && lhs.rlhfRating == rhs.rlhfRating
    }
}

struct Conversation: Identifiable, Equatable {
    let id = UUID()
    var title: String = "New Chat"
    var messages: [Message] = []
    let createdAt = Date()
}

@MainActor
class ChatViewModel: ObservableObject {
    @Published var conversations: [Conversation] = [Conversation()]
    @Published var activeConversationId: UUID
    @Published var isTyping: Bool = false
    
    private var token: String = ""
    private let appSession: AppSession
    
    init(appSession: AppSession) {
        self.appSession = appSession
        self.activeConversationId = conversations[0].id
        if let token = appSession.currentUserToken {
            self.token = token
        }
    }
    
    var activeConversation: Conversation {
        conversations.first(where: { $0.id == activeConversationId }) ?? conversations[0]
    }
    
    func selectConversation(_ id: UUID) {
        activeConversationId = id
    }
    
    func createNewChat() {
        let newConv = Conversation()
        conversations.append(newConv)
        activeConversationId = newConv.id
    }
    
    func sendMessage(_ query: String) async {
        guard !query.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        
        // 1. Add user message
        addMessage(Message(text: query, isUser: true))
        
        // 2. Add loading placeholder
        let loadingId = addMessage(Message(text: "", isUser: false, isLoading: true))
        
        // 3. Auto-title from first message
        if activeConversation.messages.filter({ $0.isUser }).count == 1 {
            updateTitle(query)
        }
        
        isTyping = true
        
        do {
            let req = PromptRequest(query: query)
            let token = appSession.currentUserToken ?? ""
            
            // Initial AI message (empty)
            let aiMessage = Message(text: "", isUser: false, isLoading: false)
            replaceMessage(id: loadingId, with: aiMessage)
            
            let stream = AarkaaiAPI.shared.streamPrompt(token: token, request: req)
            
            for try await chunk in stream {
                aiMessage.text += chunk
                // Force UI update for the conversation
                objectWillChange.send()
            }
            
        } catch {
            replaceMessage(id: loadingId, with: Message(
                text: "⚠️ Connection failed. Is the backend running?",
                isUser: false,
                isError: true
            ))
        }
        
        isTyping = false
    }
    
    func submitRLHF(messageId: UUID, rating: Int) async {
        // Optimistic UI update
        updateMessageRating(id: messageId, rating: rating)
        
        do {
            let req = RLHFRequest(user_id: appSession.currentUserId ?? "ios_user", rating: rating)
            _ = try await AarkaaiAPI.shared.submitRLHF(token: appSession.currentUserToken ?? "", request: req)
        } catch {
            print("RLHF fail: \(error)")
        }
    }
    
    // MARK: - Helpers
    
    @discardableResult
    private func addMessage(_ msg: Message) -> UUID {
        if let index = conversations.firstIndex(where: { $0.id == activeConversationId }) {
            conversations[index].messages.append(msg)
            return msg.id
        }
        return UUID()
    }
    
    private func replaceMessage(id: UUID, with newMsg: Message) {
        if let cIdx = conversations.firstIndex(where: { $0.id == activeConversationId }) {
            if let mIdx = conversations[cIdx].messages.firstIndex(where: { $0.id == id }) {
                conversations[cIdx].messages[mIdx] = newMsg
            }
        }
    }
    
    private func updateTitle(_ query: String) {
        if let index = conversations.firstIndex(where: { $0.id == activeConversationId }) {
            let limit = 40
            let title = query.count > limit ? String(query.prefix(limit)) + "..." : query
            conversations[index].title = title
        }
    }
    
    private func updateMessageRating(id: UUID, rating: Int) {
        if let cIdx = conversations.firstIndex(where: { $0.id == activeConversationId }) {
            if let mIdx = conversations[cIdx].messages.firstIndex(where: { $0.id == id }) {
                conversations[cIdx].messages[mIdx].rlhfRating = rating
            }
        }
    }
}
