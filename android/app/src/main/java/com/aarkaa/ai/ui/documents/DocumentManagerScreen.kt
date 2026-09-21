package com.aarkaa.ai.ui.documents

import android.app.DownloadManager
import android.content.Context
import android.net.Uri
import android.os.Environment
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.UploadFile
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aarkaa.ai.AarkaaApplication
import com.aarkaa.ai.core.theme.*
import com.aarkaa.ai.data.api.AarkaaApiService
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody

@Composable
fun DocumentManagerScreen() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val api = remember { AarkaaApplication.instance.apiClient.createService<AarkaaApiService>() }
    val token = remember { AarkaaApplication.instance.tokenManager.getAccessToken() }

    var downloadFileName by remember { mutableStateOf("portfolio_report.pdf") }
    var isUploading by remember { mutableStateOf(false) }

    val filePickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        if (uri != null) {
            isUploading = true
            scope.launch {
                try {
                    val inputStream = context.contentResolver.openInputStream(uri)
                    val bytes = inputStream?.readBytes() ?: return@launch
                    val requestFile = bytes.toRequestBody("application/octet-stream".toMediaTypeOrNull())
                    val body = MultipartBody.Part.createFormData("file", "uploaded_doc.pdf", requestFile)

                    val resp = api.uploadFile(body)
                    Toast.makeText(context, "Uploaded: " + resp.filename, Toast.LENGTH_SHORT).show()
                } catch (e: Exception) {
                    Toast.makeText(context, "Upload failed: " + e.message, Toast.LENGTH_LONG).show()
                } finally {
                    isUploading = false
                }
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .padding(16.dp)
    ) {
        Text("Sandboxed Workspace & Reports", color = TextPrimary, fontSize = 20.sp, fontWeight = FontWeight.Bold)
        Spacer(modifier = Modifier.height(16.dp))

        Card(
            colors = CardDefaults.cardColors(containerColor = DarkSurface),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Upload Document to Agent Sandbox", color = TextPrimary, fontWeight = FontWeight.SemiBold)
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    "Upload PDF, CSV, XLSX, or TXT files directly to your user-isolated sandbox directory.",
                    color = TextSecondary,
                    fontSize = 13.sp
                )
                Spacer(modifier = Modifier.height(16.dp))
                Button(
                    onClick = { filePickerLauncher.launch("*/*") },
                    colors = ButtonDefaults.buttonColors(containerColor = AccentCyan),
                    enabled = !isUploading
                ) {
                    Icon(Icons.Default.UploadFile, contentDescription = null, tint = DarkBackground)
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Select & Upload File", color = DarkBackground, fontWeight = FontWeight.Bold)
                }
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        Card(
            colors = CardDefaults.cardColors(containerColor = DarkSurface),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Download Generated 6-Page Report", color = TextPrimary, fontWeight = FontWeight.SemiBold)
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = downloadFileName,
                    onValueChange = { downloadFileName = it },
                    label = { Text("Report Filename") },
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(16.dp))
                Button(
                    onClick = {
                        val url = "https://synthetixanalytics.com/download/" + downloadFileName.trim()
                        val request = DownloadManager.Request(Uri.parse(url)).apply {
                            setTitle("Aarkaa Report: " + downloadFileName)
                            setDescription("Downloading report from AARKAAI")
                            setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                            setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, downloadFileName)
                            if (token != null) {
                                addRequestHeader("Authorization", "Bearer " + token)
                            }
                        }
                        val dm = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
                        dm.enqueue(request)
                        Toast.makeText(context, "Download enqueued", Toast.LENGTH_SHORT).show()
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = AccentGreen)
                ) {
                    Icon(Icons.Default.Download, contentDescription = null, tint = DarkBackground)
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Download to Device", color = DarkBackground, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}
