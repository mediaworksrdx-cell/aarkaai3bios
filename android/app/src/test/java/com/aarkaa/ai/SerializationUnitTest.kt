package com.aarkaa.ai

import com.aarkaa.ai.data.api.*
import kotlinx.serialization.json.Json
import org.junit.Assert.*
import org.junit.Test

class SerializationUnitTest {

    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
    }

    @Test
    fun testPromptRequestSerialization() {
        val req = PromptRequest(
            query = "Analyze RELIANCE.NS quarterly earnings",
            sessionId = "test-session-42",
            mode = "agent_path",
            modelOverride = "claude"
        )
        val encoded = json.encodeToString(PromptRequest.serializer(), req)
        assertTrue(encoded.contains(""query":"Analyze RELIANCE.NS quarterly earnings""))
        assertTrue(encoded.contains(""session_id":"test-session-42""))
        assertTrue(encoded.contains(""mode":"agent_path""))
    }

    @Test
    fun testTokenResponseDeserialization() {
        val rawJson = """
            {
                "access_token": "mock.jwt.token",
                "refresh_token": "mock.refresh.token",
                "token_type": "bearer",
                "user_id": "usr-12345",
                "name": "Enterprise Tester"
            }
        """.trimIndent()

        val resp = json.decodeFromString<TokenResponse>(rawJson)
        assertEquals("mock.jwt.token", resp.accessToken)
        assertEquals("mock.refresh.token", resp.refreshToken)
        assertEquals("usr-12345", resp.userId)
        assertEquals("Enterprise Tester", resp.name)
    }

    @Test
    fun testScreenerRequestSerialization() {
        val req = ScreenerAPIRequest(
            sector = "FINANCIAL_SERVICES",
            marketCapMin = 50000.0,
            limit = 10
        )
        val encoded = json.encodeToString(ScreenerAPIRequest.serializer(), req)
        assertTrue(encoded.contains(""sector":"FINANCIAL_SERVICES""))
        assertTrue(encoded.contains(""limit":10"))
    }
}
