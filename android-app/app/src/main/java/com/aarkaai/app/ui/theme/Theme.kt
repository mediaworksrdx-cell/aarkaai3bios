package com.aarkaai.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val PermanentLightColorScheme = lightColorScheme(
    primary = AccentPrimary,
    onPrimary = Color.White,
    primaryContainer = AccentMuted,
    onPrimaryContainer = AccentHover,
    background = BgPrimary,
    onBackground = TextPrimary,
    surface = BgSecondary,
    onSurface = TextPrimary,
    surfaceVariant = UserBubbleBg,
    onSurfaceVariant = TextSecondary,
    outline = BorderColor,
    outlineVariant = BorderStrong,
    error = ErrorRed,
)

@Composable
fun AarkaaiTheme(
    darkTheme: Boolean = false, // Permanent Light Theme matching Aarka AI web policy
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = PermanentLightColorScheme,
        typography = Typography(),
        content = content
    )
}
