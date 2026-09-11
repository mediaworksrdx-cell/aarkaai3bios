package com.aarkaai.app.ui.navigation

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.aarkaai.app.ui.auth.AuthScreen
import com.aarkaai.app.ui.auth.AuthViewModel
import com.aarkaai.app.ui.chat.ChatScreen
import com.aarkaai.app.ui.chat.ChatViewModel

object Routes {
    const val SPLASH = "splash"
    const val AUTH = "auth"
    const val CHAT = "chat"
    const val SETTINGS = "settings"
    const val SKILLS = "skills"
}

@Composable
fun AarkaaiNavHost() {
    val navController = rememberNavController()
    val chatViewModel: ChatViewModel = viewModel()
    val authViewModel: AuthViewModel = viewModel()

    // Observe auth state for auto-login
    val authState = authViewModel.uiState

    // Keep chatViewModel in sync with auth token
    LaunchedEffect(authState.token) {
        if (authState.token != null) {
            chatViewModel.bearerToken = authState.token
        }
    }

    NavHost(
        navController = navController,
        startDestination = Routes.SPLASH
    ) {
        composable(Routes.SPLASH) {
            com.aarkaai.app.ui.splash.SplashScreen(
                onSplashFinished = {
                    val nextRoute = if (authState.isLoggedIn && authState.token != null) Routes.CHAT else Routes.AUTH
                    navController.navigate(nextRoute) {
                        popUpTo(Routes.SPLASH) { inclusive = true }
                    }
                }
            )
        }
        composable(Routes.AUTH) {
            AuthScreen(
                authViewModel = authViewModel,
                onAuthSuccess = { token ->
                    chatViewModel.bearerToken = token
                    val uid = authViewModel.uiState.userId ?: "user"
                    val uname = authViewModel.uiState.userName
                    chatViewModel.onUserLoggedIn(token, uid, uname)
                    navController.navigate(Routes.CHAT) {
                        popUpTo(Routes.AUTH) { inclusive = true }
                    }
                }
            )
        }

        composable(Routes.CHAT) {
            ChatScreen(
                viewModel = chatViewModel,
                onNavigateToSettings = { navController.navigate(Routes.SETTINGS) },
                onNavigateToSkills = { navController.navigate(Routes.SKILLS) },
                onNavigateToAuth = { navController.navigate(Routes.AUTH) },
                onLogout = {
                    chatViewModel.onUserLoggedOut()
                    authViewModel.logout()
                    navController.navigate(Routes.AUTH) {
                        popUpTo(0) { inclusive = true }
                    }
                }
            )
        }

        composable(Routes.SETTINGS) {
            com.aarkaai.app.ui.settings.SettingsScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Routes.SKILLS) {
            com.aarkaai.app.ui.skills.SkillsScreen(
                onNavigateBack = { navController.popBackStack() },
                onSkillSelect = { skillCommand ->
                    chatViewModel.sendMessage(skillCommand)
                }
            )
        }
    }
}
