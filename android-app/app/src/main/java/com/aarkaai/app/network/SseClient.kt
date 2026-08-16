package com.aarkaai.app.network

import com.aarkaai.app.BuildConfig
import com.google.gson.Gson
import com.google.gson.JsonObject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okio.BufferedSource
import java.io.IOException

class SseAuthException : Exception("Unauthorized")

object SseClient {
    private const val BASE_URL = BuildConfig.BASE_URL
    private val gson = Gson()
    
    fun streamPrompt(token: String, query: String, sessionId: String): Flow<String> = flow {
        val jsonRequest = JsonObject().apply {
            addProperty("query", query)
            addProperty("session_id", sessionId)
        }
        val requestBody = jsonRequest.toString().toRequestBody("application/json".toMediaType())
        
        val request = Request.Builder()
            .url("${BASE_URL}prompt/stream")
            .header("Authorization", token)
            .post(requestBody)
            .build()
            
        RetrofitClient.okHttpClient.newCall(request).execute().use { response ->
            if (!response.isSuccessful) {
                if (response.code == 401 || response.code == 403) {
                    throw SseAuthException()
                }
                throw IOException("Unexpected code $response")
            }
            
            val source: BufferedSource = response.body?.source() ?: throw IOException("Empty body")
            
            while (!source.exhausted()) {
                val line = source.readUtf8Line() ?: break
                if (line.startsWith("data: ")) {
                    val data = line.removePrefix("data: ").trim()
                    if (data == "[DONE]") {
                        break
                    }
                    try {
                        val json = gson.fromJson(data, JsonObject::class.java)
                        val type = json.get("type")?.asString
                        if (type == "content") {
                            val tokenStr = json.get("token")?.asString ?: ""
                            emit(tokenStr)
                        } else if (type == "done") {
                            break
                        }
                    } catch (e: Exception) {
                        // ignore malformed json or unexpected format
                    }
                }
            }
        }
    }.flowOn(Dispatchers.IO)
}
