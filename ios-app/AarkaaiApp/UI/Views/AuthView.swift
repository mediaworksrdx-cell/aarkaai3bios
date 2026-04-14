import SwiftUI

struct AuthView: View {
    @StateObject var viewModel: AuthViewModel
    @Environment(\.colorScheme) var colorScheme
    
    var body: some View {
        ZStack {
            // Background
            (colorScheme == .dark ? AppTheme.bgDark : AppTheme.bgLight)
                .ignoresSafeArea()
            
            VStack(spacing: 32) {
                // Header
                VStack(spacing: 12) {
                    Circle()
                        .fill(AppTheme.primary)
                        .frame(width: 80, height: 80)
                        .overlay(
                            Text("A")
                                .font(.system(size: 40, weight: .bold))
                                .foregroundColor(.white)
                        )
                    
                    Text("AARKAAI")
                        .font(.system(size: 28, weight: .bold, design: .rounded))
                        .letterSpacing(2)
                        .foregroundColor(colorScheme == .dark ? .white : AppTheme.textPrimaryLight)
                    
                    Text(viewModel.isLoginMode ? "Welcome back" : "Create your account")
                        .font(.subheadline)
                        .foregroundColor(colorScheme == .dark ? AppTheme.textSecondaryDark : AppTheme.textSecondaryLight)
                }
                .padding(.top, 40)
                
                // Form
                VStack(spacing: 20) {
                    if !viewModel.isLoginMode {
                        CustomTextField(title: "Name", text: $viewModel.name, icon: "person")
                    }
                    
                    CustomTextField(title: "Email", text: $viewModel.email, icon: "envelope")
                        .keyboardType(.emailAddress)
                        .textInputAutocapitalization(.never)
                    
                    CustomTextField(title: "Password", text: $viewModel.password, icon: "lock", isSecure: true)
                }
                .padding(.horizontal, 24)
                
                if let error = viewModel.errorMessage {
                    Text(error)
                        .font(.caption)
                        .foregroundColor(.red)
                        .padding(.horizontal)
                }
                
                // Actions
                VStack(spacing: 16) {
                    Button(action: {
                        Task { await viewModel.authenticate() }
                    }) {
                        if viewModel.isLoading {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        } else {
                            Text(viewModel.isLoginMode ? "Sign In" : "Sign Up")
                                .fontWeight(.bold)
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .frame(height: 56)
                    .background(AppTheme.primary)
                    .foregroundColor(.white)
                    .cornerRadius(16)
                    .disabled(viewModel.isLoading)
                    
                    Button(action: {
                        withAnimation {
                            viewModel.isLoginMode.toggle()
                            viewModel.errorMessage = nil
                        }
                    }) {
                        Text(viewModel.isLoginMode ? "Don't have an account? Sign Up" : "Already have an account? Sign In")
                            .font(.footnote)
                            .foregroundColor(AppTheme.primary)
                    }
                }
                .padding(.horizontal, 24)
                
                Spacer()
            }
        }
    }
}

// MARK: - Subviews

struct CustomTextField: View {
    let title: String
    @Binding var text: String
    let icon: String
    var isSecure: Bool = false
    
    @Environment(\.colorScheme) var colorScheme
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(AppTheme.primary)
                .frame(width: 20)
            
            if isSecure {
                SecureField(title, text: $text)
            } else {
                TextField(title, text: $text)
            }
        }
        .padding()
        .background(colorScheme == .dark ? AppTheme.surfaceDark : AppTheme.surfaceLight)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.gray.opacity(0.1), lineWidth: 1)
        )
    }
}
