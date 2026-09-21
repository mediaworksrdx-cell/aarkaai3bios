package com.aarkaa.ai

import android.app.Application
import com.aarkaa.ai.core.network.AarkaaApiClient
import com.aarkaa.ai.core.security.TokenManager

class AarkaaApplication : Application() {

    lateinit var tokenManager: TokenManager
        private set

    lateinit var apiClient: AarkaaApiClient
        private set

    override fun onCreate() {
        super.onCreate()
        instance = this
        tokenManager = TokenManager(this)
        apiClient = AarkaaApiClient(tokenManager)
    }

    companion object {
        lateinit var instance: AarkaaApplication
            private set
    }
}
