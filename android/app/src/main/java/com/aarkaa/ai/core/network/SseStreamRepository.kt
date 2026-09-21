package com.aarkaa.ai.core.network

import com.aarkaa.ai.data.api.PromptRequest
import com.aarkaa.ai.data.api.StreamEvent
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.flowOn
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import okhttp3.sse.EventSource
import okhttp3.sse.EventSourceListener
import okhttp3.sse.EventSources
import java.io.IOException

class SseStreamRepository(
    private val apiClient: AarkaaApiClient
) {
    private val json = Json { ignoreUnknownKeys = true; isLenient = true }

    fun streamPrompt(
        request: PromptRequest,
        mode: String = "production"
    ): Flow<StreamEvent> = callbackFlow {
        apiClient.authInterceptor.currentMode = mode

        val requestBody = json.encodeToString(PromptRequest.serializer(), request)
            .toRequestBody("application/json".toMediaType())

        val httpRequest = Request.Builder()
            .url(apiClient.baseUrl + "prompt/stream")
            .header("Accept", "text/event-stream")
            .header("Cache-Control", "no-cache")
            .post(requestBody)
            .build()

        val listener = object : EventSourceListener() {
            override fun onEvent(eventSource: EventSource, id: String?, type: String?, data: String) {
                try {
                    val event = json.decodeFromString<StreamEvent>(data)
                    trySend(event)
                } catch (e: Exception) {
                    trySend(StreamEvent.Token(content = data))
                }
            }

            override fun onClosed(eventSource: EventSource) {
                close()
            }

            override fun onFailure(eventSource: EventSource, t: Throwable?, response: Response?) {
                close(t ?: IOException("SSE connection dropped with code: " + (response?.code ?: -1)))
            }
        }

        val factory = EventSources.createFactory(apiClient.okHttpClient)
        val eventSource = factory.newEventSource(httpRequest, listener)

        awaitClose {
            eventSource.cancel()
        }
    }.flowOn(Dispatchers.IO)
}
