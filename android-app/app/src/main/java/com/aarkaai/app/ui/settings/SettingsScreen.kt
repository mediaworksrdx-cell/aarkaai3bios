package com.aarkaai.app.ui.settings

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.aarkaai.app.ui.theme.*

enum class SettingsTab(val label: String, val icon: ImageVector) {
    GENERAL("General", Icons.Outlined.Tune),
    CHAT("Chat", Icons.Outlined.Chat),
    MODELS("Models", Icons.Outlined.Memory),
    WEB("Web & Research", Icons.Outlined.Language),
    SECURITY("Security", Icons.Outlined.Security),
    NOTIFICATIONS("Notifications", Icons.Outlined.Notifications)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    viewModel: SettingsViewModel = viewModel(),
    onNavigateBack: () -> Unit
) {
    val state by viewModel.uiState.collectAsState()
    var activeTab by remember { mutableStateOf(SettingsTab.GENERAL) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = "Settings",
                            fontWeight = FontWeight.Bold,
                            fontSize = 18.sp,
                            color = TextPrimary
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Surface(
                            color = AccentMuted,
                            shape = RoundedCornerShape(6.dp)
                        ) {
                            Text(
                                text = "v2.0",
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = AccentPrimary,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                            )
                        }
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back", tint = TextPrimary)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = BgPrimary
                )
            )
        },
        bottomBar = {
            Surface(
                modifier = Modifier.fillMaxWidth(),
                color = BgSecondary,
                shadowElevation = 8.dp
            ) {
                Box(
                    modifier = Modifier
                        .navigationBarsPadding()
                        .padding(horizontal = 16.dp, vertical = 12.dp)
                ) {
                    Button(
                        onClick = { viewModel.saveSettings() },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = AccentPrimary),
                        enabled = !state.isSaving
                    ) {
                        if (state.isSaving) {
                            com.aarkaai.app.ui.common.AarkaaiLoadingIndicator(
                                color = BgSecondary,
                                size = 20.dp,
                                strokeWidth = 2.dp
                            )
                        } else if (state.savedSuccess) {
                            Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(18.dp))
                            Spacer(modifier = Modifier.width(6.dp))
                            Text("Preferences Saved!", fontWeight = FontWeight.Bold)
                        } else {
                            Text("Save Preferences", fontWeight = FontWeight.SemiBold)
                        }
                    }
                }
            }
        },
        containerColor = BgPrimary
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Horizontal Tab Row
            ScrollableTabRow(
                selectedTabIndex = activeTab.ordinal,
                containerColor = BgPrimary,
                contentColor = AccentPrimary,
                edgePadding = 12.dp,
                divider = { Divider(color = BorderColor) }
            ) {
                SettingsTab.values().forEach { tab ->
                    Tab(
                        selected = activeTab == tab,
                        onClick = { activeTab = tab },
                        text = {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(
                                    imageVector = tab.icon,
                                    contentDescription = null,
                                    modifier = Modifier.size(16.dp),
                                    tint = if (activeTab == tab) AccentPrimary else TextTertiary
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                                Text(
                                    text = tab.label,
                                    fontSize = 13.sp,
                                    fontWeight = if (activeTab == tab) FontWeight.Bold else FontWeight.Normal,
                                    color = if (activeTab == tab) AccentPrimary else TextSecondary
                                )
                            }
                        }
                    )
                }
            }

            // Tab Content
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp, vertical = 16.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                when (activeTab) {
                    SettingsTab.GENERAL -> {
                        item {
                            Text("COLOR THEME", fontWeight = FontWeight.SemiBold, fontSize = 11.sp, color = TextTertiary, letterSpacing = 1.sp)
                            Spacer(modifier = Modifier.height(6.dp))
                            Surface(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .border(1.dp, AccentBorder, RoundedCornerShape(12.dp)),
                                color = AccentMuted,
                                shape = RoundedCornerShape(12.dp)
                            ) {
                                Row(
                                    modifier = Modifier.padding(14.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Icon(Icons.Default.WbSunny, contentDescription = null, tint = AccentPrimary, modifier = Modifier.size(20.dp))
                                    Spacer(modifier = Modifier.width(10.dp))
                                    Column {
                                        Text("Permanent Light Theme (Active)", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = AccentPrimary)
                                        Text("Strictly enforced warm terracotta palette across web & mobile.", fontSize = 11.sp, color = TextSecondary)
                                    }
                                }
                            }
                        }

                        item {
                            Text("PRIMARY LANGUAGE", fontWeight = FontWeight.SemiBold, fontSize = 11.sp, color = TextTertiary, letterSpacing = 1.sp)
                            Spacer(modifier = Modifier.height(6.dp))
                            val languages = listOf(
                                "en" to "English (US / Global)",
                                "hi" to "Hindi (हिंदी)",
                                "ta" to "Tamil (தமிழ்)",
                                "te" to "Telugu (తెలుగు)",
                                "kn" to "Kannada (ಕನ್ನಡ)",
                                "ml" to "Malayalam (മലയാളം)",
                                "mr" to "Marathi (मराठी)",
                                "bn" to "Bengali (বাংলা)",
                                "gu" to "Gujarati (ગુજરાતી)",
                                "pa" to "Punjabi (ਪੰਜਾਬੀ)"
                            )
                            var expanded by remember { mutableStateOf(false) }
                            Box {
                                Surface(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .border(1.dp, BorderColor, RoundedCornerShape(12.dp))
                                        .clickable { expanded = true },
                                    color = BgSecondary,
                                    shape = RoundedCornerShape(12.dp)
                                ) {
                                    Row(
                                        modifier = Modifier.padding(14.dp),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Text(
                                            text = languages.find { it.first == state.language }?.second ?: "English",
                                            fontSize = 13.sp,
                                            fontWeight = FontWeight.Medium,
                                            color = TextPrimary
                                        )
                                        Icon(Icons.Default.ArrowDropDown, contentDescription = null, tint = TextSecondary)
                                    }
                                }
                                DropdownMenu(
                                    expanded = expanded,
                                    onDismissRequest = { expanded = false },
                                    modifier = Modifier.background(BgSecondary)
                                ) {
                                    languages.forEach { (code, label) ->
                                        DropdownMenuItem(
                                            text = { Text(label, fontSize = 13.sp, color = TextPrimary) },
                                            onClick = {
                                                viewModel.setLanguage(code)
                                                expanded = false
                                            }
                                        )
                                    }
                                }
                            }
                        }

                        item {
                            Text("MESSAGE DENSITY", fontWeight = FontWeight.SemiBold, fontSize = 11.sp, color = TextTertiary, letterSpacing = 1.sp)
                            Spacer(modifier = Modifier.height(6.dp))
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                listOf("comfortable" to "Comfortable", "compact" to "Compact").forEach { (key, label) ->
                                    val isSelected = state.density == key
                                    Surface(
                                        modifier = Modifier
                                            .weight(1f)
                                            .border(1.dp, if (isSelected) AccentPrimary else BorderColor, RoundedCornerShape(12.dp))
                                            .clickable { viewModel.setDensity(key) },
                                        color = if (isSelected) AccentMuted else BgSecondary,
                                        shape = RoundedCornerShape(12.dp)
                                    ) {
                                        Box(modifier = Modifier.padding(vertical = 12.dp), contentAlignment = Alignment.Center) {
                                            Text(
                                                text = label,
                                                fontSize = 13.sp,
                                                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                                                color = if (isSelected) AccentPrimary else TextPrimary
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }

                    SettingsTab.CHAT -> {
                        item {
                            SettingToggleCard(
                                title = "Enter to Send",
                                subtitle = "Press Enter on keyboard to immediately send prompt.",
                                checked = state.enterToSend,
                                onCheckedChange = { viewModel.setEnterToSend(it) }
                            )
                        }
                        item {
                            SettingToggleCard(
                                title = "Message Timestamps",
                                subtitle = "Display exact send and receipt times on messages.",
                                checked = state.showTimestamps,
                                onCheckedChange = { viewModel.setShowTimestamps(it) }
                            )
                        }
                        item {
                            SettingToggleCard(
                                title = "Streaming Token Responses",
                                subtitle = "Stream tokens in real-time as they are generated by the neural mesh.",
                                checked = state.streamingResponses,
                                onCheckedChange = { viewModel.setStreamingResponses(it) }
                            )
                        }
                        item {
                            SettingToggleCard(
                                title = "Incognito Chat Mode",
                                subtitle = "Incognito sessions are never saved to history or indexed into memory.",
                                checked = state.incognitoChat,
                                onCheckedChange = { viewModel.setIncognitoChat(it) },
                                highlightColor = PurpleAccent
                            )
                        }
                    }

                    SettingsTab.MODELS -> {
                        item {
                            Text("DEFAULT MODEL", fontWeight = FontWeight.SemiBold, fontSize = 11.sp, color = TextTertiary, letterSpacing = 1.sp)
                            Spacer(modifier = Modifier.height(6.dp))
                            listOf(
                                Triple("aarka-2.0", "Aarka AI 2.0", "Flagship reasoning engine with mathematical and quantitative rigor."),
                                Triple("gemini-3.7", "Google Gemini 3.7", "Multimodal partner model with extended context capabilities."),
                                Triple("claude-sonnet-5", "Claude Sonnet 5", "Anthropic state-of-the-art hybrid reasoning and deep coding model.")
                            ).forEach { (id, name, desc) ->
                                val isSelected = state.defaultModel == id
                                Surface(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 4.dp)
                                        .border(1.5.dp, if (isSelected) AccentPrimary else BorderColor, RoundedCornerShape(12.dp))
                                        .clickable { viewModel.setDefaultModel(id) },
                                    color = if (isSelected) AccentMuted else BgSecondary,
                                    shape = RoundedCornerShape(12.dp)
                                ) {
                                    Column(modifier = Modifier.padding(14.dp)) {
                                        Text(text = name, fontWeight = FontWeight.Bold, fontSize = 14.sp, color = TextPrimary)
                                        Spacer(modifier = Modifier.height(2.dp))
                                        Text(text = desc, fontSize = 11.sp, color = TextSecondary)
                                    }
                                }
                            }
                        }

                        item {
                            Spacer(modifier = Modifier.height(8.dp))
                            Text("DEFAULT REASONING EFFORT", fontWeight = FontWeight.SemiBold, fontSize = 11.sp, color = TextTertiary, letterSpacing = 1.sp)
                            Spacer(modifier = Modifier.height(6.dp))
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                listOf("low" to "Low", "medium" to "Medium", "high" to "High").forEach { (effort, label) ->
                                    val isSelected = state.defaultEffort == effort
                                    Surface(
                                        modifier = Modifier
                                            .weight(1f)
                                            .border(1.dp, if (isSelected) AccentPrimary else BorderColor, RoundedCornerShape(12.dp))
                                            .clickable { viewModel.setDefaultEffort(effort) },
                                        color = if (isSelected) AccentMuted else BgSecondary,
                                        shape = RoundedCornerShape(12.dp)
                                    ) {
                                        Box(modifier = Modifier.padding(vertical = 10.dp), contentAlignment = Alignment.Center) {
                                            Text(
                                                text = label,
                                                fontSize = 13.sp,
                                                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium,
                                                color = if (isSelected) AccentPrimary else TextPrimary
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }

                    SettingsTab.WEB -> {
                        item {
                            SettingToggleCard(
                                title = "Live Web Search",
                                subtitle = "Perform real-time queries for up-to-date web facts.",
                                checked = state.webSearchEnabled,
                                onCheckedChange = { viewModel.setWebSearch(it) }
                            )
                        }
                        item {
                            SettingToggleCard(
                                title = "Deep Research Mode",
                                subtitle = "Multi-step web crawling and factual cross-referencing.",
                                checked = state.deepResearchEnabled,
                                onCheckedChange = { viewModel.setDeepResearch(it) }
                            )
                        }
                        item {
                            SettingToggleCard(
                                title = "Real-Time Market Data Feeds",
                                subtitle = "Integrate live stock tickers, FX rates, and macro indicators.",
                                checked = state.marketDataEnabled,
                                onCheckedChange = { viewModel.setMarketData(it) }
                            )
                        }
                    }

                    SettingsTab.SECURITY -> {
                        item {
                            Surface(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .border(1.dp, BorderColor, RoundedCornerShape(12.dp)),
                                color = BgSecondary,
                                shape = RoundedCornerShape(12.dp)
                            ) {
                                Row(
                                    modifier = Modifier.padding(14.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Column(modifier = Modifier.weight(1f)) {
                                        Text("Two-Factor Authentication (2FA)", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = TextPrimary)
                                        Text("Protect your account with TOTP authenticator app verification.", fontSize = 11.sp, color = TextSecondary)
                                    }
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Surface(color = WarningAmber.copy(alpha = 0.15f), shape = RoundedCornerShape(6.dp)) {
                                        Text("Coming Soon", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = WarningAmber, modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp))
                                    }
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Switch(
                                        checked = state.twoFactorEnabled,
                                        onCheckedChange = { viewModel.setTwoFactor(it) },
                                        colors = SwitchDefaults.colors(checkedThumbColor = BgSecondary, checkedTrackColor = AccentPrimary)
                                    )
                                }
                            }
                        }

                        item {
                            Surface(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .border(1.dp, BorderColor, RoundedCornerShape(12.dp)),
                                color = BgSecondary,
                                shape = RoundedCornerShape(12.dp)
                            ) {
                                Column(modifier = Modifier.padding(14.dp)) {
                                    Text("Active Sessions", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = TextPrimary)
                                    Spacer(modifier = Modifier.height(6.dp))
                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Column {
                                            Text("Current Mobile Session", fontSize = 12.sp, fontWeight = FontWeight.Medium, color = TextPrimary)
                                            Text("Last active: Now", fontSize = 10.sp, color = TextTertiary)
                                        }
                                        Surface(color = SuccessGreen.copy(alpha = 0.15f), shape = RoundedCornerShape(6.dp)) {
                                            Text("Active", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = SuccessGreen, modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp))
                                        }
                                    }
                                    Spacer(modifier = Modifier.height(12.dp))
                                    Text("Sign Out All Other Devices (Coming Soon)", fontSize = 12.sp, color = TextTertiary)
                                }
                            }
                        }
                    }

                    SettingsTab.NOTIFICATIONS -> {
                        item {
                            SettingToggleCard(
                                title = "Email Notifications",
                                subtitle = "Receive weekly research summaries and account updates.",
                                checked = state.emailAlerts,
                                onCheckedChange = { viewModel.setEmailAlerts(it) }
                            )
                        }
                        item {
                            SettingToggleCard(
                                title = "Security Alerts",
                                subtitle = "Instant alerts for new logins and token rotations.",
                                checked = state.securityAlerts,
                                onCheckedChange = { viewModel.setSecurityAlerts(it) }
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun SettingToggleCard(
    title: String,
    subtitle: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    highlightColor: androidx.compose.ui.graphics.Color? = null
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .border(
                1.dp,
                if (highlightColor != null && checked) highlightColor.copy(alpha = 0.4f) else BorderColor,
                RoundedCornerShape(12.dp)
            ),
        color = if (highlightColor != null && checked) highlightColor.copy(alpha = 0.08f) else BgSecondary,
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    color = if (highlightColor != null && checked) highlightColor else TextPrimary
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = subtitle,
                    fontSize = 11.sp,
                    color = TextSecondary,
                    lineHeight = 15.sp
                )
            }
            Spacer(modifier = Modifier.width(12.dp))
            Switch(
                checked = checked,
                onCheckedChange = onCheckedChange,
                colors = SwitchDefaults.colors(
                    checkedThumbColor = BgSecondary,
                    checkedTrackColor = highlightColor ?: AccentPrimary
                )
            )
        }
    }
}
