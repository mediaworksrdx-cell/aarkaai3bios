package com.aarkaai.app.ui.navigation

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.aarkaai.app.ui.auth.AuthScreen
import com.aarkaai.app.ui.auth.AuthViewModel
import com.aarkaai.app.ui.chat.ChatScreen
import com.aarkaai.app.ui.chat.ChatViewModel

object Routes {
    const val AUTH = "auth"
    const val CHAT = "chat"
    const val LOADING = "loading"
}

@Composable
fun AarkaaiNavHost() {
    val navController = rememberNavController()
    val chatViewModel: ChatViewModel = viewModel()
    val authViewModel: AuthViewModel = viewModel()

    // Observe auth state for auto-login
    val authState = authViewModel.uiState

    // Determine start destination based on stored token
    LaunchedEffect(authState.isCheckingToken, authState.isLoggedIn) {
        if (!authState.isCheckingToken) {
            if (authState.isLoggedIn && authState.token != null) {
                chatViewModel.bearerToken = authState.token!!
                navController.navigate(Routes.CHAT) {
                    popUpTo(0) { inclusive = true }
                }
            } else {
                if (navController.currentDestination?.route == Routes.LOADING) {
                    navController.navigate(Routes.AUTH) {
                        popUpTo(0) { inclusive = true }
                    }
                }
            }
        }
    }

    NavHost(
        navController = navController,
        startDestination = Routes.LOADING
    ) {
        // Loading screen while checking stored token
        composable(Routes.LOADING) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(color = MaterialTheme.colorScheme.primary)
            }
        }

        composable(Routes.AUTH) {
            AuthScreen(
                authViewModel = authViewModel,
                onAuthSuccess = { token ->
                    chatViewModel.bearerToken = token
                    navController.navigate(Routes.CHAT) {
                        popUpTo(0) { inclusive = true }
                    }
                }
            )
        }

        composable(Routes.CHAT) {
            ChatScreen(
                viewModel = chatViewModel,
                onLogout = {
                    authViewModel.logout()
                    navController.navigate(Routes.AUTH) {
                        popUpTo(0) { inclusive = true }
                    }
                }
            )
        }
    }
}
