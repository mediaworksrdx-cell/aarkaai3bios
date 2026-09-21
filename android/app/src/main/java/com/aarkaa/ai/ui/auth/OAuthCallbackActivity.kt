package com.aarkaa.ai.ui.auth

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import com.aarkaa.ai.AarkaaApplication
import com.aarkaa.ai.ui.MainActivity

class OAuthCallbackActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val uri = intent?.data
        if (uri != null && uri.scheme == "aarkaai" && uri.host == "auth-callback") {
            val token = uri.getQueryParameter("token")
            val userId = uri.getQueryParameter("user_id")
            val name = uri.getQueryParameter("name")

            if (!token.isNullOrEmpty()) {
                AarkaaApplication.instance.tokenManager.saveTokens(
                    accessToken = token,
                    refreshToken = null,
                    userId = userId,
                    name = name
                )
                Toast.makeText(this, "Signed in as " + (name ?: "User"), Toast.LENGTH_SHORT).show()

                val mainIntent = Intent(this, MainActivity::class.java).apply {
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                }
                startActivity(mainIntent)
                finish()
                return
            }
        }

        Toast.makeText(this, "Authentication failed or was cancelled.", Toast.LENGTH_LONG).show()
        finish()
    }
}
