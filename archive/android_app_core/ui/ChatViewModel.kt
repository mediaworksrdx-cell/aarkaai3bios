package com.example.aarkaai.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.aarkaai.network.PromptRequest
import com.example.aarkaai.network.RetrofitClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class ChatMessage(
    val id: String = java.util.UUID.randomUUID().toString(),
    val text: String,
    val isUser: Boolean,
    val isLoading: Boolean = false,
    val processingTime: Double? = null
)

class ChatViewModel : ViewModel() {

    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()

    // Assuming we use a static token or let user paste it for now
    var bearerToken: String = ""

    fun sendMessage(query: String) {
        if (query.isBlank()) return

        // 1. Add UX message to list
        val userMsg = ChatMessage(text = query, isUser = true)
        // 2. Add temporary loading message for AI
        val loadingMsg = ChatMessage(text = "", isUser = false, isLoading = true)
        
        _messages.value = _messages.value + listOf(userMsg, loadingMsg)

        viewModelScope.launch {
            try {
                // Ensure Bearer prefix
                val tokenHeader = if (bearerToken.startsWith("Bearer ")) bearerToken else "Bearer $bearerToken"
                
                val req = PromptRequest(query = query)
                val res = RetrofitClient.apiService.sendPrompt(tokenHeader, req)

                // Swap loading message with result
                _messages.value = _messages.value.dropLast(1) + ChatMessage(
                    text = res.response,
                    isUser = false,
                    isLoading = false,
                    processingTime = res.processing_time
                )
            } catch (e: Exception) {
                // Swap loading message with error
                _messages.value = _messages.value.dropLast(1) + ChatMessage(
                    text = "Connection Error: ${e.message}\nMake sure your backend is running or your Token is valid.",
                    isUser = false,
                    isLoading = false
                )
            }
        }
    }
}
