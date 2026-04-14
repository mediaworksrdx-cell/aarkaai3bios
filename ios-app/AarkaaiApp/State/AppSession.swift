import SwiftUI
import Combine

@MainActor
class AppSession: ObservableObject {
    @Published var isLoggedIn: Bool = false
    @Published var currentUserToken: String?
    @Published var currentUserId: String?
    @Published var currentUserName: String?
    @Published var isCheckingAuth: Bool = true
    
    init() {
        checkToken()
    }
    
    func checkToken() {
        if let token = AuthManager.shared.getToken() {
            self.currentUserToken = token
            self.currentUserId = AuthManager.shared.getUserId()
            self.currentUserName = AuthManager.shared.getUserName()
            self.isLoggedIn = true
        }
        self.isCheckingAuth = false
    }
    
    func setAuth(response: AuthResponse) {
        AuthManager.shared.saveAuth(token: response.access_token, userId: response.user_id, name: response.name)
        self.currentUserToken = response.access_token
        self.currentUserId = response.user_id
        self.currentUserName = response.name
        self.isLoggedIn = true
    }
    
    func logout() {
        AuthManager.shared.clearAuth()
        self.currentUserToken = nil
        self.currentUserId = nil
        self.currentUserName = nil
        self.isLoggedIn = false
    }
}
