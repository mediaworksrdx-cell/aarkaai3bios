package com.aarkaai.app.ui.chat

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aarkaai.app.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ModelSwitcherBottomSheet(
    currentModel: String,
    currentEffort: String,
    onModelSelect: (String) -> Unit,
    onEffortSelect: (String) -> Unit,
    onDismiss: () -> Unit
) {
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = BgPrimary,
        shape = RoundedCornerShape(topStart = 20.dp, topEnd = 20.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp)
                .padding(bottom = 24.dp)
        ) {
            Text(
                text = "Model & Reasoning",
                fontWeight = FontWeight.Bold,
                fontSize = 15.sp,
                color = TextPrimary
            )
            Text(
                text = "Select active AI engine and reasoning effort.",
                fontSize = 11.sp,
                color = TextTertiary,
                modifier = Modifier.padding(bottom = 12.dp)
            )

            // Model Selection
            Text(
                text = "AI MODEL",
                fontWeight = FontWeight.SemiBold,
                fontSize = 9.5.sp,
                letterSpacing = 0.8.sp,
                color = TextSecondary,
                modifier = Modifier.padding(bottom = 6.dp)
            )

            // Aarka AI 2.0 Option
            val isAarka = currentModel == "aarka-2.0"
            ModelOptionCard(
                title = "Aarka AI 2.0",
                subtitle = "Flagship reasoning engine with mathematical and quantitative rigor",
                icon = "⚡",
                badge = "Recommended",
                isSelected = isAarka,
                onClick = { onModelSelect("aarka-2.0") }
            )

            Spacer(modifier = Modifier.height(8.dp))

            // Google Gemini 3.7 Option
            val isGemini = currentModel == "gemini-3.7"
            ModelOptionCard(
                title = "Google Gemini 3.7",
                subtitle = "Multimodal partner model with extended context capabilities",
                icon = "✨",
                badge = "Multimodal",
                isSelected = isGemini,
                onClick = { onModelSelect("gemini-3.7") }
            )

            Spacer(modifier = Modifier.height(8.dp))

            // Claude Sonnet 5 Option
            val isClaude = currentModel == "claude-sonnet-5"
            ModelOptionCard(
                title = "Claude Sonnet 5",
                subtitle = "Anthropic state-of-the-art hybrid reasoning & coding model",
                icon = "🟣",
                badge = "Anthropic",
                isSelected = isClaude,
                onClick = { onModelSelect("claude-sonnet-5") }
            )

            Spacer(modifier = Modifier.height(14.dp))

            // Effort Selection
            Text(
                text = "REASONING EFFORT",
                fontWeight = FontWeight.SemiBold,
                fontSize = 9.5.sp,
                letterSpacing = 0.8.sp,
                color = TextSecondary,
                modifier = Modifier.padding(bottom = 6.dp)
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                listOf(
                    Triple("low", "Low", "⚡ Fast"),
                    Triple("medium", "Medium", "🎯 Balanced"),
                    Triple("high", "High", "🧠 Deep")
                ).forEach { (key, label, desc) ->
                    val isEffortSelected = currentEffort == key
                    Surface(
                        modifier = Modifier
                            .weight(1f)
                            .clip(RoundedCornerShape(10.dp))
                            .border(
                                width = 1.dp,
                                color = if (isEffortSelected) AccentPrimary else BorderColor,
                                shape = RoundedCornerShape(10.dp)
                            )
                            .clickable { onEffortSelect(key) },
                        color = if (isEffortSelected) AccentMuted else BgSecondary,
                        shape = RoundedCornerShape(10.dp)
                    ) {
                        Column(
                            modifier = Modifier.padding(vertical = 8.dp, horizontal = 6.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text(
                                text = label,
                                fontWeight = if (isEffortSelected) FontWeight.Bold else FontWeight.Medium,
                                fontSize = 11.5.sp,
                                color = if (isEffortSelected) AccentPrimary else TextPrimary
                            )
                            Text(
                                text = desc,
                                fontSize = 8.5.sp,
                                color = if (isEffortSelected) AccentHover else TextTertiary
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ModelOptionCard(
    title: String,
    subtitle: String,
    icon: String,
    badge: String,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .border(
                width = 1.dp,
                color = if (isSelected) AccentPrimary else BorderColor,
                shape = RoundedCornerShape(10.dp)
            )
            .clickable(onClick = onClick),
        color = if (isSelected) AccentMuted else BgSecondary,
        shape = RoundedCornerShape(10.dp)
    ) {
        Row(
            modifier = Modifier.padding(10.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(28.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(if (isSelected) AccentPrimary.copy(alpha = 0.2f) else BgTertiary),
                contentAlignment = Alignment.Center
            ) {
                Text(text = icon, fontSize = 14.sp)
            }

            Spacer(modifier = Modifier.width(10.dp))

            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = title,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        color = TextPrimary
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Surface(
                        color = if (isSelected) AccentPrimary else BgTertiary,
                        shape = RoundedCornerShape(4.dp)
                    ) {
                        Text(
                            text = badge,
                            fontSize = 7.5.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = if (isSelected) BgSecondary else TextSecondary,
                            modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp)
                        )
                    }
                }
                Spacer(modifier = Modifier.height(1.dp))
                Text(
                    text = subtitle,
                    fontSize = 9.5.sp,
                    color = TextSecondary,
                    lineHeight = 13.sp
                )
            }

            if (isSelected) {
                Icon(
                    imageVector = Icons.Default.Check,
                    contentDescription = "Selected",
                    tint = AccentPrimary,
                    modifier = Modifier.size(16.dp)
                )
            }
        }
    }
}
