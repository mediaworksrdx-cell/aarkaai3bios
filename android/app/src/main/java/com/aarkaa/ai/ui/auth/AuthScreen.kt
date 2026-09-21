package com.aarkaa.ai.ui.auth

import android.content.Intent
import android.net.Uri
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
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aarkaa.ai.AarkaaApplication
import com.aarkaa.ai.core.theme.*
import com.aarkaa.ai.data.api.AarkaaApiService
import com.aarkaa.ai.data.api.UserCreate
import kotlinx.coroutines.launch

@Composable
fun AuthScreen(onAuthSuccess: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val api = remember { AarkaaApplication.instance.apiClient.createService<AarkaaApiService>() }
    val tokenManager = remember { AarkaaApplication.instance.tokenManager }

    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var name by remember { mutableStateOf("") }
    var isRegistering by remember { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(false) }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = DarkSurface),
            shape = RoundedCornerShape(16.dp)
        ) {
            Column(
                modifier = Modifier.padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "AARKAAI",
                    fontSize = 28.sp,
                    fontWeight = FontWeight.Bold,
                    color = AccentCyan
                )
                Text(
                    text = "Autonomous Agentic Intelligence",
                    fontSize = 13.sp,
                    color = TextSecondary,
                    modifier = Modifier.padding(bottom = 24.dp)
                )

                if (isRegistering) {
                    OutlinedTextField(
                        value = name,
                        onValueChange = { name = it },
                        label = { Text("Full Name") },
                        modifier = Modifier.fillMaxWidth(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedTextColor = TextPrimary,
                            unfocusedTextColor = TextPrimary,
                            focusedBorderColor = AccentCyan
                        )
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                }

                OutlinedTextField(
                    value = email,
                    onValueChange = { email = it },
                    label = { Text("Email Address") },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary,
                        focusedBorderColor = AccentCyan
                    )
                )
                Spacer(modifier = Modifier.height(12.dp))

                OutlinedTextField(
                    value = password,
                    onValueChange = { password = it },
                    label = { Text("Password") },
                    visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary,
                        focusedBorderColor = AccentCyan
                    )
                )
                Spacer(modifier = Modifier.height(20.dp))

                Button(
                    onClick = {
                        if (email.isBlank() || password.isBlank()) {
                            Toast.makeText(context, "Please enter email and password", Toast.LENGTH_SHORT).show()
                            return@Button
                        }
                        isLoading = true
                        scope.launch {
                            try {
                                val req = UserCreate(email = email.trim(), password = password, name = if (isRegistering) name.trim() else null)
                                val resp = if (isRegistering) api.register(req) else api.login(req)
                                tokenManager.saveTokens(resp.accessToken, resp.refreshToken, resp.userId, resp.name)
                                onAuthSuccess()
                            } catch (e: Exception) {
                                Toast.makeText(context, "Auth Error: " + (e.message ?: "Unknown error"), Toast.LENGTH_LONG).show()
                            } finally {
                                isLoading = false
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = AccentCyan),
                    shape = RoundedCornerShape(8.dp),
                    enabled = !isLoading
                ) {
                    if (isLoading) {
                        CircularProgressIndicator(modifier = Modifier.size(20.dp), color = DarkBackground)
                    } else {
                        Text(
                            text = if (isRegistering) "Create Account" else "Sign In",
                            color = DarkBackground,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                Spacer(modifier = Modifier.height(12.dp))

                // Guest / Visitor Token Button
                OutlinedButton(
                    onClick = {
                        isLoading = true
                        scope.launch {
                            try {
                                val resp = api.getVisitorToken()
                                tokenManager.saveTokens(resp.accessToken, resp.refreshToken, resp.userId, resp.name)
                                onAuthSuccess()
                            } catch (e: Exception) {
                                Toast.makeText(context, "Visitor Token Error: " + (e.message ?: "Failed"), Toast.LENGTH_LONG).show()
                            } finally {
                                isLoading = false
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("Continue as Guest (Visitor)", color = TextPrimary)
                }

                Spacer(modifier = Modifier.height(16.dp))

                // GitHub OAuth Button
                Button(
                    onClick = {
                        val browserIntent = Intent(
                            Intent.ACTION_VIEW,
                            Uri.parse("https://synthetixanalytics.com/auth/github/login")
                        )
                        context.startActivity(browserIntent)
                    },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = DarkSurfaceVariant),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("Sign in with GitHub", color = TextPrimary)
                }

                Spacer(modifier = Modifier.height(16.dp))

                TextButton(onClick = { isRegistering = !isRegistering }) {
                    Text(
                        text = if (isRegistering) "Already have an account? Sign In" else "Don't have an account? Register",
                        color = AccentCyan
                    )
                }
            }
        }
    }
}
