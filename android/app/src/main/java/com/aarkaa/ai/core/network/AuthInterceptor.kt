package com.aarkaa.ai.core.network

import com.aarkaa.ai.core.security.TokenManager
import okhttp3.Interceptor
import okhttp3.Response

class AuthInterceptor(private val tokenManager: TokenManager) : Interceptor {

    @Volatile
    var currentMode: String = "production"

    override fun intercept(chain: Interceptor.Chain): Response {
        val original = chain.request()
        val builder = original.newBuilder()

        val token = tokenManager.getAccessToken()
        if (!token.isNullOrEmpty()) {
            builder.header("Authorization", "Bearer $token")
        }

        builder.header("x-aarkaai-mode", currentMode)
        builder.header("User-Agent", "AarkaaAI-Android/2.0.0 (OkHttp)")

        return chain.proceed(builder.build())
    }
}
