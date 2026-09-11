package com.aarkaai.app.ui.chat

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.aarkaai.app.data.ConversationRepository
import com.aarkaai.app.data.SettingsRepository
import com.aarkaai.app.data.TokenManager
import com.aarkaai.app.network.PromptRequest
import com.aarkaai.app.network.RetrofitClient
import com.aarkaai.app.network.RlhfRequest
import com.aarkaai.app.network.SseAuthException
import com.aarkaai.app.network.SseClient
import androidx.annotation.Keep
import com.google.gson.annotations.SerializedName
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.util.UUID

// ──────── Data Classes ────────

@Keep
data class ChatMessage(
    @SerializedName("id") val id: String = UUID.randomUUID().toString(),
    @SerializedName("text") val text: String = "",
    @SerializedName("isUser") val isUser: Boolean = false,
    @SerializedName("isLoading") val isLoading: Boolean = false,
    @SerializedName("isError") val isError: Boolean = false,
    @SerializedName("processingTime") val processingTime: Double? = null,
    @SerializedName("intent") val intent: String? = null,
    @SerializedName("sources") val sources: List<String> = emptyList(),
    @SerializedName("timestamp") val timestamp: Long = System.currentTimeMillis(),
    @SerializedName("rlhfRating") val rlhfRating: Int? = null,   // null = not rated, 1 = positive, -1 = negative
    @SerializedName("modelUsed") val modelUsed: String? = null
)

@Keep
data class Conversation(
    @SerializedName("id") val id: String = UUID.randomUUID().toString(),
    @SerializedName("title") val title: String = "New Chat",
    @SerializedName("messages") val messages: List<ChatMessage> = emptyList(),
    @SerializedName("createdAt") val createdAt: Long = System.currentTimeMillis(),
    @SerializedName("model") val model: String = "aarka-2.0",
    @SerializedName("effort") val effort: String = "medium"
)

data class ChatUiState(
    val conversations: List<Conversation> = listOf(Conversation()),
    val activeConversationId: String = "",
    val isSidebarOpen: Boolean = false,
    val isTyping: Boolean = false,
    val selectedModel: String = "aarka-2.0",
    val reasoningEffort: String = "medium",
    val searchQuery: String = "",
    val userName: String = "Web Visitor",
    val userEmail: String = "visitor@aarkaai.com",
    val isGuest: Boolean = true,
    val currentUserId: String? = null,
    val incognitoMode: Boolean = false,
    val density: String = "comfortable",
    val showTimestamps: Boolean = true
) {
    val activeConversation: Conversation?
        get() = conversations.find { it.id == activeConversationId }

    val messages: List<ChatMessage>
        get() = activeConversation?.messages ?: emptyList()

    val filteredConversations: List<Conversation>
        get() = if (searchQuery.isBlank()) {
            conversations
        } else {
            conversations.filter { it.title.contains(searchQuery, ignoreCase = true) }
        }
}

// ──────── ViewModel ────────

class ChatViewModel(application: Application) : AndroidViewModel(application) {

    private val tokenManager = TokenManager(application)
    private val conversationRepository = ConversationRepository(application)
    private val settingsRepository = SettingsRepository(application)

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    var bearerToken: String = ""
    private var streamJob: Job? = null

    init {
        val initial = Conversation()
        _uiState.value = ChatUiState(
            conversations = listOf(initial),
            activeConversationId = initial.id
        )

        // Observe user ID once on startup and on genuine user account switches
        var lastLoadedUserId: String? = null
        var isFirstLaunch = true

        viewModelScope.launch {
            tokenManager.userId.collectLatest { userId ->
                if (isFirstLaunch) {
                    isFirstLaunch = false
                    lastLoadedUserId = userId
                    loadConversationsForUser(userId, openNewChat = true)
                } else if (userId != null && userId != lastLoadedUserId) {
                    lastLoadedUserId = userId
                    loadConversationsForUser(userId, openNewChat = false)
                }
            }
        }

        // Sync token
        viewModelScope.launch {
            tokenManager.token.collectLatest { token ->
                if (token != null) {
                    bearerToken = token
                }
            }
        }

        // Sync user profile name
        viewModelScope.launch {
            tokenManager.userName.collectLatest { name ->
                if (!name.isNullOrBlank()) {
                    val isGuestUser = name == "Web Visitor" || name == "Guest User" || name.startsWith("Guest") || name.startsWith("offline_guest")
                    _uiState.update { it.copy(userName = name, isGuest = isGuestUser) }
                }
            }
        }

        // Sync settings (model, effort, density, timestamps, incognito)
        viewModelScope.launch {
            settingsRepository.localSettings.collectLatest { settings ->
                _uiState.update { current ->
                    current.copy(
                        selectedModel = settings.defaultModel ?: current.selectedModel,
                        reasoningEffort = settings.reasoningDepth ?: current.reasoningEffort,
                        density = settings.density ?: current.density,
                        showTimestamps = settings.showTimestamps,
                        incognitoMode = settings.incognitoChat
                    )
                }
            }
        }
    }

    fun loadConversationsForUser(userId: String?, openNewChat: Boolean = true) {
        viewModelScope.launch {
            val rawSaved = conversationRepository.loadConversations(userId)
            val saved = rawSaved.map { conv ->
                val cleanedMsgs = conv.messages.map { msg ->
                    if (msg.isLoading) {
                        msg.copy(
                            isLoading = false,
                            text = if (msg.text.isBlank()) "⚠️ Connection was interrupted. Tap regenerate to retry." else cleanAssistantText(msg.text)
                        )
                    } else msg
                }
                conv.copy(messages = cleanedMsgs)
            }

            if (openNewChat) {
                // When launching fresh, start on a clean new chat so welcome screen is shown,
                // while preserving all saved conversations in history/drawer.
                val topEmpty = saved.firstOrNull()?.takeIf { it.messages.isEmpty() }
                if (topEmpty != null) {
                    _uiState.update { current ->
                        current.copy(
                            conversations = saved,
                            activeConversationId = topEmpty.id,
                            currentUserId = userId
                        )
                    }
                    tokenManager.saveActiveConversationId(topEmpty.id)
                } else {
                    val freshChat = Conversation(
                        model = _uiState.value.selectedModel,
                        effort = _uiState.value.reasoningEffort
                    )
                    _uiState.update { current ->
                        current.copy(
                            conversations = listOf(freshChat) + saved,
                            activeConversationId = freshChat.id,
                            currentUserId = userId
                        )
                    }
                    tokenManager.saveActiveConversationId(freshChat.id)
                }
            } else {
                val storedActiveId = tokenManager.activeConversationId.firstOrNull()
                val targetActive = saved.find { it.id == storedActiveId }
                    ?: saved.firstOrNull()
                    ?: Conversation()

                val allConvs = if (saved.isEmpty()) listOf(targetActive) else saved
                _uiState.update { current ->
                    current.copy(
                        conversations = allConvs,
                        activeConversationId = targetActive.id,
                        currentUserId = userId
                    )
                }
            }
        }
    }

    fun onUserLoggedIn(token: String, userId: String, name: String?) {
        bearerToken = token
        _uiState.update {
            it.copy(
                userName = name ?: "Aarka User",
                isGuest = false,
                currentUserId = userId
            )
        }
        loadConversationsForUser(userId, openNewChat = true)
    }

    fun onUserLoggedOut() {
        bearerToken = ""
        val initial = Conversation()
        _uiState.update {
            ChatUiState(
                conversations = listOf(initial),
                activeConversationId = initial.id,
                userName = "Web Visitor",
                userEmail = "visitor@aarkaai.com",
                isGuest = true,
                currentUserId = null
            )
        }
        loadConversationsForUser(null)
    }

    fun toggleSidebar() {
        _uiState.update { it.copy(isSidebarOpen = !it.isSidebarOpen) }
    }

    fun closeSidebar() {
        _uiState.update { it.copy(isSidebarOpen = false) }
    }

    fun setSearchQuery(query: String) {
        _uiState.update { it.copy(searchQuery = query) }
    }

    fun selectModel(model: String) {
        _uiState.update { it.copy(selectedModel = model) }
    }

    fun selectEffort(effort: String) {
        _uiState.update { it.copy(reasoningEffort = effort) }
    }

    fun newConversation(model: String? = null, effort: String? = null) {
        val currentConvs = _uiState.value.conversations
        // If the top conversation is already empty, just select it
        val topEmpty = currentConvs.firstOrNull()?.takeIf { it.messages.isEmpty() }
        if (topEmpty != null) {
            _uiState.update { it.copy(activeConversationId = topEmpty.id, isSidebarOpen = false, isTyping = false) }
            viewModelScope.launch {
                tokenManager.saveActiveConversationId(topEmpty.id)
            }
            return
        }

        val conv = Conversation(
            model = model ?: _uiState.value.selectedModel,
            effort = effort ?: _uiState.value.reasoningEffort
        )
        _uiState.update {
            it.copy(
                conversations = listOf(conv) + it.conversations,
                activeConversationId = conv.id,
                isSidebarOpen = false,
                isTyping = false
            )
        }
        viewModelScope.launch {
            tokenManager.saveActiveConversationId(conv.id)
        }
        persistConversations()
    }

    fun selectConversation(id: String) {
        val targetConv = _uiState.value.conversations.find { it.id == id }
        val hasActiveLoading = targetConv?.messages?.any { it.isLoading } == true && streamJob?.isActive == true
        _uiState.update { it.copy(activeConversationId = id, isSidebarOpen = false, isTyping = hasActiveLoading) }
        viewModelScope.launch {
            tokenManager.saveActiveConversationId(id)
        }
    }

    fun renameConversation(id: String, newTitle: String) {
        if (newTitle.isBlank()) return
        _uiState.update { state ->
            val updated = state.conversations.map {
                if (it.id == id) it.copy(title = newTitle.trim()) else it
            }
            state.copy(conversations = updated)
        }
        persistConversations()
    }

    fun deleteConversation(id: String) {
        _uiState.update { state ->
            val remaining = state.conversations.filter { it.id != id }
            val nextList = if (remaining.isEmpty()) listOf(Conversation()) else remaining
            val nextActive = if (state.activeConversationId == id) nextList.first().id else state.activeConversationId
            state.copy(conversations = nextList, activeConversationId = nextActive)
        }
        persistConversations()
    }

    fun clearAllHistory() {
        val initial = Conversation()
        val userId = _uiState.value.currentUserId
        _uiState.update {
            it.copy(
                conversations = listOf(initial),
                activeConversationId = initial.id,
                isSidebarOpen = false
            )
        }
        viewModelScope.launch {
            conversationRepository.clearConversations(userId)
        }
    }

    fun stopGeneration() {
        val activeId = _uiState.value.activeConversationId
        streamJob?.cancel()
        streamJob = null
        finishLoading(activeId)
        _uiState.update { it.copy(isTyping = false) }
        persistConversations()
    }

    fun regenerateResponse(assistantMessageId: String) {
        val active = _uiState.value.activeConversation ?: return
        val messages = active.messages
        val assistantIdx = messages.indexOfFirst { it.id == assistantMessageId }
        if (assistantIdx <= 0) return

        val userMessage = messages[assistantIdx - 1]
        if (!userMessage.isUser) return

        // Remove the assistant message and regenerate
        _uiState.update { state ->
            val updatedConvs = state.conversations.map { conv ->
                if (conv.id == state.activeConversationId) {
                    conv.copy(messages = messages.filter { it.id != assistantMessageId })
                } else conv
            }
            state.copy(conversations = updatedConvs)
        }

        val loadingMsg = ChatMessage(text = "", isUser = false, isLoading = true, modelUsed = _uiState.value.selectedModel)
        addMessages(loadingMsg)
        _uiState.update { it.copy(isTyping = true) }

        executeStreaming(userMessage.text)
    }

    fun sendMessage(query: String) {
        if (query.isBlank()) return

        val currentModel = _uiState.value.selectedModel
        val userMsg = ChatMessage(text = query, isUser = true)
        val loadingMsg = ChatMessage(text = "", isUser = false, isLoading = true, modelUsed = currentModel)

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

        // Persist immediately so query is saved even if user navigates away or network drops
        persistConversations()

        executeStreaming(query)
    }

    private fun executeStreaming(query: String) {
        val targetConversationId = _uiState.value.activeConversationId
        streamJob?.cancel()
        streamJob = viewModelScope.launch {
            try {
                var tokenHeader = if (bearerToken.startsWith("Bearer ")) bearerToken else "Bearer $bearerToken"
                val model = _uiState.value.selectedModel
                val effort = _uiState.value.reasoningEffort

                try {
                    streamOrFallback(targetConversationId, tokenHeader, query, targetConversationId, model, effort)
                } catch (e: Exception) {
                    val isAuthError = (e is retrofit2.HttpException && (e.code() == 401 || e.code() == 403)) ||
                                      (e is SseAuthException)
                    if (isAuthError) {
                        val newToken = refreshGuestToken()
                        if (newToken != null) {
                            tokenHeader = if (newToken.startsWith("Bearer ")) newToken else "Bearer $newToken"
                            streamOrFallback(targetConversationId, tokenHeader, query, targetConversationId, model, effort)
                        } else {
                            throw e
                        }
                    } else {
                        throw e
                    }
                }
            } catch (e: kotlinx.coroutines.CancellationException) {
                // User clicked stop - keep partial response
                finishLoading(targetConversationId)
            } catch (e: Exception) {
                replaceLoading(
                    targetConversationId,
                    ChatMessage(
                        text = "⚠️ ${e.localizedMessage ?: "Connection failed. Is the backend running?"}",
                        isUser = false,
                        isError = true,
                        isLoading = false
                    )
                )
            } finally {
                finishLoading(targetConversationId)
                _uiState.update { it.copy(isTyping = false) }
                persistConversations()
            }
        }
    }

    private fun persistConversations() {
        if (_uiState.value.incognitoMode) return // Don't persist incognito sessions
        val userId = _uiState.value.currentUserId
        val currentConvs = _uiState.value.conversations
        val activeId = _uiState.value.activeConversationId
        viewModelScope.launch {
            // Keep all conversations that have messages, plus the current active one if empty
            val toSave = currentConvs.filter { conv ->
                conv.messages.isNotEmpty() || conv.id == activeId
            }
            conversationRepository.saveConversations(toSave, userId)
        }
    }

    private suspend fun refreshGuestToken(): String? {
        val guestEmail = "visitor@aarkaai.com"
        val guestPassword = "VisitorSecurePassword123!"
        val guestName = "Web Visitor"
        return try {
            val res = RetrofitClient.api.login(com.aarkaai.app.network.AuthRequest(email = guestEmail, password = guestPassword))
            tokenManager.saveToken(res.access_token)
            bearerToken = res.access_token
            res.access_token
        } catch (loginEx: Exception) {
            try {
                val res = RetrofitClient.api.register(
                    com.aarkaai.app.network.AuthRequest(email = guestEmail, password = guestPassword, name = guestName)
                )
                tokenManager.saveToken(res.access_token)
                bearerToken = res.access_token
                res.access_token
            } catch (regEx: Exception) {
                null
            }
        }
    }

    fun submitRlhf(messageId: String, rating: Int) {
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

        viewModelScope.launch {
            try {
                var tokenHeader = if (bearerToken.startsWith("Bearer ")) bearerToken else "Bearer $bearerToken"
                try {
                    RetrofitClient.api.submitRlhf(
                        token = tokenHeader,
                        request = RlhfRequest(
                            user_id = "android_user",
                            rating = rating
                        )
                    )
                } catch (e: retrofit2.HttpException) {
                    if (e.code() == 401 || e.code() == 403) {
                        val newToken = refreshGuestToken()
                        if (newToken != null) {
                            tokenHeader = if (newToken.startsWith("Bearer ")) newToken else "Bearer $newToken"
                            RetrofitClient.api.submitRlhf(
                                token = tokenHeader,
                                request = RlhfRequest(
                                    user_id = "android_user",
                                    rating = rating
                                )
                            )
                        }
                    }
                }
            } catch (e: Exception) {
            }
        }
        persistConversations()
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

    companion object {
        fun cleanAssistantText(text: String): String {
            return text
                .replace(Regex("""(?i)\s*(?:\*{1,2}|[\(\[])?\s*end of (?:answer|response|text|explanation)\s*(?:\*{1,2}|[\)\]])?\.?[\s`]*$"""), "")
                .replace(Regex("""(?i)\s*---+\s*end\s+(?:of\s+)?(?:answer|response|disclaimer|text)\s*---+[\s`]*$"""), "")
                .replace(Regex("""(?i)\s*#Aarkaa(?:AI)?\b.*$"""), "")
                .replace(Regex("""(?i)\s*#Aarka(?:AI)?\b.*$"""), "")
                .replace(Regex("""(?:\s*#[A-Za-z0-9_\-\/]+)+\s*$"""), "")
                .trimEnd()
        }
    }

    private fun replaceLoading(conversationId: String, replacement: ChatMessage) {
        val cleanMsg = if (!replacement.isUser) {
            replacement.copy(text = cleanAssistantText(replacement.text), isLoading = false)
        } else replacement
        _uiState.update { state ->
            val convs = state.conversations.map { conv ->
                if (conv.id == conversationId) {
                    val updated = conv.messages.toMutableList()
                    val loadingIdx = updated.indexOfLast { it.isLoading }
                    if (loadingIdx >= 0) updated[loadingIdx] = cleanMsg
                    else updated.add(cleanMsg)
                    conv.copy(messages = updated)
                } else conv
            }
            state.copy(conversations = convs)
        }
    }

    private suspend fun streamOrFallback(
        targetConversationId: String,
        tokenHeader: String,
        query: String,
        currentSessionId: String,
        model: String,
        effort: String
    ) {
        try {
            var hasReceivedTokens = false
            SseClient.streamPrompt(tokenHeader, query, currentSessionId, model, effort).collect { token ->
                hasReceivedTokens = true
                appendToLoading(targetConversationId, token)
            }
            if (!hasReceivedTokens) {
                throw Exception("Stream ended without tokens")
            }
            finishLoading(targetConversationId)
        } catch (e: SseAuthException) {
            throw e
        } catch (e: Exception) {
            val response = RetrofitClient.api.sendPrompt(
                token = tokenHeader,
                request = PromptRequest(query = query, session_id = currentSessionId, model = model, effort = effort)
            )
            replaceLoading(
                targetConversationId,
                ChatMessage(
                    text = response.response,
                    isUser = false,
                    isLoading = false,
                    processingTime = response.processing_time,
                    intent = response.intent,
                    sources = response.sources,
                    modelUsed = model
                )
            )
        }
    }

    private fun appendToLoading(conversationId: String, textToAppend: String) {
        _uiState.update { state ->
            val convs = state.conversations.map { conv ->
                if (conv.id == conversationId) {
                    val updated = conv.messages.toMutableList()
                    val loadingIdx = updated.indexOfLast { it.isLoading }
                    if (loadingIdx >= 0) {
                        val msg = updated[loadingIdx]
                        updated[loadingIdx] = msg.copy(text = msg.text + textToAppend)
                    }
                    conv.copy(messages = updated)
                } else conv
            }
            state.copy(conversations = convs)
        }
    }

    private fun finishLoading(conversationId: String) {
        _uiState.update { state ->
            val convs = state.conversations.map { conv ->
                if (conv.id == conversationId) {
                    val updated = conv.messages.toMutableList()
                    val loadingIdx = updated.indexOfLast { it.isLoading }
                    if (loadingIdx >= 0) {
                        val msg = updated[loadingIdx]
                        updated[loadingIdx] = msg.copy(
                            text = cleanAssistantText(msg.text),
                            isLoading = false
                        )
                    }
                    conv.copy(messages = updated)
                } else conv
            }
            state.copy(conversations = convs)
        }
    }
}
