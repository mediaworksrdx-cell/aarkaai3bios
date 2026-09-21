package com.aarkaa.ai.ui.chat.components

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.aarkaa.ai.core.theme.*

@Composable
fun RlhfCorrectionDialog(
    rating: Int,
    onDismiss: () -> Unit,
    onSubmit: (String) -> Unit
) {
    var correctionText by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(
                text = if (rating > 0) "Provide Positive Feedback" else "Report Issue / Suggest Correction",
                color = TextPrimary
            )
        },
        text = {
            Column {
                Text(
                    text = "Help Aarka self-learn by explaining what was accurate or what should be improved.",
                    color = TextSecondary,
                    modifier = Modifier.padding(bottom = 12.dp)
                )
                OutlinedTextField(
                    value = correctionText,
                    onValueChange = { correctionText = it },
                    placeholder = { Text("Enter your correction or note...") },
                    modifier = Modifier.fillMaxWidth().height(120.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary
                    )
                )
            }
        },
        confirmButton = {
            Button(
                onClick = { onSubmit(correctionText) },
                colors = ButtonDefaults.buttonColors(containerColor = AccentCyan)
            ) {
                Text("Submit Feedback", color = DarkBackground)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel", color = TextSecondary)
            }
        },
        containerColor = DarkSurface
    )
}
