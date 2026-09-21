package com.aarkaa.ai.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.Folder
import androidx.compose.material.icons.filled.QueryStats
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.ShowChart
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.aarkaa.ai.AarkaaApplication
import com.aarkaa.ai.core.theme.AarkaaAITheme
import com.aarkaa.ai.core.theme.AccentCyan
import com.aarkaa.ai.core.theme.DarkBackground
import com.aarkaa.ai.core.theme.DarkSurface
import com.aarkaa.ai.core.theme.TextMuted
import com.aarkaa.ai.ui.auth.AuthScreen
import com.aarkaa.ai.ui.chat.ChatScreen
import com.aarkaa.ai.ui.documents.DocumentManagerScreen
import com.aarkaa.ai.ui.navigation.Screen
import com.aarkaa.ai.ui.screener.ScreenerScreen
import com.aarkaa.ai.ui.settings.SettingsScreen
import com.aarkaa.ai.ui.skills.SkillsScreen
import com.aarkaa.ai.ui.strategy.OptionsStrategyScreen

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AarkaaAITheme {
                MainApp()
            }
        }
    }
}

@Composable
fun MainApp() {
    val navController = rememberNavController()
    val tokenManager = remember { AarkaaApplication.instance.tokenManager }
    val isAuthenticated = remember { mutableStateOf(tokenManager.isAuthenticated()) }

    if (!isAuthenticated.value) {
        AuthScreen(onAuthSuccess = {
            isAuthenticated.value = true
        })
        return
    }

    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    Scaffold(
        containerColor = DarkBackground,
        bottomBar = {
            NavigationBar(
                containerColor = DarkSurface
            ) {
                val items = listOf(
                    Screen.Chat to Icons.Default.Chat,
                    Screen.Screener to Icons.Default.QueryStats,
                    Screen.Strategy to Icons.Default.ShowChart,
                    Screen.Skills to Icons.Default.AutoAwesome,
                    Screen.Documents to Icons.Default.Folder,
                    Screen.Settings to Icons.Default.Settings
                )

                items.forEach { (screen, icon) ->
                    NavigationBarItem(
                        selected = currentRoute == screen.route,
                        onClick = {
                            navController.navigate(screen.route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(icon, contentDescription = screen.title) },
                        label = { Text(screen.title) },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = DarkBackground,
                            selectedTextColor = AccentCyan,
                            indicatorColor = AccentCyan,
                            unselectedIconColor = TextMuted,
                            unselectedTextColor = TextMuted
                        )
                    )
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Screen.Chat.route,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(Screen.Chat.route) { ChatScreen() }
            composable(Screen.Screener.route) { ScreenerScreen() }
            composable(Screen.Strategy.route) { OptionsStrategyScreen() }
            composable(Screen.Skills.route) { SkillsScreen() }
            composable(Screen.Documents.route) { DocumentManagerScreen() }
            composable(Screen.Settings.route) {
                SettingsScreen(onLogout = {
                    isAuthenticated.value = false
                })
            }
        }
    }
}
