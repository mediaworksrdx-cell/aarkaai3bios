import SwiftUI
import MarkdownUI

struct ChatBubble: View {
    let text: String
    let isUser: Bool
    let isLoading: Bool
    
    @Environment(\.colorScheme) var colorScheme
    
    var body: some View {
        HStack {
            if isUser { Spacer() }
            
            VStack(alignment: isUser ? .trailing : .leading, spacing: 4) {
                if !isUser {
                    HStack(spacing: 8) {
                        Circle()
                            .fill(AppTheme.primary)
                            .frame(width: 24, height: 24)
                            .overlay(Text("A").font(.caption).bold().foregroundColor(.white))
                        
                        Text("Aarkaai")
                            .font(.caption)
                            .fontWeight(.medium)
                            .foregroundColor(colorScheme == .dark ? AppTheme.textSecondaryDark : AppTheme.textSecondaryLight)
                    }
                }
                
                Group {
                    if isLoading {
                        typingIndicator
                    } else if isUser {
                        Text(text)
                            .font(.body)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 12)
                            .background(colorScheme == .dark ? AppTheme.userBubbleDark : AppTheme.userBubbleLight)
                            .clipShape(bubbleShape(forUser: true))
                    } else {
                        Markdown(text)
                            .markdownTheme(.gitHub)
                            .font(.body)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 12)
                            .background(Color.clear)
                            .clipShape(bubbleShape(forUser: false))
                    }
                }
                .foregroundColor(colorScheme == .dark ? AppTheme.textPrimaryDark : AppTheme.textPrimaryLight)
            }
            
            if !isUser { Spacer() }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 4)
    }
    
    private func bubbleShape(forUser: Bool) -> RoundedCornerShape {
        if forUser {
            return RoundedCornerShape(radius: 20, corners: [.topLeft, .topRight, .bottomLeft])
        } else {
            return RoundedCornerShape(radius: 20, corners: [.topLeft, .topRight, .bottomRight])
        }
    }
    
    private var typingIndicator: some View {
        HStack(spacing: 4) {
            DotView(delay: 0)
            DotView(delay: 0.2)
            DotView(delay: 0.4)
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 16)
    }
}

// MARK: - Helpers

struct DotView: View {
    @State private var scale: CGFloat = 0.5
    let delay: Double
    
    var body: some View {
        Circle()
            .fill(AppTheme.primary)
            .frame(width: 6, height: 6)
            .scaleEffect(scale)
            .onAppear {
                withAnimation(Animation.easeInOut(duration: 0.6).repeatForever().delay(delay)) {
                    scale = 1.0
                }
            }
    }
}

struct RoundedCornerShape: Shape {
    var radius: CGFloat = .infinity
    var corners: UIRectCorner = .allCorners

    func path(in rect: CGRect) -> Path {
        let path = UIBezierPath(roundedRect: rect, byRoundingCorners: corners, cornerRadii: CGSize(width: radius, height: radius))
        return Path(path.cgPath)
    }
}
