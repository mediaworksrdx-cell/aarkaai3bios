package com.aarkaa.ai.data.api

import okhttp3.MultipartBody
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.*

interface AarkaaApiService {

    // ─── Authentication Endpoints ─────────────────────────────────────────────
    @POST("auth/register")
    suspend fun register(@Body req: UserCreate): TokenResponse

    @POST("auth/login")
    suspend fun login(@Body req: UserCreate): TokenResponse

    @POST("auth/visitor-token")
    suspend fun getVisitorToken(): TokenResponse

    @POST("auth/refresh")
    suspend fun refreshAccessToken(@Body req: RefreshRequest): TokenResponse

    @POST("auth/logout")
    suspend fun logout(@Body req: LogoutRequest): Map<String, String>

    @POST("auth/google/verify")
    suspend fun verifyGoogleToken(@Body req: GoogleAuthRequest): TokenResponse

    // ─── Core AI Inference ────────────────────────────────────────────────────
    @POST("prompt")
    suspend fun prompt(@Body req: PromptRequest): PromptResponse

    @GET("health")
    suspend fun checkHealth(): HealthResponse

    @POST("rlhf")
    suspend fun submitRlhf(@Body req: RLHFRequest): Map<String, String>

    // ─── Institutional Screener ───────────────────────────────────────────────
    @POST("screener")
    suspend fun screenStocks(@Body req: ScreenerAPIRequest): ScreenerResponse

    @GET("screener/strategies")
    suspend fun listScreenerStrategies(): List<ScreenerStrategyInfo>

    @GET("screener/regime")
    suspend fun getMarketRegime(): MarketRegimeResponse

    @GET("screener/sectors")
    suspend fun getSectors(): List<SectorRanking>

    @GET("screener/provenance")
    suspend fun getProvenance(): ProvenanceResponse

    // ─── Technical Analysis & Options Strategy ────────────────────────────────
    @POST("strategy")
    suspend fun getStrategy(@Body req: StrategyRequest): StrategyResponse

    // ─── Agent Skills ─────────────────────────────────────────────────────────
    @GET("skills")
    suspend fun listSkills(): List<SkillSummary>

    @POST("skills")
    suspend fun createSkill(@Body req: SkillModel): Map<String, String>

    @GET("skills/{name}")
    suspend fun getSkill(@Path("name") name: String): SkillModel

    @PUT("skills/{name}")
    suspend fun updateSkill(@Path("name") name: String, @Body req: SkillModel): Map<String, String>

    @DELETE("skills/{name}")
    suspend fun deleteSkill(@Path("name") name: String): Map<String, String>

    @GET("skills/{name}/versions")
    suspend fun getSkillVersions(@Path("name") name: String): Map<String, List<SkillVersion>>

    // ─── User Settings ────────────────────────────────────────────────────────
    @GET("settings")
    suspend fun getSettings(): UserSettingsResponse

    @PUT("settings")
    suspend fun updateSettings(@Body req: UserSettingsUpdate): UserSettingsResponse

    // ─── Subscription ─────────────────────────────────────────────────────────
    @GET("subscription")
    suspend fun getSubscription(): SubscriptionInfo

    // ─── Documents & File Sandboxing ──────────────────────────────────────────
    @Multipart
    @POST("upload")
    suspend fun uploadFile(@Part file: MultipartBody.Part): FileUploadResponse

    @Streaming
    @GET("download/{filename}")
    suspend fun downloadFile(@Path("filename") filename: String): Response<ResponseBody>
}
