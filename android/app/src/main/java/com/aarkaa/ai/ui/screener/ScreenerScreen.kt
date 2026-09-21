package com.aarkaa.ai.ui.screener

import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aarkaa.ai.AarkaaApplication
import com.aarkaa.ai.core.theme.*
import com.aarkaa.ai.data.api.AarkaaApiService
import com.aarkaa.ai.data.api.MarketRegimeResponse
import com.aarkaa.ai.data.api.ScreenerAPIRequest
import com.aarkaa.ai.data.api.StockScoreProfile
import kotlinx.coroutines.launch

@Composable
fun ScreenerScreen() {
    val scope = rememberCoroutineScope()
    val api = remember { AarkaaApplication.instance.apiClient.createService<AarkaaApiService>() }

    var regime by remember { mutableStateOf<MarketRegimeResponse?>(null) }
    val stockResults = remember { mutableStateListOf<StockScoreProfile>() }
    var isLoading by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        isLoading = true
        scope.launch {
            try {
                regime = api.getMarketRegime()
                val resp = api.screenStocks(ScreenerAPIRequest(limit = 25))
                stockResults.clear()
                stockResults.addAll(resp.results)
            } catch (e: Exception) {
                // Fallback state
            } finally {
                isLoading = false
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .padding(16.dp)
    ) {
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = DarkSurface),
            shape = RoundedCornerShape(12.dp)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text("Market Regime Classification", color = TextSecondary, fontSize = 12.sp)
                    Text(
                        text = regime?.regime?.replace("_", " ")?.uppercase() ?: "RANGE BOUND",
                        color = AccentGreen,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
                Text("Benchmark: " + (regime?.benchmark ?: "NIFTY 50"), color = TextMuted, fontSize = 12.sp)
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        Text(
            text = "Multi-Factor Institutional Screener",
            color = TextPrimary,
            fontSize = 18.sp,
            fontWeight = FontWeight.SemiBold
        )

        Spacer(modifier = Modifier.height(12.dp))

        if (isLoading) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = AccentCyan)
            }
        } else {
            val horizontalScrollState = rememberScrollState()

            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .clip(RoundedCornerShape(8.dp))
                    .background(DarkSurface)
            ) {
                Column(modifier = Modifier.horizontalScroll(horizontalScrollState)) {
                    Row(
                        modifier = Modifier
                            .background(DarkSurfaceVariant)
                            .padding(horizontal = 12.dp, vertical = 10.dp)
                    ) {
                        Text("Symbol", color = AccentCyan, fontWeight = FontWeight.Bold, modifier = Modifier.width(90.dp))
                        Text("Signal", color = TextPrimary, fontWeight = FontWeight.Bold, modifier = Modifier.width(80.dp))
                        Text("Score", color = TextPrimary, fontWeight = FontWeight.Bold, modifier = Modifier.width(60.dp))
                        Text("Price", color = TextPrimary, fontWeight = FontWeight.Bold, modifier = Modifier.width(80.dp))
                        Text("P/E", color = TextPrimary, fontWeight = FontWeight.Bold, modifier = Modifier.width(60.dp))
                        Text("ROE", color = TextPrimary, fontWeight = FontWeight.Bold, modifier = Modifier.width(60.dp))
                        Text("RSI", color = TextPrimary, fontWeight = FontWeight.Bold, modifier = Modifier.width(60.dp))
                    }

                    LazyColumn {
                        items(stockResults) { stock ->
                            Row(
                                modifier = Modifier
                                    .padding(horizontal = 12.dp, vertical = 10.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(stock.symbol, color = TextPrimary, fontWeight = FontWeight.Medium, modifier = Modifier.width(90.dp))
                                Text(
                                    text = stock.signal,
                                    color = if (stock.signal.contains("BUY")) AccentGreen else if (stock.signal.contains("SELL")) AccentRed else AccentAmber,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.width(80.dp)
                                )
                                Text(String.format("%.1f", stock.compositeScore), color = TextPrimary, modifier = Modifier.width(60.dp))
                                Text("₹" + String.format("%.1f", stock.currentPrice), color = TextPrimary, modifier = Modifier.width(80.dp))
                                Text(stock.pToE?.let { String.format("%.1f", it) } ?: "-", color = TextSecondary, modifier = Modifier.width(60.dp))
                                Text(stock.roe?.let { String.format("%.1f%%", it) } ?: "-", color = TextSecondary, modifier = Modifier.width(60.dp))
                                Text(stock.rsi?.let { String.format("%.1f", it) } ?: "-", color = TextSecondary, modifier = Modifier.width(60.dp))
                            }
                            HorizontalDivider(color = DarkBackground, thickness = 1.dp)
                        }
                    }
                }
            }
        }
    }
}
