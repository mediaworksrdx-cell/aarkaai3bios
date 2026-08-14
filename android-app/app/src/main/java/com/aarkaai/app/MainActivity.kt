package com.aarkaai.app

import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import com.aarkaai.app.ui.navigation.AarkaaiNavHost
import com.aarkaai.app.ui.theme.AarkaaiTheme
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)           // MUST be first

        try {
            installSplashScreen()                   // after super, before setContent
        } catch (e: Exception) {
            logCrash("installSplashScreen", e)
        }


        try {
            enableEdgeToEdge()
        } catch (e: Exception) {
            logCrash("enableEdgeToEdge", e)
        }

        try {
            setContent {
                AarkaaiTheme {
                    Surface(modifier = Modifier.fillMaxSize()) {
                        AarkaaiNavHost()
                    }
                }
            }
        } catch (e: Exception) {
            logCrash("setContent", e)
        }
        
        handleDeepLink(intent)
    }

    override fun onNewIntent(intent: android.content.Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleDeepLink(intent)
    }

    private fun handleDeepLink(intent: android.content.Intent?) {
        val data: android.net.Uri? = intent?.data
        if (data != null && data.scheme == "aarkaai" && data.host == "auth-callback") {
            val token = data.getQueryParameter("token")
            val userId = data.getQueryParameter("user_id")
            val name = data.getQueryParameter("name") ?: "GitHub User"
            
            if (token != null && userId != null) {
                // Initialize ViewModel instance and login session directly
                val authViewModel = androidx.lifecycle.ViewModelProvider(this)[com.aarkaai.app.ui.auth.AuthViewModel::class.java]
                authViewModel.handleExternalAuth(token, userId, name)
                Toast.makeText(this, "Welcome, $name!", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun logCrash(phase: String, e: Exception) {
        val sw = StringWriter()
        e.printStackTrace(PrintWriter(sw))
        val msg = "CRASH in $phase: ${e.javaClass.simpleName}: ${e.message}"
        Log.e("AARKAAI", msg)
        Log.e("AARKAAI", sw.toString())

        try {
            val crashFile = File(getExternalFilesDir(null), "crash.log")
            crashFile.appendText("\n=== $phase CRASH ===\n$msg\n$sw\n")
            Toast.makeText(this, msg, Toast.LENGTH_LONG).show()
        } catch (_: Exception) { }
    }
}
