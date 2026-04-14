package com.aarkaai.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import com.aarkaai.app.ui.navigation.AarkaaiNavHost
import com.aarkaai.app.ui.theme.AarkaaiTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            AarkaaiTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    AarkaaiNavHost()
                }
            }
        }
    }
}
