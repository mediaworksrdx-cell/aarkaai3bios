import Foundation
import Security

class AuthManager {
    
    static let shared = AuthManager()
    private init() {}
    
    private let tokenKey = "com.aarkaai.authToken"
    private let userIdKey = "com.aarkaai.userId"
    private let userNameKey = "com.aarkaai.userName"
    
    func saveAuth(token: String, userId: String, name: String?) {
        save(token, for: tokenKey)
        save(userId, for: userIdKey)
        if let name = name {
            save(name, for: userNameKey)
        }
    }
    
    func getToken() -> String? {
        return read(for: tokenKey)
    }
    
    func getUserId() -> String? {
        return read(for: userIdKey)
    }
    
    func getUserName() -> String? {
        return read(for: userNameKey)
    }
    
    func clearAuth() {
        delete(for: tokenKey)
        delete(for: userIdKey)
        delete(for: userNameKey)
    }
    
    // MARK: - Keychain Helpers
    
    private func save(_ value: String, for key: String) {
        let data = Data(value.utf8)
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: data
        ]
        
        // Delete existing item before saving
        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
    }
    
    private func read(for key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var dataTypeRef: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &dataTypeRef)
        
        if status == errSecSuccess {
            if let data = dataTypeRef as? Data {
                return String(data: data, encoding: .utf8)
            }
        }
        return nil
    }
    
    private func delete(for key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key
        ]
        SecItemDelete(query as CFDictionary)
    }
}
