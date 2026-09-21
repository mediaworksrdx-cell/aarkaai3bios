package com.aarkaa.ai.ui.navigation

sealed class Screen(val route: String, val title: String) {
    data object Auth : Screen("auth", "Sign In")
    data object Chat : Screen("chat", "Chat")
    data object Screener : Screen("screener", "Screener")
    data object Strategy : Screen("strategy", "Options Strategy")
    data object Skills : Screen("skills", "Agent Skills")
    data object Documents : Screen("documents", "Workspace")
    data object Settings : Screen("settings", "Preferences")
}
