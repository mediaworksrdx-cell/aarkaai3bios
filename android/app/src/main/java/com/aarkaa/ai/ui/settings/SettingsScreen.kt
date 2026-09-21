package com.aarkaa.ai.ui.settings

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aarkaa.ai.AarkaaApplication
import com.aarkaa.ai.core.theme.*
import com.aarkaa.ai.data.api.AarkaaApiService
import com.aarkaa.ai.data.api.SubscriptionInfo
import com.aarkaa.ai.data.api.UserSettingsResponse
import com.aarkaa.ai.data.api.UserSettingsUpdate
import kotlinx.coroutines.launch

@Composable
fun SettingsScreen(onLogout: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val api = remember { AarkaaApplication.instance.apiClient.createService<AarkaaApiService>() }
    val tokenManager = remember { AarkaaApplication.instance.tokenManager }

    var settings by remember { mutableStateOf<UserSettingsResponse?>(null) }
    var subscription by remember { mutableStateOf<SubscriptionInfo?>(null) }
    var streamingEnabled by remember { mutableStateOf(true) }
    var extendedThinking by remember { mutableStateOf(true) }
    var biometricEnabled by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        scope.launch {
            try {
                settings = api.getSettings()
                subscription = api.getSubscription()
                streamingEnabled = settings?.streamingEnabled ?: true
                extendedThinking = settings?.extendedThinking ?: true
            } catch (e: Exception) {
                // Keep local defaults
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .padding(16.dp)
    ) {
        Text("Account & System Preferences", color = TextPrimary, fontSize = 20.sp, fontWeight = FontWeight.Bold)
        Spacer(modifier = Modifier.height(16.dp))

        Card(
            colors = CardDefaults.cardColors(containerColor = DarkSurface),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Subscription Tier", color = TextSecondary, fontSize = 12.sp)
                Text(
                    text = (subscription?.tier ?: "Free Tier").uppercase(),
                    color = AccentCyan,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "Queries remaining today: " + (subscription?.strategyQueriesRemaining ?: 15),
                    color = TextPrimary,
                    fontSize = 13.sp
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        Card(
            colors = CardDefaults.cardColors(containerColor = DarkSurface),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Token Streaming (SSE)", color = TextPrimary)
                    Switch(
                        checked = streamingEnabled,
                        onCheckedChange = {
                            streamingEnabled = it
                            scope.launch {
                                try {
                                    api.updateSettings(UserSettingsUpdate(streamingEnabled = it))
                                } catch (e: Exception) {}
                            }
                        }
                    )
                }

                HorizontalDivider(color = DarkBackground, modifier = Modifier.padding(vertical = 8.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Extended DAG Thinking", color = TextPrimary)
                    Switch(
                        checked = extendedThinking,
                        onCheckedChange = {
                            extendedThinking = it
                            scope.launch {
                                try {
                                    api.updateSettings(UserSettingsUpdate(extendedThinking = it))
                                } catch (e: Exception) {}
                            }
                        }
                    )
                }

                HorizontalDivider(color = DarkBackground, modifier = Modifier.padding(vertical = 8.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Biometric Security Lock", color = TextPrimary)
                    Switch(
                        checked = biometricEnabled,
                        onCheckedChange = { biometricEnabled = it }
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = {
                tokenManager.clear()
                onLogout()
                Toast.makeText(context, "Signed out", Toast.LENGTH_SHORT).show()
            },
            colors = ButtonDefaults.buttonColors(containerColor = AccentRed),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Sign Out", color = TextPrimary, fontWeight = FontWeight.Bold)
        }
    }
}
