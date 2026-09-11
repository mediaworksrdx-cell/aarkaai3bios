package com.aarkaai.app.ui.theme

import androidx.compose.ui.graphics.Color

// ──────── Aarka AI Exact Web Color System (globals.css) ────────

// Backgrounds
val BgPrimary = Color(0xFFFBF8F5)          // --bg-primary: #FBF8F5 (Nordic Porcelain Ivory)
val BgSecondary = Color(0xFFFFFFFF)        // --bg-secondary: #FFFFFF (Pure white surface)
val BgTertiary = Color(0xFFF1EDE5)         // --bg-tertiary: #F1EDE5 (Button/chip background)
val BgInput = Color(0xFFF6F3EB)            // --bg-input: #F6F3EB (Input pill background)
val BgHover = Color(0xFFECE6DA)            // --bg-hover: #ECE6DA
val BgGlass = Color(0xEBFBF8F5)            // --bg-glass: rgba(251, 248, 245, 0.92)

// Primary Terracotta Accent
val AccentPrimary = Color(0xFFC15F3D)      // --accent-primary: #C15F3D (Signature terracotta)
val AccentHover = Color(0xFFB05333)        // --accent-hover: #B05333 (Darker terracotta)
val AccentMuted = Color(0x1FC15F3D)        // --accent-muted: rgba(193, 95, 61, 0.12)
val AccentBorder = Color(0x59C15F3D)       // --border-accent: rgba(193, 95, 61, 0.35)

// Typography
val TextPrimary = Color(0xFF1F1E1B)        // --text-primary: #1F1E1B (Deep charcoal)
val TextSecondary = Color(0xFF635F55)      // --text-secondary: #635F55 (Medium charcoal)
val TextTertiary = Color(0xFF8E897E)       // --text-tertiary: #8E897E (Subtle muted gray)

// Structural Borders
val BorderColor = Color(0x14000000)        // --border: rgba(0, 0, 0, 0.08)
val BorderStrong = Color(0x26000000)       // --border-strong: rgba(0, 0, 0, 0.15)

// Code Blocks
val CodeBg = Color(0xFFF0ECE3)             // --code-bg: #F0ECE3
val CodeBorder = Color(0x14000000)         // --code-border: rgba(0, 0, 0, 0.08)

// Chat Bubbles
val UserBubbleBg = Color(0xFFF1EDE5)       // Neutral warm beige for user message bubble
val AiBubbleBg = Color.Transparent         // Blends with primary parchment background

// Legacy compatibility aliases for existing references
val BgLight = BgPrimary
val BgDark = BgPrimary                     // Permanent Light Theme enforced across app
val SurfaceLight = BgSecondary
val SurfaceDark = BgSecondary
val PrimaryLight = AccentPrimary
val PrimaryDark = AccentPrimary
val TextPrimaryLight = TextPrimary
val TextPrimaryDark = TextPrimary
val TextSecondaryLight = TextSecondary
val TextSecondaryDark = TextSecondary
val UserBubbleLight = UserBubbleBg
val UserBubbleDark = UserBubbleBg
val InputBgLight = BgInput
val InputBgDark = BgInput
val InputBorderLight = BorderColor
val InputBorderDark = BorderColor
val DividerLight = BorderColor
val DividerDark = BorderColor

// Status
val SuccessGreen = Color(0xFF16A34A)
val ErrorRed = Color(0xFFDC2626)
val WarningAmber = Color(0xFFD97706)
val PurpleAccent = Color(0xFF9333EA)
val BlueAccent = Color(0xFF2563EB)
