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
            self.isCheckingAuth = false
        } else {
            Task {
                await loginOrRegisterGuest()
            }
        }
    }

    func loginOrRegisterGuest() async {
        let guestEmail = "visitor@aarkaai.com"
        let guestPassword = "VisitorSecurePassword123!"
        let guestName = "Web Visitor"
        
        do {
            let req = AuthRequest(email: guestEmail, password: guestPassword)
            let response = try await AarkaaiAPI.shared.login(request: req)
            self.setAuth(response: response)
            self.isCheckingAuth = false
        } catch {
            do {
                let req = AuthRequest(email: guestEmail, password: guestPassword, name: guestName)
                let response = try await AarkaaiAPI.shared.register(request: req)
                self.setAuth(response: response)
                self.isCheckingAuth = false
            } catch {
                self.isCheckingAuth = false
            }
        }
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
