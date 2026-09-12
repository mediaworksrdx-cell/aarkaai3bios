package com.aarkaai.app.data

import android.content.Context
import android.util.Log
import com.aarkaai.app.ui.chat.Conversation
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

class ConversationRepository(private val context: Context) {
    private val gson = Gson()
    private val TAG = "ConversationRepo"

    private fun getFile(userId: String?): File {
        val isAuthUser = !userId.isNullOrBlank() &&
                userId != "guest_user" &&
                !userId.startsWith("offline_guest") &&
                userId != "visitor"

        return if (isAuthUser) {
            val safeId = userId!!.replace(Regex("[^a-zA-Z0-9_-]"), "_")
            File(context.filesDir, "aarka_conv_${safeId}.json")
        } else {
            File(context.filesDir, "aarka_conv_guest.json")
        }
    }

    private fun checkLegacyMigration(targetFile: File, userId: String?) {
        try {
            val legacyFile = File(context.filesDir, "aarka_conversations.json")
            if (legacyFile.exists() && !targetFile.exists()) {
                legacyFile.copyTo(targetFile, overwrite = true)
                Log.i(TAG, "Migrated legacy aarka_conversations.json to ${targetFile.name}")
            }

            // If user logged in and user file doesn't exist, migrate guest conversations if present
            val isAuthUser = !userId.isNullOrBlank() &&
                    userId != "guest_user" &&
                    !userId.startsWith("offline_guest")
            if (isAuthUser && !targetFile.exists()) {
                val guestFile = File(context.filesDir, "aarka_conv_guest.json")
                if (guestFile.exists() && guestFile.length() > 0) {
                    guestFile.copyTo(targetFile, overwrite = true)
                    Log.i(TAG, "Migrated guest conversations to user file ${targetFile.name}")
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "Migration check warning: ${e.message}")
        }
    }

    suspend fun loadConversations(userId: String? = null): List<Conversation> = withContext(Dispatchers.IO) {
        try {
            val file = getFile(userId)
            checkLegacyMigration(file, userId)

            if (!file.exists() || file.length() == 0L) {
                return@withContext emptyList()
            }

            val json = file.readText(Charsets.UTF_8).trim()
            if (json.isBlank() || json == "[]") {
                return@withContext emptyList()
            }

            val type = object : TypeToken<List<Conversation>>() {}.type
            val result: List<Conversation>? = gson.fromJson(json, type)
            result?.filter { it.id.isNotBlank() } ?: emptyList()
        } catch (e: Exception) {
            Log.e(TAG, "Error loading conversations for user: $userId: ${e.message}", e)
            emptyList()
        }
    }

    suspend fun saveConversations(conversations: List<Conversation>, userId: String? = null) {
        withContext(Dispatchers.IO) {
            try {
                val file = getFile(userId)
                val json = gson.toJson(conversations)

                // Atomic file write using temporary file to prevent partial file corruption
                val tempFile = File(context.filesDir, "${file.name}.tmp")
                tempFile.writeText(json, Charsets.UTF_8)
                if (tempFile.exists()) {
                    if (file.exists()) {
                        file.delete()
                    }
                    tempFile.renameTo(file)
                }
                Unit
            } catch (e: Exception) {
                Log.e(TAG, "Error saving conversations for user: $userId: ${e.message}", e)
                Unit
            }
        }
    }

    suspend fun clearConversations(userId: String? = null) {
        withContext(Dispatchers.IO) {
            try {
                val file = getFile(userId)
                if (file.exists()) {
                    file.delete()
                }
                Unit
            } catch (e: Exception) {
                Log.e(TAG, "Error clearing conversations for user: $userId: ${e.message}", e)
                Unit
            }
        }
    }
}
