import Foundation

// MARK: - Auth Models

struct AuthRequest: Codable {
    let email: String
    let password: String
    var name: String? = nil
}

struct AuthResponse: Codable {
    let access_token: String
    let token_type: String
    let user_id: String
    let name: String?
}

// MARK: - Prompt Models

struct PromptRequest: Codable {
    let query: String
    var session_id: String = "1"
    var context: [String: AnyCodable]? = nil
}

struct PromptResponse: Codable {
    let response: String
    let intent: String
    let confidence: Double
    let sources: [String]
    let detected_language: String
    let processing_time: Double
}

// MARK: - RLHF Models

struct RLHFRequest: Codable {
    let user_id: String
    let rating: Int
    var conversation_id: Int? = nil
    var correction: String? = nil
}

struct RLHFResponse: Codable {
    let status: String
    let message: String
}

// MARK: - Helper: AnyCodable
/// A type-safe way to handle dynamic dictionaries in Swift Codable
struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let x = try? container.decode(String.self) { value = x }
        else if let x = try? container.decode(Int.self) { value = x }
        else if let x = try? container.decode(Double.self) { value = x }
        else if let x = try? container.decode(Bool.self) { value = x }
        else if let x = try? container.decode([String: AnyCodable].self) { value = x.mapValues { $0.value } }
        else if let x = try? container.decode([AnyCodable].self) { value = x.map { $0.value } }
        else { throw DecodingError.dataCorruptedError(in: container, debugDescription: "Wrong type") }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch value {
        case let x as String: try container.encode(x)
        case let x as Int: try container.encode(x)
        case let x as Double: try container.encode(x)
        case let x as Bool: try container.encode(x)
        case let x as [String: Any]: try container.encode(x.mapValues { AnyCodable($0) })
        case let x as [Any]: try container.encode(x.map { AnyCodable($0) })
        default: throw EncodingError.invalidValue(value, EncodingError.Context(codingPath: [], debugDescription: "Invalid type"))
        }
    }
}
