package com.aarkaai.app.ui.settings

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.aarkaai.app.data.SettingsRepository
import com.aarkaai.app.data.TokenManager
import com.aarkaai.app.network.UserSettingsDto
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

data class SettingsUiState(
    val language: String = "en",
    val density: String = "comfortable",
    val enterToSend: Boolean = true,
    val showTimestamps: Boolean = true,
    val streamingResponses: Boolean = true,
    val incognitoChat: Boolean = false,
    val defaultModel: String = "aarka-2.0",
    val defaultEffort: String = "medium",
    val webSearchEnabled: Boolean = true,
    val deepResearchEnabled: Boolean = true,
    val marketDataEnabled: Boolean = true,
    val twoFactorEnabled: Boolean = false,
    val emailAlerts: Boolean = true,
    val securityAlerts: Boolean = true,
    val isSaving: Boolean = false,
    val savedSuccess: Boolean = false,
    val errorMessage: String? = null
)

class SettingsViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = SettingsRepository(application)
    private val tokenManager = TokenManager(application)

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    private var authToken: String? = null

    init {
        viewModelScope.launch {
            tokenManager.token.collectLatest { token ->
                authToken = token
                if (token != null) {
                    val remote = repository.fetchRemoteSettings(token)
                    if (remote != null) {
                        applyDto(remote)
                    }
                }
            }
        }

        viewModelScope.launch {
            repository.localSettings.collectLatest { local ->
                applyDto(local)
            }
        }
    }

    private fun applyDto(dto: UserSettingsDto) {
        _uiState.update { current ->
            current.copy(
                language = dto.language ?: current.language,
                density = dto.density ?: current.density,
                enterToSend = dto.enterToSend,
                showTimestamps = dto.showTimestamps,
                streamingResponses = dto.streamingEnabled,
                incognitoChat = dto.incognitoChat,
                defaultModel = dto.defaultModel ?: current.defaultModel,
                defaultEffort = dto.reasoningDepth ?: current.defaultEffort,
                webSearchEnabled = dto.webSearchEnabled,
                deepResearchEnabled = dto.deepResearchEnabled,
                marketDataEnabled = dto.marketDataEnabled,
                twoFactorEnabled = dto.twoFactorEnabled,
                emailAlerts = dto.emailAlerts,
                securityAlerts = dto.securityAlerts
            )
        }
    }

    fun setLanguage(lang: String) = _uiState.update { it.copy(language = lang) }
    fun setDensity(density: String) = _uiState.update { it.copy(density = density) }
    fun setEnterToSend(enabled: Boolean) = _uiState.update { it.copy(enterToSend = enabled) }
    fun setShowTimestamps(enabled: Boolean) = _uiState.update { it.copy(showTimestamps = enabled) }
    fun setStreamingResponses(enabled: Boolean) = _uiState.update { it.copy(streamingResponses = enabled) }
    fun setIncognitoChat(enabled: Boolean) = _uiState.update { it.copy(incognitoChat = enabled) }
    fun setDefaultModel(model: String) = _uiState.update { it.copy(defaultModel = model) }
    fun setDefaultEffort(effort: String) = _uiState.update { it.copy(defaultEffort = effort) }
    fun setWebSearch(enabled: Boolean) = _uiState.update { it.copy(webSearchEnabled = enabled) }
    fun setDeepResearch(enabled: Boolean) = _uiState.update { it.copy(deepResearchEnabled = enabled) }
    fun setMarketData(enabled: Boolean) = _uiState.update { it.copy(marketDataEnabled = enabled) }
    fun setTwoFactor(enabled: Boolean) = _uiState.update { it.copy(twoFactorEnabled = enabled) }
    fun setEmailAlerts(enabled: Boolean) = _uiState.update { it.copy(emailAlerts = enabled) }
    fun setSecurityAlerts(enabled: Boolean) = _uiState.update { it.copy(securityAlerts = enabled) }

    fun saveSettings() {
        val state = _uiState.value
        val dto = UserSettingsDto(
            language = state.language,
            density = state.density,
            enterToSend = state.enterToSend,
            showTimestamps = state.showTimestamps,
            streamingEnabled = state.streamingResponses,
            incognitoChat = state.incognitoChat,
            defaultModel = state.defaultModel,
            reasoningDepth = state.defaultEffort,
            webSearchEnabled = state.webSearchEnabled,
            deepResearchEnabled = state.deepResearchEnabled,
            marketDataEnabled = state.marketDataEnabled,
            twoFactorEnabled = state.twoFactorEnabled,
            emailAlerts = state.emailAlerts,
            securityAlerts = state.securityAlerts
        )

        viewModelScope.launch {
            _uiState.update { it.copy(isSaving = true, errorMessage = null) }
            repository.saveLocalSettings(dto)

            val token = authToken
            if (!token.isNullOrBlank()) {
                try {
                    repository.updateRemoteSettings(token, dto)
                } catch (e: Exception) {
                    _uiState.update { it.copy(errorMessage = "Saved locally. Server sync failed.") }
                }
            }
            _uiState.update { it.copy(isSaving = false, savedSuccess = true) }
            kotlinx.coroutines.delay(2000)
            _uiState.update { it.copy(savedSuccess = false) }
        }
    }
}
