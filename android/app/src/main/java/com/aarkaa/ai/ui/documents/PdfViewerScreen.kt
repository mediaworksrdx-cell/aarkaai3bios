package com.aarkaa.ai.ui.documents

import android.graphics.Bitmap
import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aarkaa.ai.core.theme.DarkBackground
import com.aarkaa.ai.core.theme.TextPrimary
import java.io.File

@Composable
fun PdfViewerScreen(pdfFile: File) {
    var pageBitmaps by remember { mutableStateOf<List<Bitmap>>(emptyList()) }

    LaunchedEffect(pdfFile) {
        if (!pdfFile.exists()) return@LaunchedEffect
        val pfd = ParcelFileDescriptor.open(pdfFile, ParcelFileDescriptor.MODE_READ_ONLY)
        val renderer = PdfRenderer(pfd)
        val bitmaps = mutableListOf<Bitmap>()

        for (i in 0 until renderer.pageCount) {
            val page = renderer.openPage(i)
            val bitmap = Bitmap.createBitmap(page.width * 2, page.height * 2, Bitmap.Config.ARGB_8888)
            page.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
            bitmaps.add(bitmap)
            page.close()
        }
        renderer.close()
        pfd.close()
        pageBitmaps = bitmaps
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .padding(16.dp)
    ) {
        Text("Executive Report Viewer (Exact 6-Page Budget)", color = TextPrimary, fontSize = 16.sp)
        Spacer(modifier = Modifier.height(12.dp))

        LazyColumn {
            itemsIndexed(pageBitmaps) { index, bitmap ->
                Column(modifier = Modifier.padding(bottom = 16.dp)) {
                    Text("Page " + (index + 1) + " of " + pageBitmaps.size, color = TextPrimary, fontSize = 12.sp)
                    Spacer(modifier = Modifier.height(4.dp))
                    Image(
                        bitmap = bitmap.asImageBitmap(),
                        contentDescription = "Page " + (index + 1),
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(8.dp)),
                        contentScale = ContentScale.FillWidth
                    )
                }
            }
        }
    }
}
