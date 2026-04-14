package com.aarkaai.app.ui.chat

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.aarkaai.app.network.PromptRequest
import com.aarkaai.app.network.RetrofitClient
import com.aarkaai.app.network.RlhfRequest
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID
import com.aarkaai.app.data.TokenManager
import kotlinx.coroutines.flow.collectLatest

// ──────── Data Classes ────────

data class ChatMessage(
    val id: String = UUID.randomUUID().toString(),
    val text: String,
    val isUser: Boolean,
    val isLoading: Boolean = false,
    val isError: Boolean = false,
    val processingTime: Double? = null,
    val intent: String? = null,
    val sources: List<String> = emptyList(),
    val timestamp: Long = System.currentTimeMillis(),
    val rlhfRating: Int? = null   // null = not rated, 1 = positive, -1 = negative
)

data class Conversation(
    val id: String = UUID.randomUUID().toString(),
    val title: String = "New Chat",
    val messages: List<ChatMessage> = emptyList(),
    val createdAt: Long = System.currentTimeMillis()
)

data class ChatUiState(
    val conversations: List<Conversation> = listOf(Conversation()),
    val activeConversationId: String = "",
    val isSidebarOpen: Boolean = false,
    val isTyping: Boolean = false
) {
    val activeConversation: Conversation?
        get() = conversations.find { it.id == activeConversationId }

    val messages: List<ChatMessage>
        get() = activeConversation?.messages ?: emptyList()
}

// ──────── ViewModel ────────

class ChatViewModel(application: Application) : AndroidViewModel(application) {

    private val tokenManager = TokenManager(application)
    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    var bearerToken: String = ""

    init {
        val initial = Conversation()
        _uiState.value = ChatUiState(
            conversations = listOf(initial),
            activeConversationId = initial.id
        )

        // Sync token from TokenManager
        viewModelScope.launch {
            tokenManager.token.collectLatest { token ->
                if (token != null) {
                    bearerToken = token
                }
            }
        }
    }

    fun toggleSidebar() {
        _uiState.update { it.copy(isSidebarOpen = !it.isSidebarOpen) }
    }

    fun closeSidebar() {
        _uiState.update { it.copy(isSidebarOpen = false) }
    }

    fun newConversation() {
        val conv = Conversation()
        _uiState.update {
            it.copy(
                conversations = it.conversations + conv,
                activeConversationId = conv.id,
                isSidebarOpen = false
            )
        }
    }

    fun selectConversation(id: String) {
        _uiState.update { it.copy(activeConversationId = id, isSidebarOpen = false) }
    }

    fun sendMessage(query: String) {
        if (query.isBlank()) return

        val userMsg = ChatMessage(text = query, isUser = true)
        val loadingMsg = ChatMessage(text = "", isUser = false, isLoading = true)

        addMessages(userMsg, loadingMsg)

        // Auto-title the conversation from the first user message
        _uiState.update { state ->
            val convs = state.conversations.map { conv ->
                if (conv.id == state.activeConversationId && conv.messages.count { it.isUser } <= 1) {
                    conv.copy(title = query.take(40) + if (query.length > 40) "…" else "")
                } else conv
            }
            state.copy(conversations = convs, isTyping = true)
        }

        viewModelScope.launch {
            try {
                val tokenHeader = if (bearerToken.startsWith("Bearer ")) bearerToken else "Bearer $bearerToken"
                val response = RetrofitClient.api.sendPrompt(
                    token = tokenHeader,
                    request = PromptRequest(query = query)
                )

                replaceLoading(
                    ChatMessage(
                        text = response.response,
                        isUser = false,
                        processingTime = response.processing_time,
                        intent = response.intent,
                        sources = response.sources
                    )
                )
            } catch (e: Exception) {
                replaceLoading(
                    ChatMessage(
                        text = "⚠️ ${e.localizedMessage ?: "Connection failed. Is the backend running?"}",
                        isUser = false,
                        isError = true
                    )
                )
            } finally {
                _uiState.update { it.copy(isTyping = false) }
            }
        }
    }

    // ── RLHF Feedback ──────────────────────────────────────────────
    fun submitRlhf(messageId: String, rating: Int) {
        // Update the UI immediately
        _uiState.update { state ->
            val convs = state.conversations.map { conv ->
                if (conv.id == state.activeConversationId) {
                    val updated = conv.messages.map { msg ->
                        if (msg.id == messageId) msg.copy(rlhfRating = rating) else msg
                    }
                    conv.copy(messages = updated)
                } else conv
            }
            state.copy(conversations = convs)
        }

        // Send to backend asynchronously
        viewModelScope.launch {
            try {
                val tokenHeader = if (bearerToken.startsWith("Bearer ")) bearerToken else "Bearer $bearerToken"
                RetrofitClient.api.submitRlhf(
                    token = tokenHeader,
                    request = RlhfRequest(
                        user_id = "android_user",  // Will be overridden by JWT on backend
                        rating = rating
                    )
                )
            } catch (e: Exception) {
                // Silently fail — feedback is best-effort
            }
        }
    }

    private fun addMessages(vararg msgs: ChatMessage) {
        _uiState.update { state ->
            val convs = state.conversations.map { conv ->
                if (conv.id == state.activeConversationId) {
                    conv.copy(messages = conv.messages + msgs.toList())
                } else conv
            }
            state.copy(conversations = convs)
        }
    }

    private fun replaceLoading(replacement: ChatMessage) {
        _uiState.update { state ->
            val convs = state.conversations.map { conv ->
                if (conv.id == state.activeConversationId) {
                    val updated = conv.messages.toMutableList()
                    val loadingIdx = updated.indexOfLast { it.isLoading }
                    if (loadingIdx >= 0) updated[loadingIdx] = replacement
                    else updated.add(replacement)
                    conv.copy(messages = updated)
                } else conv
            }
            state.copy(conversations = convs)
        }
    }
}
