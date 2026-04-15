import Foundation

enum APIError: Error {
    case invalidURL
    case networkError(String)
    case decodingError
    case unauthorized
    case serverError(String)
}

class AarkaaiAPI {
    
    static let shared = AarkaaiAPI()
    private init() {}
    
    // Change this to your production backend URL
    var baseURL: String = "http://3.108.34.65:5000" // Production backend URL
    
    func register(request: AuthRequest) async throws -> AuthResponse {
        return try await performRequest(path: "/auth/register", method: "POST", body: request)
    }
    
    func login(request: AuthRequest) async throws -> AuthResponse {
        return try await performRequest(path: "/auth/login", method: "POST", body: request)
    }
    
    func sendPrompt(token: String, request: PromptRequest) async throws -> PromptResponse {
        let headers = ["Authorization": "Bearer \(token)"]
        return try await performRequest(path: "/prompt", method: "POST", body: request, headers: headers)
    }

    func streamPrompt(token: String, request: PromptRequest) -> AsyncThrowingStream<String, Error> {
        let headers = ["Authorization": "Bearer \(token)"]
        
        return AsyncThrowingStream { continuation in
            let task = Task {
                guard let url = URL(string: baseURL + "/prompt/stream") else {
                    continuation.finish(throwing: APIError.invalidURL)
                    return
                }
                
                var urlRequest = URLRequest(url: url)
                urlRequest.httpMethod = "POST"
                urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
                urlRequest.setValue("text/event-stream", forHTTPHeaderField: "Accept")
                headers.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
                
                do {
                    urlRequest.httpBody = try JSONEncoder().encode(request)
                    
                    let (bytes, response) = try await URLSession.shared.bytes(for: urlRequest)
                    
                    guard let httpResponse = response as? HTTPURLResponse else {
                        continuation.finish(throwing: APIError.networkError("Invalid response"))
                        return
                    }
                    
                    if httpResponse.statusCode != 200 {
                        continuation.finish(throwing: APIError.serverError("Status \(httpResponse.statusCode)"))
                        return
                    }
                    
                    for try await line in bytes.lines {
                        if Task.isCancelled { break }
                        
                        if line.hasPrefix("data: ") {
                            let jsonString = String(line.dropFirst(6))
                            if let data = jsonString.data(using: .utf8),
                               let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                               let type = dict["type"] as? String {
                                
                                if type == "content", let token = dict["token"] as? String {
                                    continuation.yield(token)
                                } else if type == "error", let detail = dict["detail"] as? String {
                                    continuation.finish(throwing: APIError.serverError(detail))
                                    return
                                }
                            }
                        }
                    }
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
            
            continuation.onTermination = { @Sendable _ in
                task.cancel()
            }
        }
    }

    func submitRLHF(token: String, request: RLHFRequest) async throws -> RLHFResponse {
        let headers = ["Authorization": "Bearer \(token)"]
        return try await performRequest(path: "/rlhf", method: "POST", body: request, headers: headers)
    }
    
    // MARK: - Private Core Request Method
    
    private func performRequest<T: Decodable, E: Encodable>(
        path: String,
        method: String,
        body: E? = nil,
        headers: [String: String]? = nil
    ) async throws -> T {
        guard let url = URL(string: baseURL + path) else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        headers?.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        if let body = body {
            do {
                request.httpBody = try JSONEncoder().encode(body)
            } catch {
                throw APIError.networkError("Encoding failed")
            }
        }
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError("Invalid response")
        }
        
        if httpResponse.statusCode == 401 {
            throw APIError.unauthorized
        }
        
        if !(200...299).contains(httpResponse.statusCode) {
            let errorMsg = String(data: data, encoding: .utf8) ?? "Unknown server error"
            throw APIError.serverError(errorMsg)
        }
        
        do {
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            print("Decoding Error: \(error)")
            throw APIError.decodingError
        }
    }
}
