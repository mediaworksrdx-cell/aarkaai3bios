package com.aarkaa.ai.core.network

import com.aarkaa.ai.core.security.TokenManager
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import okhttp3.Authenticator
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import okhttp3.Route

class TokenAuthenticator(
    private val tokenManager: TokenManager,
    private val baseUrl: String = "https://synthetixanalytics.com"
) : Authenticator {

    private val client = OkHttpClient()

    override fun authenticate(route: Route?, response: Response): Request? {
        if (responseCount(response) >= 2) return null

        synchronized(this) {
            val currentToken = tokenManager.getAccessToken()
            val requestToken = response.request.header("Authorization")?.removePrefix("Bearer ")

            if (currentToken != null && currentToken != requestToken) {
                return response.request.newBuilder()
                    .header("Authorization", "Bearer " + currentToken)
                    .build()
            }

            val refreshToken = tokenManager.getRefreshToken() ?: return null

            val refreshPayload = "{\"refresh_token\": \"" + refreshToken + "\"}"
            val refreshRequest = Request.Builder()
                .url(baseUrl + "/auth/refresh")
                .post(refreshPayload.toRequestBody("application/json".toMediaType()))
                .build()

            try {
                val refreshResponse = client.newCall(refreshRequest).execute()
                if (refreshResponse.isSuccessful) {
                    val body = refreshResponse.body?.string() ?: return null
                    val json = Json.parseToJsonElement(body).jsonObject
                    val newAccessToken = json["access_token"]?.jsonPrimitive?.content ?: return null
                    val newRefreshToken = json["refresh_token"]?.jsonPrimitive?.content ?: refreshToken

                    tokenManager.saveTokens(
                        accessToken = newAccessToken,
                        refreshToken = newRefreshToken,
                        userId = tokenManager.getUserId(),
                        name = tokenManager.getUserName()
                    )

                    return response.request.newBuilder()
                        .header("Authorization", "Bearer " + newAccessToken)
                        .build()
                } else {
                    tokenManager.clear()
                }
            } catch (e: Exception) {
                return null
            }
        }
        return null
    }

    private fun responseCount(response: Response): Int {
        var result = 1
        var prior = response.priorResponse
        while (prior != null) {
            result++
            prior = prior.priorResponse
        }
        return result
    }
}
