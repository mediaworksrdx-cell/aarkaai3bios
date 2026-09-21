package com.aarkaa.ai.data.local

data class ChatMessage(
    val id: String = java.util.UUID.randomUUID().toString(),
    val sender: MessageSender,
    val content: String,
    val thinkingTrace: String? = null,
    val toolCalls: List<String> = emptyList(),
    val sources: List<String> = emptyList(),
    val timestamp: Long = System.currentTimeMillis(),
    val isStreaming: Boolean = false,
    val feedbackRating: Int = 0 // 1 for thumbs up, -1 for thumbs down
)

enum class MessageSender {
    USER,
    AARKAA_AGENT,
    SYSTEM
}
