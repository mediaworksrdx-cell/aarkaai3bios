package com.aarkaai.app

import android.app.Application
import android.util.Log
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Custom Application class that captures uncaught exceptions to a log file.
 * The crash log is written to: /sdcard/Android/data/com.aarkaai.app/files/crash.log
 */
class AarkaaiApplication : Application() {

    override fun onCreate() {
        super.onCreate()

        // Set up a global crash handler
        val defaultHandler = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            try {
                val sw = StringWriter()
                val pw = PrintWriter(sw)
                throwable.printStackTrace(pw)
                val stackTrace = sw.toString()

                val timestamp = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US).format(Date())
                val logContent = """
                    |=== AARKAAI CRASH LOG ===
                    |Time: $timestamp
                    |Thread: ${thread.name}
                    |Exception: ${throwable.javaClass.name}
                    |Message: ${throwable.message}
                    |
                    |Stack Trace:
                    |$stackTrace
                """.trimMargin()

                // Write to app-specific external storage (no permission needed)
                val crashFile = File(getExternalFilesDir(null), "crash.log")
                crashFile.writeText(logContent)

                Log.e("AARKAAI", "Crash logged to: ${crashFile.absolutePath}")
                Log.e("AARKAAI", logContent)
            } catch (e: Exception) {
                Log.e("AARKAAI", "Failed to write crash log", e)
            }

            // Pass to default handler (shows "app has stopped" dialog)
            defaultHandler?.uncaughtException(thread, throwable)
        }
    }
}
