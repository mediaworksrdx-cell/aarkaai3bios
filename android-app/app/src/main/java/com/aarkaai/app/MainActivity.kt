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
