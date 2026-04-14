package com.aarkaai.app.ui.auth

import android.app.Application
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.aarkaai.app.data.TokenManager
import com.aarkaai.app.network.AuthRequest
import com.aarkaai.app.network.RetrofitClient
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

data class AuthUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val token: String? = null,
    val userId: String? = null,
    val userName: String? = null,
    val isLoggedIn: Boolean = false,
    val isCheckingToken: Boolean = true  // True while checking stored token
)

class AuthViewModel(application: Application) : AndroidViewModel(application) {

    private val tokenManager = TokenManager(application)

    var uiState by mutableStateOf(AuthUiState())
        private set

    init {
        // Check if a stored token exists (auto-login)
        viewModelScope.launch {
            val storedToken = tokenManager.token.first()
            if (storedToken != null) {
                uiState = uiState.copy(
                    token = storedToken,
                    userId = tokenManager.userId.first(),
                    userName = tokenManager.userName.first(),
                    isLoggedIn = true,
                    isCheckingToken = false
                )
            } else {
                uiState = uiState.copy(isCheckingToken = false)
            }
        }
    }

    fun login(email: String, password: String) {
        if (email.isBlank() || password.isBlank()) {
            uiState = uiState.copy(error = "Please fill in all fields")
            return
        }

        uiState = uiState.copy(isLoading = true, error = null)

        viewModelScope.launch {
            try {
                val res = RetrofitClient.api.login(AuthRequest(email = email, password = password))
                // Persist the token
                tokenManager.saveAuth(res.access_token, res.user_id, res.name)
                uiState = uiState.copy(
                    isLoading = false,
                    token = res.access_token,
                    userId = res.user_id,
                    userName = res.name,
                    isLoggedIn = true,
                    error = null
                )
            } catch (e: Exception) {
                uiState = uiState.copy(
                    isLoading = false,
                    error = e.localizedMessage ?: "Login failed"
                )
            }
        }
    }

    fun register(email: String, password: String, name: String) {
        if (email.isBlank() || password.isBlank()) {
            uiState = uiState.copy(error = "Please fill in all fields")
            return
        }

        uiState = uiState.copy(isLoading = true, error = null)

        viewModelScope.launch {
            try {
                val res = RetrofitClient.api.register(
                    AuthRequest(email = email, password = password, name = name.ifBlank { null })
                )
                // Persist the token
                tokenManager.saveAuth(res.access_token, res.user_id, res.name)
                uiState = uiState.copy(
                    isLoading = false,
                    token = res.access_token,
                    userId = res.user_id,
                    userName = res.name,
                    isLoggedIn = true,
                    error = null
                )
            } catch (e: Exception) {
                uiState = uiState.copy(
                    isLoading = false,
                    error = e.localizedMessage ?: "Registration failed"
                )
            }
        }
    }

    fun logout() {
        viewModelScope.launch {
            tokenManager.clearAuth()
            uiState = AuthUiState(isCheckingToken = false)
        }
    }

    fun clearError() {
        uiState = uiState.copy(error = null)
    }
}
