package com.aarkaai.app.network

import com.google.gson.annotations.SerializedName

data class UserSettingsDto(
    @SerializedName("user_id") val userId: String? = null,
    @SerializedName("default_model") val defaultModel: String? = "aarka-2.0",
    @SerializedName("response_style") val responseStyle: String? = "balanced",
    @SerializedName("theme") val theme: String? = "light",
    @SerializedName("language") val language: String? = "en",
    @SerializedName("streaming_enabled") val streamingEnabled: Boolean = true,
    @SerializedName("reasoning_depth") val reasoningDepth: String? = "medium",
    @SerializedName("about_you") val aboutYou: String? = null,
    @SerializedName("system_directives") val systemDirectives: String? = null,
    @SerializedName("extended_thinking") val extendedThinking: Boolean = true,
    @SerializedName("thinking_budget") val thinkingBudget: Int = 4096,
    @SerializedName("web_search_enabled") val webSearchEnabled: Boolean = true,
    @SerializedName("deep_research_enabled") val deepResearchEnabled: Boolean = true,
    @SerializedName("market_data_enabled") val marketDataEnabled: Boolean = true,
    @SerializedName("connected_apps") val connectedApps: String? = "{}",
    // UI preference fields
    @SerializedName("density") val density: String? = "comfortable",
    @SerializedName("enter_to_send") val enterToSend: Boolean = true,
    @SerializedName("show_timestamps") val showTimestamps: Boolean = true,
    @SerializedName("incognito_chat") val incognitoChat: Boolean = false,
    @SerializedName("two_factor_enabled") val twoFactorEnabled: Boolean = false,
    @SerializedName("email_alerts") val emailAlerts: Boolean = true,
    @SerializedName("security_alerts") val securityAlerts: Boolean = true,
    @SerializedName("updated_at") val updatedAt: String? = null
)
