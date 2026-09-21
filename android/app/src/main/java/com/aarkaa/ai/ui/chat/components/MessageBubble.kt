package com.aarkaa.ai.ui.chat.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ThumbDown
import androidx.compose.material.icons.filled.ThumbUp
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aarkaa.ai.core.theme.*
import com.aarkaa.ai.data.local.ChatMessage
import com.aarkaa.ai.data.local.MessageSender

@Composable
fun MessageBubble(
    message: ChatMessage,
    onFeedback: (rating: Int, correction: String?) -> Unit
) {
    val isUser = message.sender == MessageSender.USER
    var showCorrectionModal by remember { mutableStateOf(false) }
    var selectedRating by remember { mutableIntStateOf(0) }

    if (showCorrectionModal) {
        RlhfCorrectionDialog(
            rating = selectedRating,
            onDismiss = { showCorrectionModal = false },
            onSubmit = { correction ->
                showCorrectionModal = false
                onFeedback(selectedRating, correction)
            }
        )
    }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalAlignment = if (isUser) Alignment.End else Alignment.Start
    ) {
        Box(
            modifier = Modifier
                .widthIn(max = 340.dp)
                .clip(
                    RoundedCornerShape(
                        topStart = 16.dp,
                        topEnd = 16.dp,
                        bottomStart = if (isUser) 16.dp else 2.dp,
                        bottomEnd = if (isUser) 2.dp else 16.dp
                    )
                )
                .background(if (isUser) AccentIndigo.copy(alpha = 0.25f) else DarkSurface)
                .padding(14.dp)
        ) {
            Column {
                // If reasoning trace exists
                if (!message.thinkingTrace.isNullOrEmpty()) {
                    ReasoningAccordion(thoughtContent = message.thinkingTrace)
                    Spacer(modifier = Modifier.height(8.dp))
                }

                Text(
                    text = message.content,
                    color = TextPrimary,
                    fontSize = 15.sp,
                    lineHeight = 22.sp
                )

                if (message.sources.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Sources: " + message.sources.joinToString(", "),
                        color = AccentCyan,
                        fontSize = 11.sp
                    )
                }
            }
        }

        // Action row for Agent responses
        if (!isUser && !message.isStreaming) {
            Row(
                modifier = Modifier.padding(start = 4.dp, top = 2.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(
                    onClick = {
                        selectedRating = 1
                        onFeedback(1, null)
                    },
                    modifier = Modifier.size(28.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.ThumbUp,
                        contentDescription = "Thumbs Up",
                        tint = if (message.feedbackRating == 1) AccentGreen else TextMuted,
                        modifier = Modifier.size(15.dp)
                    )
                }

                IconButton(
                    onClick = {
                        selectedRating = -1
                        showCorrectionModal = true
                    },
                    modifier = Modifier.size(28.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.ThumbDown,
                        contentDescription = "Thumbs Down",
                        tint = if (message.feedbackRating == -1) AccentRed else TextMuted,
                        modifier = Modifier.size(15.dp)
                    )
                }
            }
        }
    }
}
