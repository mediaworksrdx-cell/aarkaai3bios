import SwiftUI

struct PillInputBar: View {
    @Binding var text: String
    var isTyping: Bool
    var onSend: () -> Void
    
    @Environment(\.colorScheme) var colorScheme
    @FocusState private var isFocused: Bool
    
    var body: some View {
        VStack(spacing: 0) {
            Divider()
            
            HStack(alignment: .bottom, spacing: 12) {
                HStack(alignment: .bottom, spacing: 8) {
                    TextField("Message Aarkaai...", text: $text, axis: .vertical)
                        .focused($isFocused)
                        .padding(.vertical, 10)
                        .padding(.horizontal, 16)
                        .lineLimit(1...6)
                        .font(.body)
                        .submitLabel(.send)
                        .onSubmit {
                            if !text.isEmpty && !isTyping {
                                onSend()
                            }
                        }
                    
                    if !text.isEmpty {
                        Button(action: onSend) {
                            Image(systemName: "arrow.up.circle.fill")
                                .font(.system(size: 32))
                                .foregroundColor(isTyping ? .gray : AppTheme.primary)
                        }
                        .padding(.bottom, 6)
                        .padding(.trailing, 6)
                        .disabled(isTyping)
                    }
                }
                .background(
                    RoundedRectangle(cornerRadius: 24)
                        .stroke(colorScheme == .dark ? AppTheme.inputBorderDark : AppTheme.inputBorderLight, lineWidth: 1)
                        .background(colorScheme == .dark ? AppTheme.surfaceDark : AppTheme.surfaceLight)
                )
                .clipShape(RoundedRectangle(cornerRadius: 24))
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(colorScheme == .dark ? AppTheme.bgDark : AppTheme.bgLight)
        }
    }
}

// MARK: - Theme Extensions for Input

extension AppTheme {
    static let inputBorderLight = Color(hex: "E0DCD8")
    static let inputBorderDark = Color(hex: "444444")
}
