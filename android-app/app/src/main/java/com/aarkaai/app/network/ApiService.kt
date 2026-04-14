package com.aarkaai.app.network

import retrofit2.http.Body
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.GET

// ──────── Request / Response models matching FastAPI schemas ────────

data class PromptRequest(
    val query: String,
    val session_id: String = "1",
    val context: Map<String, Any>? = null
)

data class PromptResponse(
    val response: String,
    val intent: String,
    val confidence: Double,
    val sources: List<String> = emptyList(),
    val detected_language: String = "en",
    val processing_time: Double = 0.0
)

data class AuthRequest(
    val email: String,
    val password: String,
    val name: String? = null
)

data class AuthResponse(
    val access_token: String,
    val token_type: String = "bearer",
    val user_id: String,
    val name: String? = null
)

data class HealthResponse(
    val status: String,
    val version: String,
    val modules: Map<String, Any> = emptyMap()
)

data class RlhfRequest(
    val user_id: String,
    val rating: Int,              // 1 = positive, -1 = negative
    val conversation_id: Int? = null,
    val correction: String? = null
)

data class RlhfResponse(
    val status: String,
    val message: String
)

// ──────── Retrofit API Definition ────────

interface ApiService {

    @POST("auth/register")
    suspend fun register(@Body request: AuthRequest): AuthResponse

    @POST("auth/login")
    suspend fun login(@Body request: AuthRequest): AuthResponse

    @POST("prompt")
    suspend fun sendPrompt(
        @Header("Authorization") token: String,
        @Body request: PromptRequest
    ): PromptResponse

    @POST("rlhf")
    suspend fun submitRlhf(
        @Header("Authorization") token: String,
        @Body request: RlhfRequest
    ): RlhfResponse

    @GET("health")
    suspend fun health(): HealthResponse
}
