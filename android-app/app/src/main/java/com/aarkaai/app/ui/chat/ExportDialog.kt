package com.aarkaai.app.ui.chat

import android.content.Context
import android.content.Intent
import android.graphics.Canvas
import android.graphics.Color as AndroidColor
import android.graphics.Paint
import android.graphics.RectF
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import android.os.Build
import android.text.Layout
import android.text.StaticLayout
import android.text.TextPaint
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowForwardIos
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import com.aarkaai.app.ui.theme.*
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun ExportDialog(
    conversationTitle: String,
    messages: List<ChatMessage>,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = BgSecondary,
        shape = RoundedCornerShape(20.dp),
        title = {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(32.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(AccentMuted)
                        .border(1.dp, AccentBorder, RoundedCornerShape(8.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Outlined.IosShare,
                        contentDescription = null,
                        tint = AccentPrimary,
                        modifier = Modifier.size(16.dp)
                    )
                }
                Text(
                    text = "Export Conversation",
                    fontWeight = FontWeight.Bold,
                    fontSize = 17.sp,
                    color = TextPrimary
                )
            }
        },
        text = {
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Text(
                    text = "Choose a document format to export this conversation:",
                    fontSize = 12.sp,
                    color = TextSecondary,
                    modifier = Modifier.padding(bottom = 2.dp)
                )

                // 1. PDF Document (.pdf)
                ExportOptionItem(
                    title = "PDF Document (.pdf)",
                    subtitle = "Formatted multi-page document with executive styling",
                    icon = Icons.Outlined.PictureAsPdf,
                    accentColor = Color(0xFFD96645),
                    badge = "PDF",
                    onClick = {
                        exportAsPdf(context, conversationTitle, messages)
                        onDismiss()
                    }
                )

                // 2. Word Document (.doc)
                ExportOptionItem(
                    title = "Word Document (.doc)",
                    subtitle = "Microsoft Word & Office compatible structured document",
                    icon = Icons.Outlined.Article,
                    accentColor = Color(0xFF2563EB),
                    badge = "DOC",
                    onClick = {
                        exportAsWord(context, conversationTitle, messages)
                        onDismiss()
                    }
                )
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("Close", color = TextSecondary, fontWeight = FontWeight.SemiBold)
            }
        }
    )
}

@Composable
private fun ExportOptionItem(
    title: String,
    subtitle: String,
    icon: ImageVector,
    accentColor: Color,
    badge: String?,
    onClick: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .border(1.dp, BorderColor, RoundedCornerShape(10.dp))
            .clickable(onClick = onClick),
        color = BgPrimary,
        shape = RoundedCornerShape(10.dp)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 9.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = accentColor,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = title,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = TextPrimary
                    )
                    if (badge != null) {
                        Spacer(modifier = Modifier.width(6.dp))
                        Surface(
                            color = accentColor.copy(alpha = 0.12f),
                            shape = RoundedCornerShape(4.dp)
                        ) {
                            Text(
                                text = badge,
                                fontSize = 8.5.sp,
                                fontWeight = FontWeight.Bold,
                                color = accentColor,
                                modifier = Modifier.padding(horizontal = 5.dp, vertical = 1.dp)
                            )
                        }
                    }
                }
                Text(
                    text = subtitle,
                    fontSize = 10.sp,
                    color = TextTertiary,
                    maxLines = 1
                )
            }
            Icon(
                imageVector = Icons.AutoMirrored.Outlined.ArrowForwardIos,
                contentDescription = null,
                tint = TextTertiary,
                modifier = Modifier.size(11.dp)
            )
        }
    }
}

fun exportAsPdf(context: Context, title: String, messages: List<ChatMessage>) {
    if (messages.isEmpty()) {
        Toast.makeText(context, "No messages to export", Toast.LENGTH_SHORT).show()
        return
    }

    try {
        val pdfDoc = PdfDocument()
        val pageWidth = 595
        val pageHeight = 842
        val marginX = 40f
        val contentWidth = (pageWidth - (marginX * 2)).toInt()
        val topMargin = 45f
        val bottomMargin = pageHeight - 50f

        var pageNum = 1
        var pageInfo = PdfDocument.PageInfo.Builder(pageWidth, pageHeight, pageNum).create()
        var page = pdfDoc.startPage(pageInfo)
        var canvas = page.canvas

        val titlePaint = Paint().apply {
            color = AndroidColor.parseColor("#0F172A")
            textSize = 17f
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            isAntiAlias = true
        }

        val brandPaint = Paint().apply {
            color = AndroidColor.parseColor("#C15F3D")
            textSize = 10f
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            isAntiAlias = true
        }

        val metaPaint = Paint().apply {
            color = AndroidColor.parseColor("#64748B")
            textSize = 8.5f
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.NORMAL)
            isAntiAlias = true
        }

        val dividerPaint = Paint().apply {
            color = AndroidColor.parseColor("#E2E8F0")
            strokeWidth = 1f
            style = Paint.Style.STROKE
            isAntiAlias = true
        }

        val accentBarPaint = Paint().apply {
            color = AndroidColor.parseColor("#C15F3D")
            style = Paint.Style.FILL
            isAntiAlias = true
        }

        val footerPaint = Paint().apply {
            color = AndroidColor.parseColor("#94A3B8")
            textSize = 8f
            isAntiAlias = true
        }

        val userBadgePaint = Paint().apply {
            color = AndroidColor.parseColor("#475569")
            textSize = 8.5f
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            isAntiAlias = true
        }

        val aarkaBadgePaint = Paint().apply {
            color = AndroidColor.parseColor("#C15F3D")
            textSize = 8.5f
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            isAntiAlias = true
        }

        val userBgPaint = Paint().apply {
            color = AndroidColor.parseColor("#F8FAFC")
            style = Paint.Style.FILL
            isAntiAlias = true
        }

        val aarkaBgPaint = Paint().apply {
            color = AndroidColor.parseColor("#FFF7ED")
            style = Paint.Style.FILL
            isAntiAlias = true
        }

        val bodyTextPaint = TextPaint().apply {
            color = AndroidColor.parseColor("#1E293B")
            textSize = 9.5f
            isAntiAlias = true
        }

        // Draw top accent bar
        canvas.drawRect(0f, 0f, pageWidth.toFloat(), 5f, accentBarPaint)

        var yPos = topMargin

        // Header on Page 1
        canvas.drawText("AARKA AI", marginX, yPos + 10f, brandPaint)
        yPos += 22f
        canvas.drawText(title.take(45), marginX, yPos + 10f, titlePaint)
        yPos += 24f

        val dateFormat = SimpleDateFormat("MMM dd, yyyy • HH:mm", Locale.getDefault())
        val dateStr = dateFormat.format(Date())
        val metaLine = "Export Date: $dateStr  |  Messages: ${messages.size}"
        canvas.drawText(metaLine, marginX, yPos + 8f, metaPaint)
        yPos += 18f

        canvas.drawLine(marginX, yPos, pageWidth - marginX, yPos, dividerPaint)
        yPos += 20f

        fun drawFooter(c: Canvas, num: Int) {
            c.drawLine(marginX, bottomMargin + 10f, pageWidth - marginX, bottomMargin + 10f, dividerPaint)
            c.drawText("Aarka AI • Synthetix Analytics Confidential", marginX, bottomMargin + 24f, footerPaint)
            val pText = "Page $num"
            val pWidth = footerPaint.measureText(pText)
            c.drawText(pText, pageWidth - marginX - pWidth, bottomMargin + 24f, footerPaint)
        }

        for (msg in messages) {
            val isUser = msg.isUser
            val speakerLabel = if (isUser) "USER" else "AARKA AI"
            val badgeTextPaint = if (isUser) userBadgePaint else aarkaBadgePaint
            val bubbleBgPaint = if (isUser) userBgPaint else aarkaBgPaint
            val accentLinePaint = if (isUser) userBadgePaint else aarkaBadgePaint

            val rawParagraphs = msg.text.split("\n\n").filter { it.isNotBlank() }
            val textToRender = if (rawParagraphs.isEmpty()) listOf(msg.text) else rawParagraphs

            // Check page break for speaker row
            if (yPos + 40f > bottomMargin) {
                drawFooter(canvas, pageNum)
                pdfDoc.finishPage(page)
                pageNum++
                pageInfo = PdfDocument.PageInfo.Builder(pageWidth, pageHeight, pageNum).create()
                page = pdfDoc.startPage(pageInfo)
                canvas = page.canvas
                canvas.drawRect(0f, 0f, pageWidth.toFloat(), 4f, accentBarPaint)
                yPos = topMargin
            }

            // Draw Speaker Row
            val timeStr = SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date(msg.timestamp))
            canvas.drawText(speakerLabel, marginX + 4f, yPos + 10f, badgeTextPaint)
            val timeWidth = metaPaint.measureText(timeStr)
            canvas.drawText(timeStr, pageWidth - marginX - timeWidth, yPos + 10f, metaPaint)
            yPos += 16f

            for (p in textToRender) {
                val layout = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    StaticLayout.Builder.obtain(p, 0, p.length, bodyTextPaint, contentWidth - 16)
                        .setAlignment(Layout.Alignment.ALIGN_NORMAL)
                        .setLineSpacing(0f, 1.25f)
                        .setIncludePad(false)
                        .build()
                } else {
                    @Suppress("DEPRECATION")
                    StaticLayout(p, bodyTextPaint, contentWidth - 16, Layout.Alignment.ALIGN_NORMAL, 1.25f, 0f, false)
                }

                val pHeight = layout.height.toFloat()

                // Check page break
                if (yPos + pHeight + 20f > bottomMargin) {
                    drawFooter(canvas, pageNum)
                    pdfDoc.finishPage(page)
                    pageNum++
                    pageInfo = PdfDocument.PageInfo.Builder(pageWidth, pageHeight, pageNum).create()
                    page = pdfDoc.startPage(pageInfo)
                    canvas = page.canvas
                    canvas.drawRect(0f, 0f, pageWidth.toFloat(), 4f, accentBarPaint)
                    yPos = topMargin
                }

                // Draw background card
                val cardRect = RectF(marginX, yPos, pageWidth - marginX, yPos + pHeight + 12f)
                canvas.drawRoundRect(cardRect, 4f, 4f, bubbleBgPaint)
                canvas.drawRect(marginX, yPos, marginX + 3f, yPos + pHeight + 12f, accentLinePaint)

                canvas.save()
                canvas.translate(marginX + 8f, yPos + 6f)
                layout.draw(canvas)
                canvas.restore()

                yPos += pHeight + 18f
            }

            yPos += 8f
        }

        drawFooter(canvas, pageNum)
        pdfDoc.finishPage(page)

        val exportDir = File(context.cacheDir, "exports").apply { mkdirs() }
        val cleanTitle = title.replace(Regex("[^a-zA-Z0-9_-]"), "_").take(25).ifEmpty { "conversation" }
        val pdfFile = File(exportDir, "AarkaAI_${cleanTitle}.pdf")
        FileOutputStream(pdfFile).use { out ->
            pdfDoc.writeTo(out)
        }
        pdfDoc.close()

        val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", pdfFile)
        val shareIntent = Intent(Intent.ACTION_SEND).apply {
            type = "application/pdf"
            putExtra(Intent.EXTRA_STREAM, uri)
            putExtra(Intent.EXTRA_TITLE, pdfFile.name)
            putExtra(Intent.EXTRA_SUBJECT, "Aarka AI - $title (PDF)")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(Intent.createChooser(shareIntent, "Export PDF Document"))
    } catch (e: Exception) {
        e.printStackTrace()
        Toast.makeText(context, "Failed to export PDF: ${e.localizedMessage}", Toast.LENGTH_LONG).show()
    }
}

private fun escapeHtml(text: String): String {
    return text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")
        .replace("'", "&#39;")
}

private fun formatMessageForWord(raw: String): String {
    val escaped = escapeHtml(raw)
    val withCode = escaped.replace(Regex("```(\\w*)\\n?([\\s\\S]*?)```")) { match ->
        val lang = match.groupValues[1]
        val code = match.groupValues[2]
        "<pre><code class='$lang'>$code</code></pre>"
    }
    val paragraphs = withCode.split("\n\n").map { p ->
        if (p.startsWith("<pre>") && p.endsWith("</pre>")) p
        else "<p>${p.replace("\n", "<br/>")}</p>"
    }
    return paragraphs.joinToString("\n")
}

fun exportAsWord(context: Context, title: String, messages: List<ChatMessage>) {
    if (messages.isEmpty()) {
        Toast.makeText(context, "No messages to export", Toast.LENGTH_SHORT).show()
        return
    }

    try {
        val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault())
        val dateStr = dateFormat.format(Date())
        val cleanTitle = title.replace(Regex("[^a-zA-Z0-9_-]"), "_").take(25).ifEmpty { "conversation" }

        val sb = StringBuilder()
        sb.append("<!DOCTYPE html>\n")
        sb.append("<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>\n")
        sb.append("<head>\n<meta charset='utf-8'>\n<title>").append(escapeHtml(title)).append("</title>\n")
        sb.append("<style>\n")
        sb.append("  body { font-family: 'Segoe UI', Calibri, Arial, sans-serif; font-size: 11pt; color: #1e293b; line-height: 1.6; margin: 36pt 48pt; background: #ffffff; }\n")
        sb.append("  .doc-header { border-bottom: 2.5pt solid #C15F3D; padding-bottom: 12pt; margin-bottom: 20pt; }\n")
        sb.append("  .brand { font-size: 11pt; font-weight: bold; color: #C15F3D; letter-spacing: 0.5pt; text-transform: uppercase; }\n")
        sb.append("  .title { font-size: 20pt; font-weight: bold; color: #0f172a; margin: 4pt 0 8pt 0; }\n")
        sb.append("  .meta { font-size: 9.5pt; color: #64748b; margin: 0; }\n")
        sb.append("  .card { margin-bottom: 16pt; padding: 12pt 16pt; border-radius: 6pt; }\n")
        sb.append("  .user-card { background: #f8fafc; border: 1pt solid #e2e8f0; border-left: 4pt solid #475569; }\n")
        sb.append("  .aarka-card { background: #fffaf5; border: 1pt solid #fed7aa; border-left: 4pt solid #C15F3D; }\n")
        sb.append("  .speaker-row { margin-bottom: 6pt; display: flex; justify-content: space-between; font-size: 9pt; }\n")
        sb.append("  .speaker-user { font-weight: bold; color: #475569; text-transform: uppercase; letter-spacing: 0.5pt; }\n")
        sb.append("  .speaker-aarka { font-weight: bold; color: #C15F3D; text-transform: uppercase; letter-spacing: 0.5pt; }\n")
        sb.append("  .timestamp { color: #94a3b8; }\n")
        sb.append("  .content { font-size: 10.5pt; color: #1e293b; }\n")
        sb.append("  .content p { margin: 0 0 8pt 0; }\n")
        sb.append("  .content p:last-child { margin-bottom: 0; }\n")
        sb.append("  pre { background: #0f172a; color: #f8fafc; padding: 10pt; border-radius: 4pt; font-family: 'Consolas', monospace; font-size: 9.5pt; overflow-x: auto; }\n")
        sb.append("  code { font-family: 'Consolas', monospace; background: #f1f5f9; padding: 1pt 4pt; border-radius: 3pt; font-size: 9.5pt; color: #0f172a; }\n")
        sb.append("  pre code { background: transparent; padding: 0; color: inherit; }\n")
        sb.append("  .footer { margin-top: 32pt; padding-top: 12pt; border-top: 1pt solid #e2e8f0; font-size: 8.5pt; color: #94a3b8; text-align: center; }\n")
        sb.append("</style>\n</head>\n<body>\n")

        sb.append("<div class='doc-header'>\n")
        sb.append("  <div class='brand'>Aarka AI</div>\n")
        sb.append("  <div class='title'>").append(escapeHtml(title)).append("</div>\n")
        sb.append("  <div class='meta'>Exported on ").append(dateStr).append("  |  Total Messages: ").append(messages.size).append("</div>\n")
        sb.append("</div>\n")

        for (msg in messages) {
            val isUser = msg.isUser
            val cardClass = if (isUser) "user-card" else "aarka-card"
            val speakerClass = if (isUser) "speaker-user" else "speaker-aarka"
            val speakerName = if (isUser) "User" else "Aarka AI"
            val msgTime = SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date(msg.timestamp))

            sb.append("<div class='card ").append(cardClass).append("'>\n")
            sb.append("  <div class='speaker-row'>\n")
            sb.append("    <span class='").append(speakerClass).append("'>").append(speakerName).append("</span>\n")
            sb.append("    <span class='timestamp'>").append(msgTime).append("</span>\n")
            sb.append("  </div>\n")
            sb.append("  <div class='content'>\n")

            val formattedContent = formatMessageForWord(msg.text)
            sb.append(formattedContent)

            sb.append("  </div>\n")
            sb.append("</div>\n")
        }

        sb.append("<div class='footer'>Aarka AI • Generated by Synthetix Analytics • Confidential</div>\n")
        sb.append("</body>\n</html>\n")

        val exportDir = File(context.cacheDir, "exports").apply { mkdirs() }
        val docFile = File(exportDir, "AarkaAI_${cleanTitle}.doc")
        docFile.writeText(sb.toString(), Charsets.UTF_8)

        val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", docFile)
        val shareIntent = Intent(Intent.ACTION_SEND).apply {
            type = "application/msword"
            putExtra(Intent.EXTRA_STREAM, uri)
            putExtra(Intent.EXTRA_TITLE, docFile.name)
            putExtra(Intent.EXTRA_SUBJECT, "Aarka AI - $title (Word Document)")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(Intent.createChooser(shareIntent, "Export Word Document"))
    } catch (e: Exception) {
        e.printStackTrace()
        Toast.makeText(context, "Failed to export Word document: ${e.localizedMessage}", Toast.LENGTH_LONG).show()
    }
}
