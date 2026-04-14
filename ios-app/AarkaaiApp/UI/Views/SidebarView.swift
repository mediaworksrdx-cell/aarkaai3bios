import SwiftUI

struct SidebarView: View {
    let conversations: [Conversation]
    let activeId: UUID
    let onSelect: (UUID) -> Void
    let onNewChat: () -> Void
    let onLogout: () -> Void
    
    @Environment(\.colorScheme) var colorScheme
    
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // New Chat Button
            Button(action: onNewChat) {
                HStack {
                    Image(systemName: "plus")
                    Text("New Chat")
                    Spacer()
                }
                .padding()
                .background(AppTheme.primary)
                .foregroundColor(.white)
                .cornerRadius(12)
            }
            .padding(.top, 60)
            
            Text("Recents")
                .font(.caption)
                .fontWeight(.bold)
                .foregroundColor(.gray)
                .padding(.horizontal, 4)
            
            // Conversation List
            ScrollView {
                VStack(spacing: 4) {
                    ForEach(conversations.reversed()) { conversation in
                        let isActive = conversation.id == activeId
                        
                        Button(action: { onSelect(conversation.id) }) {
                            Text(conversation.title)
                                .font(.subheadline)
                                .fontWeight(isActive ? .semibold : .regular)
                                .foregroundColor(isActive ? AppTheme.primary : (colorScheme == .dark ? .white : .black))
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.vertical, 12)
                                .padding(.horizontal, 16)
                                .background(isActive ? AppTheme.primary.opacity(0.1) : Color.clear)
                                .cornerRadius(8)
                        }
                    }
                }
            }
            
            Spacer()
            
            Divider()
            
            // Logout
            Button(action: onLogout) {
                HStack {
                    Image(systemName: "rectangle.portrait.and.arrow.right")
                    Text("Sign Out")
                    Spacer()
                }
                .foregroundColor(.red)
                .padding(.vertical, 12)
            }
        }
        .padding(.horizontal, 16)
        .background(colorScheme == .dark ? AppTheme.surfaceDark : AppTheme.surfaceLight)
    }
}
