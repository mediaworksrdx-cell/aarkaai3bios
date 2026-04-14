package com.example.aarkaai.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.*
import androidx.compose.runtime.Composable

private val DarkColorScheme = darkColorScheme(
    primary = ClaudePrimary,
    background = ClaudeBackgroundDark,
    surface = ClaudeBackgroundDark,
    onPrimary = Color.White,
    onBackground = ClaudeTextPrimaryDark,
    onSurface = ClaudeTextPrimaryDark,
    surfaceVariant = UserBubbleColorDark // Used for user chat bubbles
)

private val LightColorScheme = lightColorScheme(
    primary = ClaudePrimary,
    background = ClaudeBackground,
    surface = ClaudeBackground,
    onPrimary = Color.White,
    onBackground = ClaudeTextPrimary,
    onSurface = ClaudeTextPrimary,
    surfaceVariant = UserBubbleColor // Used for user chat bubbles
)

// In a real app we'd define Source Serif Pro or a clear Sans Serif here.
// For now, Material3 default typography fits the clean look.
@Composable
fun ClaudeTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        // typography = Typography, // Future: Apply specific serif/sans-serif fonts here
        content = content
    )
}
