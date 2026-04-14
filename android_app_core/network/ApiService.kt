package com.example.aarkaai.network

import retrofit2.http.Body
import retrofit2.http.Header
import retrofit2.http.POST

// 1. Define Request Body mirroring FastAPI Pydantic Model
data class PromptRequest(
    val query: String,
    val session_id: String = "1",
    val context: Map<String, Any>? = null
)

// 2. Define Response Body mirroring FastAPI Pydantic Model
data class PromptResponse(
    val response: String,
    val intent: String,
    val confidence: Double,
    val sources: List<String> = emptyList(),
    val detected_language: String = "en",
    val processing_time: Double = 0.0
)

// 3. Define the Retrofit API Interface
interface ApiService {
    @POST("prompt")
    suspend fun sendPrompt(
        @Header("Authorization") token: String,
        @Body request: PromptRequest
    ): PromptResponse
}
