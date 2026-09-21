package com.aarkaa.ai.ui.chat

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aarkaa.ai.AarkaaApplication
import com.aarkaa.ai.core.network.SseStreamRepository
import com.aarkaa.ai.core.theme.*
import com.aarkaa.ai.data.api.*
import com.aarkaa.ai.data.local.ChatMessage
import com.aarkaa.ai.data.local.MessageSender
import com.aarkaa.ai.ui.chat.components.MessageBubble
import kotlinx.coroutines.launch

@Composable
fun ChatScreen() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val listState = rememberLazyListState()

    val apiClient = remember { AarkaaApplication.instance.apiClient }
    val apiService = remember { apiClient.createService<AarkaaApiService>() }
    val streamRepo = remember { SseStreamRepository(apiClient) }

    val messages = remember { mutableStateListOf<ChatMessage>() }
    var inputText by remember { mutableStateOf("") }
    var isStreaming by remember { mutableStateOf(false) }
    var selectedMode by remember { mutableStateOf("production") }

    LaunchedEffect(Unit) {
        if (messages.isEmpty()) {
            messages.add(
                ChatMessage(
                    sender = MessageSender.AARKAA_AGENT,
                    content = "Hello! I am Aarka, your autonomous AI coding, quantitative finance, and research assistant. How can I help you today?"
                )
            )
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(DarkSurface)
                .padding(horizontal = 16.dp, vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("Mode:", color = TextSecondary, fontSize = 12.sp)
            Spacer(modifier = Modifier.width(8.dp))
            listOf("production", "fastpath", "agent_path").forEach { mode ->
                FilterChip(
                    selected = selectedMode == mode,
                    onClick = { selectedMode = mode },
                    label = { Text(mode, fontSize = 11.sp) },
                    modifier = Modifier.padding(end = 4.dp),
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = AccentCyan,
                        selectedLabelColor = DarkBackground
                    )
                )
            }
        }

        LazyColumn(
            state = listState,
            modifier = Modifier
                .weight(1f)
                .padding(horizontal = 16.dp),
            contentPadding = PaddingValues(vertical = 8.dp)
        ) {
            items(messages, key = { it.id }) { message ->
                MessageBubble(
                    message = message,
                    onFeedback = { rating, correction ->
                        scope.launch {
                            try {
                                apiService.submitRlhf(
                                    RLHFRequest(
                                        conversationId = message.id,
                                        rating = rating,
                                        correction = correction
                                    )
                                )
                                Toast.makeText(context, "Feedback saved", Toast.LENGTH_SHORT).show()
                            } catch (e: Exception) {
                                Toast.makeText(context, "RLHF failed: " + e.message, Toast.LENGTH_SHORT).show()
                            }
                        }
                    }
                )
            }
        }

        Surface(
            color = DarkSurface,
            modifier = Modifier.fillMaxWidth()
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedTextField(
                    value = inputText,
                    onValueChange = { inputText = it },
                    placeholder = { Text("Ask Aarka anything...", color = TextMuted) },
                    modifier = Modifier.weight(1f),
                    maxLines = 4,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary,
                        focusedBorderColor = AccentCyan
                    )
                )

                Spacer(modifier = Modifier.width(8.dp))

                IconButton(
                    onClick = {
                        val promptText = inputText.trim()
                        if (promptText.isEmpty() || isStreaming) return@IconButton

                        inputText = ""
                        messages.add(ChatMessage(sender = MessageSender.USER, content = promptText))

                        val assistantMsgId = java.util.UUID.randomUUID().toString()
                        val placeholderMsg = ChatMessage(
                            id = assistantMsgId,
                            sender = MessageSender.AARKAA_AGENT,
                            content = "",
                            isStreaming = true
                        )
                        messages.add(placeholderMsg)
                        isStreaming = true

                        scope.launch {
                            listState.animateScrollToItem(messages.size - 1)
                            try {
                                val req = PromptRequest(query = promptText, mode = selectedMode)
                                val responseContent = StringBuilder()
                                val thinkingContent = StringBuilder()

                                streamRepo.streamPrompt(req, mode = selectedMode).collect { event ->
                                    when (event) {
                                        is StreamEvent.Token -> responseContent.append(event.content)
                                        is StreamEvent.Thinking -> thinkingContent.append(event.content)
                                        is StreamEvent.Error -> responseContent.append("\n[Error: " + event.detail + "]")
                                        else -> {}
                                    }

                                    val idx = messages.indexOfFirst { it.id == assistantMsgId }
                                    if (idx != -1) {
                                        messages[idx] = messages[idx].copy(
                                            content = responseContent.toString(),
                                            thinkingTrace = if (thinkingContent.isNotEmpty()) thinkingContent.toString() else null,
                                            isStreaming = true
                                        )
                                    }
                                }

                                val finalIdx = messages.indexOfFirst { it.id == assistantMsgId }
                                if (finalIdx != -1) {
                                    messages[finalIdx] = messages[finalIdx].copy(isStreaming = false)
                                }
                            } catch (e: Exception) {
                                val errIdx = messages.indexOfFirst { it.id == assistantMsgId }
                                if (errIdx != -1) {
                                    messages[errIdx] = messages[errIdx].copy(
                                        content = "Connection error: " + (e.message ?: "Inference service offline."),
                                        isStreaming = false
                                    )
                                }
                            } finally {
                                isStreaming = false
                            }
                        }
                    },
                    modifier = Modifier
                        .background(AccentCyan, RoundedCornerShape(8.dp))
                        .size(48.dp)
                ) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.Send,
                        contentDescription = "Send",
                        tint = DarkBackground
                    )
                }
            }
        }
    }
}
