package com.aarkaa.ai.data.api

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

// ─── Authentication Models ───────────────────────────────────────────────────

@Serializable
data class UserCreate(
    val email: String,
    val password: String,
    val name: String? = null
)

@Serializable
data class TokenResponse(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String? = null,
    @SerialName("token_type") val tokenType: String = "bearer",
    @SerialName("user_id") val userId: String? = null,
    val name: String? = null
)

@Serializable
data class RefreshRequest(
    @SerialName("refresh_token") val refreshToken: String
)

@Serializable
data class LogoutRequest(
    @SerialName("access_token") val accessToken: String? = null,
    @SerialName("refresh_token") val refreshToken: String? = null
)

@Serializable
data class GoogleAuthRequest(
    @SerialName("id_token") val idToken: String? = null,
    @SerialName("access_token") val accessToken: String? = null
)

// ─── Inference & Chat Models ──────────────────────────────────────────────────

@Serializable
data class PromptRequest(
    val query: String,
    @SerialName("session_id") val sessionId: String = "1",
    val mode: String? = "production",
    @SerialName("model_override") val modelOverride: String? = null
)

@Serializable
data class PromptResponse(
    val response: String,
    val intent: String = "general",
    val confidence: Float = 1.0f,
    val sources: List<String> = emptyList(),
    @SerialName("detected_language") val detectedLanguage: String = "en",
    @SerialName("processing_time") val processingTime: Float = 0.0f
)

@Serializable
sealed class StreamEvent {
    @Serializable
    @SerialName("token")
    data class Token(val content: String) : StreamEvent()

    @Serializable
    @SerialName("thinking")
    data class Thinking(val content: String) : StreamEvent()

    @Serializable
    @SerialName("tool")
    data class ToolCall(val name: String, val input: String) : StreamEvent()

    @Serializable
    @SerialName("status")
    data class Status(val message: String) : StreamEvent()

    @Serializable
    @SerialName("error")
    data class Error(val detail: String) : StreamEvent()

    @Serializable
    @SerialName("done")
    data class Done(val totalTokens: Int = 0) : StreamEvent()
}

@Serializable
data class HealthResponse(
    val status: String,
    val version: String = "2.0.0",
    val modules: Map<String, String> = emptyMap()
)

// ─── RLHF Feedback ────────────────────────────────────────────────────────────

@Serializable
data class RLHFRequest(
    @SerialName("conversation_id") val conversationId: String? = null,
    val rating: Int, // 1 for positive, -1 for negative
    val correction: String? = null
)

// ─── Institutional Screener Models ───────────────────────────────────────────

@Serializable
data class ScreenerAPIRequest(
    val sector: String? = null,
    @SerialName("market_cap_min") val marketCapMin: Double? = null,
    @SerialName("market_cap_max") val marketCapMax: Double? = null,
    @SerialName("min_composite_score") val minCompositeScore: Float? = null,
    val strategies: List<String> = emptyList(),
    val limit: Int = 20
)

@Serializable
data class StockScoreProfile(
    val symbol: String,
    val companyName: String = "",
    val sector: String = "",
    val marketCap: Double = 0.0,
    val currentPrice: Double = 0.0,
    val compositeScore: Float = 0.0f,
    val signal: String = "HOLD",
    val conviction: String = "MEDIUM",
    val pToE: Double? = null,
    val debtToEquity: Double? = null,
    val roe: Double? = null,
    val rsi: Double? = null,
    val regime: String = "RANGE_BOUND"
)

@Serializable
data class ScreenerResponse(
    val count: Int,
    val results: List<StockScoreProfile> = emptyList(),
    @SerialName("regime_detected") val regimeDetected: String = "range_bound",
    @SerialName("processing_time") val processingTime: Float = 0.0f
)

@Serializable
data class ScreenerStrategyInfo(
    val id: String,
    val name: String,
    val category: String,
    val description: String,
    val factors: List<String> = emptyList()
)

@Serializable
data class MarketRegimeResponse(
    val regime: String,
    val benchmark: String = "^NSEI",
    val indicators: Map<String, Double> = emptyMap(),
    val note: String = ""
)

@Serializable
data class SectorRanking(
    val sector: String,
    @SerialName("display_name") val displayName: String,
    @SerialName("stock_count") val stockCount: Int
)

@Serializable
data class ProvenanceResponse(
    val status: String,
    val framework: String,
    val contract: String
)

// ─── Technical Analysis & Options Strategy ────────────────────────────────────

@Serializable
data class StrategyRequest(
    val symbol: String,
    @SerialName("risk_reward") val riskReward: Float = 5.0f,
    val period: String = "6mo"
)

@Serializable
data class StrategyResponse(
    val symbol: String,
    val signal: String,
    val indicators: Map<String, Double> = emptyMap(),
    val strategy: JsonObject? = null,
    @SerialName("technical_summary") val technicalSummary: String = "",
    @SerialName("strategy_summary") val strategySummary: String = "",
    @SerialName("processing_time") val processingTime: Float = 0.0f
)

// ─── Agent Skills Models ──────────────────────────────────────────────────────

@Serializable
data class SkillModel(
    val name: String,
    val content: String
)

@Serializable
data class SkillSummary(
    val name: String,
    val description: String = ""
)

@Serializable
data class TestRequestModel(
    val prompt: String
)

@Serializable
data class SkillVersion(
    val version: Int,
    @SerialName("created_at") val createdAt: String,
    val summary: String = ""
)

// ─── User Settings Models ─────────────────────────────────────────────────────

@Serializable
data class UserSettingsResponse(
    @SerialName("user_id") val userId: String,
    @SerialName("default_model") val defaultModel: String = "aarka-2.0",
    @SerialName("response_style") val responseStyle: String = "balanced",
    val theme: String = "dark",
    val language: String = "en",
    @SerialName("streaming_enabled") val streamingEnabled: Boolean = true,
    @SerialName("reasoning_depth") val reasoningDepth: String = "balanced",
    @SerialName("extended_thinking") val extendedThinking: Boolean = true,
    @SerialName("thinking_budget") val thinkingBudget: Int = 4096,
    @SerialName("web_search_enabled") val webSearchEnabled: Boolean = true,
    @SerialName("deep_research_enabled") val deepResearchEnabled: Boolean = true,
    @SerialName("market_data_enabled") val marketDataEnabled: Boolean = true
)

@Serializable
data class UserSettingsUpdate(
    @SerialName("default_model") val defaultModel: String? = null,
    @SerialName("response_style") val responseStyle: String? = null,
    val theme: String? = null,
    val language: String? = null,
    @SerialName("streaming_enabled") val streamingEnabled: Boolean? = null,
    @SerialName("reasoning_depth") val reasoningDepth: String? = null,
    @SerialName("extended_thinking") val extendedThinking: Boolean? = null,
    @SerialName("thinking_budget") val thinkingBudget: Int? = null
)

// ─── Subscription Models ──────────────────────────────────────────────────────

@Serializable
data class SubscriptionInfo(
    val tier: String = "free",
    @SerialName("strategy_queries_remaining") val strategyQueriesRemaining: Int = 15,
    @SerialName("reset_in_hours") val resetInHours: Int = 5,
    val allowed: Boolean = true
)

// ─── Document / Upload Models ─────────────────────────────────────────────────

@Serializable
data class FileUploadResponse(
    val status: String,
    val filename: String,
    @SerialName("size_bytes") val sizeBytes: Long,
    val path: String,
    @SerialName("user_isolated") val userIsolated: Boolean = true
)
