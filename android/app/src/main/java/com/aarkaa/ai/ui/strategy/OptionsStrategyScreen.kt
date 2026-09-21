package com.aarkaa.ai.ui.strategy

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
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
import com.aarkaa.ai.data.api.StrategyRequest
import com.aarkaa.ai.data.api.StrategyResponse
import com.aarkaa.ai.ui.strategy.components.PayoffDiagramCanvas
import kotlinx.coroutines.launch

@Composable
fun OptionsStrategyScreen() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val api = remember { AarkaaApplication.instance.apiClient.createService<AarkaaApiService>() }

    var tickerSymbol by remember { mutableStateOf("RELIANCE.NS") }
    var strategyResponse by remember { mutableStateOf<StrategyResponse?>(null) }
    var isLoading by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .padding(16.dp)
    ) {
        Text("Options Strategy & Technical Signal", color = TextPrimary, fontSize = 20.sp, fontWeight = FontWeight.Bold)
        Spacer(modifier = Modifier.height(12.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedTextField(
                value = tickerSymbol,
                onValueChange = { tickerSymbol = it.uppercase() },
                label = { Text("Ticker (e.g. SBIN.NS, SPY)") },
                modifier = Modifier.weight(1f),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = TextPrimary,
                    unfocusedTextColor = TextPrimary,
                    focusedBorderColor = AccentCyan
                )
            )
            Spacer(modifier = Modifier.width(8.dp))
            Button(
                onClick = {
                    if (tickerSymbol.isBlank()) return@Button
                    isLoading = true
                    scope.launch {
                        try {
                            val resp = api.getStrategy(StrategyRequest(symbol = tickerSymbol.trim()))
                            strategyResponse = resp
                        } catch (e: Exception) {
                            Toast.makeText(context, "Error: " + e.message, Toast.LENGTH_LONG).show()
                        } finally {
                            isLoading = false
                        }
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = AccentCyan),
                modifier = Modifier.height(56.dp)
            ) {
                Text("Analyze", color = DarkBackground, fontWeight = FontWeight.Bold)
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        if (isLoading) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = AccentCyan)
            }
        } else if (strategyResponse != null) {
            val data = strategyResponse!!
            Card(
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(data.symbol, fontSize = 20.sp, fontWeight = FontWeight.Bold, color = TextPrimary)
                        Text(
                            text = data.signal,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (data.signal == "BULLISH") AccentGreen else AccentRed
                        )
                    }

                    Spacer(modifier = Modifier.height(16.dp))
                    Text("Risk-to-Reward Payoff Projection", color = TextSecondary, fontSize = 13.sp)
                    Spacer(modifier = Modifier.height(8.dp))

                    PayoffDiagramCanvas(
                        isBullish = data.signal == "BULLISH"
                    )

                    Spacer(modifier = Modifier.height(16.dp))
                    Text("Technical Summary:", fontWeight = FontWeight.SemiBold, color = TextPrimary)
                    Text(data.technicalSummary, color = TextSecondary, fontSize = 14.sp)

                    if (data.strategySummary.isNotEmpty()) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("Actionable Options Strategy:", fontWeight = FontWeight.SemiBold, color = AccentCyan)
                        Text(data.strategySummary, color = TextSecondary, fontSize = 14.sp)
                    }
                }
            }
        }
    }
}
