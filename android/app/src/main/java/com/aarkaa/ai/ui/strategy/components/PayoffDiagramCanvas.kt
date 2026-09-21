package com.aarkaa.ai.ui.strategy.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import com.aarkaa.ai.core.theme.*

@Composable
fun PayoffDiagramCanvas(
    isBullish: Boolean = true,
    modifier: Modifier = Modifier
) {
    Canvas(
        modifier = modifier
            .fillMaxWidth()
            .height(200.dp)
    ) {
        val width = size.width
        val height = size.height
        val midY = height / 2

        drawLine(
            color = BorderSubtle,
            start = Offset(0f, midY),
            end = Offset(width, midY),
            strokeWidth = 2f
        )

        val path = Path()
        if (isBullish) {
            val startY = midY + 40f
            val breakEvenX = width * 0.45f
            val maxProfitX = width * 0.75f
            val maxProfitY = midY - 60f

            path.moveTo(0f, startY)
            path.lineTo(breakEvenX - 60f, startY)
            path.lineTo(maxProfitX, maxProfitY)
            path.lineTo(width, maxProfitY)
        } else {
            val maxProfitY = midY - 60f
            val startY = midY + 40f

            path.moveTo(0f, maxProfitY)
            path.lineTo(width * 0.35f, maxProfitY)
            path.lineTo(width * 0.65f, startY)
            path.lineTo(width, startY)
        }

        drawPath(
            path = path,
            color = AccentCyan,
            style = Stroke(width = 4f)
        )
    }
}
