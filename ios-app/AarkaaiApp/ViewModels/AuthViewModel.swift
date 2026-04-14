import SwiftUI

@MainActor
class AuthViewModel: ObservableObject {
    @Published var email = ""
    @Published var password = ""
    @Published var name = ""
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var isLoginMode = true
    
    private let appSession: AppSession
    
    init(appSession: AppSession) {
        self.appSession = appSession
    }
    
    func authenticate() async {
        guard !email.isEmpty && !password.isEmpty else {
            errorMessage = "Please fill in all fields"
            return
        }
        
        isLoading = true
        errorMessage = nil
        
        do {
            let req = AuthRequest(email: email, password: password, name: isLoginMode ? nil : name)
            let response: AuthResponse
            
            if isLoginMode {
                response = try await AarkaaiAPI.shared.login(request: req)
            } else {
                response = try await AarkaaiAPI.shared.register(request: req)
            }
            
            appSession.setAuth(response: response)
            isLoading = false
        } catch {
            isLoading = false
            errorMessage = "Authentication failed. Please check your credentials."
            print("Auth Error: \(error)")
        }
    }
}
