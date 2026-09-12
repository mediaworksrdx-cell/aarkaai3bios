package com.aarkaai.app.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.aarkaai.app.network.RetrofitClient
import com.aarkaai.app.network.UserSettingsDto
import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext

private val Context.settingsDataStore by preferencesDataStore(name = "aarkaai_settings_prefs")

class SettingsRepository(private val context: Context) {
    private val gson = Gson()

    companion object {
        private val SETTINGS_JSON_KEY = stringPreferencesKey("aarka_user_settings_v2")
    }

    val localSettings: Flow<UserSettingsDto> = context.settingsDataStore.data.map { prefs ->
        val json = prefs[SETTINGS_JSON_KEY]
        if (!json.isNullOrBlank()) {
            try {
                gson.fromJson(json, UserSettingsDto::class.java) ?: UserSettingsDto()
            } catch (e: Exception) {
                UserSettingsDto()
            }
        } else {
            UserSettingsDto()
        }
    }

    suspend fun saveLocalSettings(settings: UserSettingsDto) = withContext(Dispatchers.IO) {
        try {
            val json = gson.toJson(settings)
            context.settingsDataStore.edit { prefs ->
                prefs[SETTINGS_JSON_KEY] = json
            }
        } catch (e: Exception) {
        }
    }

    suspend fun fetchRemoteSettings(token: String): UserSettingsDto? = withContext(Dispatchers.IO) {
        try {
            val authHeader = if (token.startsWith("Bearer ")) token else "Bearer $token"
            val remote = RetrofitClient.api.getSettings(authHeader)
            saveLocalSettings(remote)
            remote
        } catch (e: Exception) {
            null
        }
    }

    suspend fun updateRemoteSettings(token: String, settings: UserSettingsDto): UserSettingsDto = withContext(Dispatchers.IO) {
        val authHeader = if (token.startsWith("Bearer ")) token else "Bearer $token"
        val response = RetrofitClient.api.updateSettings(authHeader, settings)
        saveLocalSettings(response)
        response
    }
}
