package com.aarkaai.app.ui.chat

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.TextView
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.ui.res.painterResource
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.Logout
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.viewmodel.compose.viewModel
import io.noties.markwon.Markwon
import io.noties.markwon.ext.latex.JLatexMathPlugin
import io.noties.markwon.ext.strikethrough.StrikethroughPlugin
import io.noties.markwon.ext.tables.TablePlugin
import io.noties.markwon.inlineparser.MarkwonInlineParserPlugin
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import com.aarkaai.app.ui.theme.*
import java.text.SimpleDateFormat
import java.util.*

@Composable
fun ChatScreen(
    viewModel: ChatViewModel = viewModel(),
    onNavigateToSettings: () -> Unit = {},
    onNavigateToSkills: () -> Unit = {},
    onNavigateToAuth: () -> Unit = {},
    onLogout: () -> Unit = {}
) {
    val state by viewModel.uiState.collectAsState()
    val drawerState = rememberDrawerState(DrawerValue.Closed)
    val scope = rememberCoroutineScope()
    val context = androidx.compose.ui.platform.LocalContext.current

    var showModelSwitcher by remember { mutableStateOf(false) }
    var showExportDialog by remember { mutableStateOf(false) }

    ModalNavigationDrawer(
        drawerState = drawerState,
        drawerContent = {
            ModalDrawerSheet(
                modifier = Modifier.width(270.dp),
                drawerContainerColor = BgSecondary
            ) {
                AarkaSidebarContent(
                    conversations = state.filteredConversations,
                    activeId = state.activeConversationId,
                    searchQuery = state.searchQuery,
                    userName = state.userName,
                    userEmail = state.userEmail,
                    isGuest = state.isGuest,
                    onSearchChange = { viewModel.setSearchQuery(it) },
                    onSelect = {
                        viewModel.selectConversation(it)
                        scope.launch { drawerState.close() }
                    },
                    onNewChat = {
                        viewModel.newConversation()
                        scope.launch { drawerState.close() }
                    },
                    onRename = { id, title -> viewModel.renameConversation(id, title) },
                    onDelete = { id -> viewModel.deleteConversation(id) },
                    onCloseDrawer = { scope.launch { drawerState.close() } },
                    onSettingsClick = {
                        scope.launch { drawerState.close() }
                        onNavigateToSettings()
                    },
                    onSkillsClick = {
                        scope.launch { drawerState.close() }
                        onNavigateToSkills()
                    },
                    onNavigateToAuth = {
                        scope.launch { drawerState.close() }
                        onNavigateToAuth()
                    },
                    onLogout = onLogout
                )
            }
        }
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(BgPrimary)
        ) {
            // Compact Top Bar
            AarkaTopBar(
                onMenuClick = { scope.launch { drawerState.open() } },
                onSkillsClick = onNavigateToSkills,
                onExportClick = {
                    if (state.messages.isEmpty()) {
                        Toast.makeText(context, "No messages to export", Toast.LENGTH_SHORT).show()
                    } else {
                        showExportDialog = true
                    }
                },
                onNewChat = { viewModel.newConversation() }
            )

            Divider(color = BorderColor, thickness = 0.5.dp)

            // Main Content Area
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
            ) {
                if (state.messages.isEmpty()) {
                    AarkaWelcomeScreen(userName = state.userName, isGuest = state.isGuest)
                } else {
                    MessageList(
                        messages = state.messages,
                        showTimestamps = state.showTimestamps,
                        density = state.density,
                        onRlhf = { messageId, rating -> viewModel.submitRlhf(messageId, rating) },
                        onRegenerate = { assistantId -> viewModel.regenerateResponse(assistantId) }
                    )
                }
            }

            // Compact Floating Composer Card
            AarkaFloatingChatInput(
                isTyping = state.isTyping,
                selectedModel = state.selectedModel,
                reasoningEffort = state.reasoningEffort,
                onModelSwitcherClick = { showModelSwitcher = true },
                onSend = { viewModel.sendMessage(it) },
                onStop = { viewModel.stopGeneration() }
            )
        }
    }

    if (showModelSwitcher) {
        ModelSwitcherBottomSheet(
            currentModel = state.selectedModel,
            currentEffort = state.reasoningEffort,
            onModelSelect = { modelId ->
                viewModel.selectModel(modelId)
                showModelSwitcher = false
            },
            onEffortSelect = { effort ->
                viewModel.selectEffort(effort)
            },
            onDismiss = { showModelSwitcher = false }
        )
    }

    if (showExportDialog) {
        ExportDialog(
            conversationTitle = state.activeConversation?.title ?: "Conversation",
            messages = state.messages,
            onDismiss = { showExportDialog = false }
        )
    }
}

// ====================================================================
//  COMPACT TOP BAR  –  Refined, Sleek, Proportional
// ====================================================================

@Composable
fun AarkaTopBar(
    onMenuClick: () -> Unit,
    onSkillsClick: () -> Unit,
    onExportClick: () -> Unit,
    onNewChat: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .statusBarsPadding()
            .padding(horizontal = 8.dp, vertical = 3.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Left: Hamburger + Brand Logo
        Row(
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(
                onClick = onMenuClick,
                modifier = Modifier.size(28.dp)
            ) {
                Icon(
                    imageVector = Icons.Outlined.Menu,
                    contentDescription = "Menu",
                    tint = TextPrimary,
                    modifier = Modifier.size(16.dp)
                )
            }

            Spacer(modifier = Modifier.width(4.dp))

            // Brand Logo & Typography
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                modifier = Modifier.clickable(
                    interactionSource = remember { MutableInteractionSource() },
                    indication = null,
                    onClick = onMenuClick
                )
            ) {
                Image(
                    painter = painterResource(id = com.aarkaai.app.R.drawable.ic_splash_logo),
                    contentDescription = null,
                    modifier = Modifier
                        .size(20.dp)
                        .clip(CircleShape)
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "Aarka ",
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp,
                        color = TextPrimary,
                        letterSpacing = (-0.3).sp
                    )
                    Text(
                        text = "AI",
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp,
                        color = AccentPrimary,
                        letterSpacing = (-0.3).sp
                    )
                }
            }
        }

        // Right Action Toolbar: Skills + Export + Compact "+ New Chat" Pill
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(2.dp)
        ) {
            IconButton(
                onClick = onSkillsClick,
                modifier = Modifier.size(28.dp)
            ) {
                Icon(
                    imageVector = Icons.Outlined.AutoAwesome,
                    contentDescription = "Autonomous Skills",
                    tint = TextSecondary,
                    modifier = Modifier.size(15.dp)
                )
            }

            IconButton(
                onClick = onExportClick,
                modifier = Modifier.size(28.dp)
            ) {
                Icon(
                    imageVector = Icons.Outlined.IosShare,
                    contentDescription = "Export Chat",
                    tint = TextSecondary,
                    modifier = Modifier.size(15.dp)
                )
            }

            // Compact single-line "+ New Chat" Pill Button
            Surface(
                modifier = Modifier
                    .height(26.dp)
                    .clip(RoundedCornerShape(13.dp))
                    .border(1.dp, BorderColor, RoundedCornerShape(13.dp))
                    .clickable(onClick = onNewChat),
                color = BgSecondary,
                shape = RoundedCornerShape(13.dp),
                shadowElevation = 0.5.dp
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Default.Add,
                        contentDescription = null,
                        tint = TextPrimary,
                        modifier = Modifier.size(10.dp)
                    )
                    Spacer(modifier = Modifier.width(3.dp))
                    Text(
                        text = "New Chat",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium,
                        color = TextPrimary,
                        maxLines = 1
                    )
                }
            }
        }
    }
}

// ====================================================================
//  COMPACT WELCOME SCREEN  –  Proportional & Minimalist
// ====================================================================

@Composable
fun AarkaWelcomeScreen(
    userName: String = "Web Visitor",
    isGuest: Boolean = true
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 20.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // Aarka AI Signature Sun & Waves Badge
        Image(
            painter = painterResource(id = com.aarkaai.app.R.drawable.ic_splash_logo),
            contentDescription = "Aarka AI",
            modifier = Modifier
                .size(64.dp)
                .clip(CircleShape)
        )

        Spacer(modifier = Modifier.height(14.dp))

        val isLoggedInUser = !isGuest && userName.isNotBlank() && userName != "Web Visitor" && userName != "Guest User"

        // Headline: "Welcome back, [Name]" when logged in, or "Welcome to Aarka AI" when guest
        if (isLoggedInUser) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.Center
            ) {
                Text(
                    text = "Welcome, ",
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp,
                    color = TextPrimary,
                    letterSpacing = (-0.4).sp
                )
                Text(
                    text = userName,
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp,
                    color = AccentPrimary,
                    letterSpacing = (-0.4).sp,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
        } else {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.Center
            ) {
                Text(
                    text = "Welcome to ",
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp,
                    color = TextPrimary,
                    letterSpacing = (-0.4).sp
                )
                Text(
                    text = "Aarka AI",
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp,
                    color = AccentPrimary,
                    letterSpacing = (-0.4).sp
                )
            }
        }

        Spacer(modifier = Modifier.height(6.dp))

        // Clean Subtitle (11.5sp, refined line spacing)
        Text(
            text = "How can Aarka assist your research, financial engineering,\nor architecture today?",
            fontSize = 11.5.sp,
            color = TextSecondary,
            textAlign = TextAlign.Center,
            lineHeight = 16.sp,
            modifier = Modifier.padding(horizontal = 8.dp)
        )

        Spacer(modifier = Modifier.height(36.dp))
    }
}

// ====================================================================
//  COMPACT FLOATING COMPOSER CARD WITH @ SKILL MENTION AUTOCOMPLETE
// ====================================================================

data class AttachedFile(
    val id: String = UUID.randomUUID().toString(),
    val uri: Uri,
    val name: String,
    val size: Long,
    val mimeType: String,
    val isImage: Boolean,
    val textContent: String? = null
)

fun formatChatFileSize(bytes: Long): String {
    if (bytes < 1024) return "$bytes B"
    if (bytes < 1024 * 1024) return String.format(Locale.US, "%.1f KB", bytes / 1024f)
    return String.format(Locale.US, "%.1f MB", bytes / (1024f * 1024f))
}

fun parseChatFileMetadata(context: Context, uri: Uri): AttachedFile {
    var displayName = "file"
    var fileSize = 0L
    try {
        context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
            val nameIndex = cursor.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
            val sizeIndex = cursor.getColumnIndex(android.provider.OpenableColumns.SIZE)
            if (cursor.moveToFirst()) {
                if (nameIndex != -1) displayName = cursor.getString(nameIndex) ?: "file"
                if (sizeIndex != -1) fileSize = cursor.getLong(sizeIndex)
            }
        }
    } catch (e: Exception) {
        displayName = uri.lastPathSegment ?: "file"
    }

    val mimeType = context.contentResolver.getType(uri) ?: "application/octet-stream"
    val isImage = mimeType.startsWith("image/") || displayName.endsWith(".png", true) || displayName.endsWith(".jpg", true) || displayName.endsWith(".jpeg", true) || displayName.endsWith(".webp", true)

    var textContent: String? = null
    val isText = mimeType.startsWith("text/") || displayName.endsWith(".txt", true) || displayName.endsWith(".py", true) || displayName.endsWith(".json", true) || displayName.endsWith(".csv", true) || displayName.endsWith(".md", true) || displayName.endsWith(".kt", true) || displayName.endsWith(".js", true) || displayName.endsWith(".ts", true)
    if (isText && fileSize in 1..300_000L) {
        try {
            context.contentResolver.openInputStream(uri)?.use { stream ->
                textContent = stream.bufferedReader().readText()
            }
        } catch (e: Exception) {
            // ignore
        }
    }

    return AttachedFile(
        uri = uri,
        name = displayName,
        size = fileSize,
        mimeType = mimeType,
        isImage = isImage,
        textContent = textContent
    )
}

@Composable
fun AarkaFloatingChatInput(
    isTyping: Boolean,
    selectedModel: String,
    reasoningEffort: String,
    onModelSwitcherClick: () -> Unit,
    onSend: (String) -> Unit,
    onStop: () -> Unit
) {
    val context = LocalContext.current
    var text by remember { mutableStateOf("") }
    var isFocused by remember { mutableStateOf(false) }
    val focusRequester = remember { FocusRequester() }
    var attachedFiles by remember { mutableStateOf<List<AttachedFile>>(emptyList()) }

    // Activity launcher for photo/file picker
    val filePickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetMultipleContents()
    ) { uris: List<Uri> ->
        if (uris.isNotEmpty()) {
            val newFiles = uris.map { uri -> parseChatFileMetadata(context, uri) }
            attachedFiles = attachedFiles + newFiles
        }
    }

    // Activity launcher for Google Speech-to-Text Recognition
    val speechRecognizerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == android.app.Activity.RESULT_OK) {
            val spokenText = result.data
                ?.getStringArrayListExtra(android.speech.RecognizerIntent.EXTRA_RESULTS)
                ?.firstOrNull()
            if (!spokenText.isNullOrBlank()) {
                text = if (text.isBlank()) spokenText else "$text $spokenText"
            }
        }
    }

    // Flatten all 19 skills for @ and / mention auto-completion
    val allSkills = remember {
        com.aarkaai.app.ui.skills.ALL_SKILL_CATEGORIES.flatMap { cat ->
            cat.skills.map { skill -> skill to cat.title }
        }
    }

    val mentionInfo = remember(text) {
        val lastToken = text.split(" ", "\n").lastOrNull() ?: ""
        if (lastToken.startsWith("@") || lastToken.startsWith("/")) {
            val trigger = lastToken.take(1)
            val query = lastToken.drop(1).lowercase()
            trigger to query
        } else null
    }

    val matchingSkills = remember(mentionInfo) {
        if (mentionInfo == null) emptyList()
        else {
            val q = mentionInfo.second
            allSkills.filter { (skill, catTitle) ->
                skill.name.lowercase().contains(q) ||
                skill.description.lowercase().contains(q) ||
                catTitle.lowercase().contains(q)
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .imePadding()
            .navigationBarsPadding()
            .padding(horizontal = 10.dp, vertical = 4.dp)
    ) {
        // Floating Autonomous Skills Mention Popup
        AnimatedVisibility(
            visible = mentionInfo != null && matchingSkills.isNotEmpty(),
            enter = fadeIn() + expandVertically(expandFrom = Alignment.Bottom),
            exit = fadeOut() + shrinkVertically(shrinkTowards = Alignment.Bottom)
        ) {
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 210.dp)
                    .padding(bottom = 6.dp)
                    .shadow(elevation = 8.dp, shape = RoundedCornerShape(14.dp)),
                color = BgSecondary,
                shape = RoundedCornerShape(14.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, AccentBorder)
            ) {
                Column(modifier = Modifier.padding(vertical = 6.dp)) {
                    // Header
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 12.dp, vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Default.AutoAwesome,
                                contentDescription = null,
                                tint = AccentPrimary,
                                modifier = Modifier.size(13.dp)
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = "Autonomous Skills",
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                color = TextPrimary
                            )
                        }
                        Text(
                            text = "${matchingSkills.size} available",
                            fontSize = 10.sp,
                            color = TextTertiary
                        )
                    }

                    Divider(color = BorderColor.copy(alpha = 0.5f), thickness = 0.5.dp)

                    LazyColumn(
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        items(matchingSkills, key = { it.first.name }) { (skill, catTitle) ->
                            val trigger = mentionInfo?.first ?: "@"
                            Surface(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clickable {
                                        val parts = text.split(" ", "\n").toMutableList()
                                        if (parts.isNotEmpty()) {
                                            parts[parts.size - 1] = "$trigger${skill.name} "
                                        } else {
                                            parts.add("$trigger${skill.name} ")
                                        }
                                        text = parts.joinToString(" ")
                                    },
                                color = Color.Transparent
                            ) {
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(horizontal = 12.dp, vertical = 7.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Column(modifier = Modifier.weight(1f)) {
                                        Row(verticalAlignment = Alignment.CenterVertically) {
                                            Text(
                                                text = "$trigger${skill.name}",
                                                fontSize = 12.sp,
                                                fontWeight = FontWeight.Bold,
                                                fontFamily = FontFamily.Monospace,
                                                color = AccentPrimary
                                            )
                                            Spacer(modifier = Modifier.width(6.dp))
                                            Surface(
                                                color = AccentMuted,
                                                shape = RoundedCornerShape(4.dp)
                                            ) {
                                                Text(
                                                    text = catTitle,
                                                    fontSize = 8.5.sp,
                                                    fontWeight = FontWeight.SemiBold,
                                                    color = TextSecondary,
                                                    modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp)
                                                )
                                            }
                                        }
                                        Text(
                                            text = skill.description,
                                            fontSize = 10.5.sp,
                                            color = TextTertiary,
                                            maxLines = 1,
                                            overflow = TextOverflow.Ellipsis,
                                            modifier = Modifier.padding(top = 1.dp)
                                        )
                                    }
                                    Icon(
                                        imageVector = Icons.Default.ArrowForward,
                                        contentDescription = null,
                                        tint = TextTertiary,
                                        modifier = Modifier.size(12.dp)
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }

        // Floating Card Container (compact padding, 16dp radius)
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .shadow(
                    elevation = if (isFocused) 6.dp else 3.dp,
                    shape = RoundedCornerShape(16.dp),
                    ambientColor = Color(0x12000000),
                    spotColor = Color(0x18000000)
                ),
            color = BgSecondary,
            shape = RoundedCornerShape(16.dp),
            border = androidx.compose.foundation.BorderStroke(
                width = 1.dp,
                color = if (isFocused) AccentBorder else BorderColor
            )
        ) {
            Column(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 7.dp)
            ) {
                // Top Meta Toolbar: Model Switcher Pill on Left, Character Counter / Skills Mention Pill on Right
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 5.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // Model Switcher Pill: ⚡ Aarka AI [LOW] ▾
                    Surface(
                        modifier = Modifier
                            .height(24.dp)
                            .clip(RoundedCornerShape(6.dp))
                            .border(1.dp, BorderColor, RoundedCornerShape(6.dp))
                            .clickable(onClick = onModelSwitcherClick),
                        color = BgPrimary,
                        shape = RoundedCornerShape(6.dp)
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 6.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = when {
                                    selectedModel == "gemini-3.7" -> "✨ Gemini 3.7"
                                    selectedModel.contains("claude") || selectedModel.contains("sonnet") -> "🟣 Claude Sonnet 5"
                                    else -> "⚡ Aarka AI"
                                },
                                fontSize = 10.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = TextPrimary
                            )
                            Spacer(modifier = Modifier.width(3.dp))
                            Surface(
                                color = AccentMuted,
                                shape = RoundedCornerShape(3.dp)
                            ) {
                                Text(
                                    text = reasoningEffort.uppercase(),
                                    fontSize = 7.5.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = AccentPrimary,
                                    modifier = Modifier.padding(horizontal = 3.dp, vertical = 0.5.dp)
                                )
                            }
                            Spacer(modifier = Modifier.width(1.dp))
                            Icon(
                                imageVector = Icons.Default.ArrowDropDown,
                                contentDescription = null,
                                tint = TextTertiary,
                                modifier = Modifier.size(12.dp)
                            )
                        }
                    }

                    // Right: Character count or @ skills shortcut tag
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        if (text.isNotEmpty()) {
                            Text(
                                text = "${text.length} chars",
                                fontSize = 9.sp,
                                fontFamily = FontFamily.Monospace,
                                color = TextTertiary
                            )
                        } else {
                            Surface(
                                color = BgPrimary,
                                shape = RoundedCornerShape(4.dp),
                                border = androidx.compose.foundation.BorderStroke(0.5.dp, BorderColor)
                            ) {
                                Text(
                                    text = "@ skills",
                                    fontSize = 8.5.sp,
                                    fontWeight = FontWeight.Medium,
                                    color = TextTertiary,
                                    modifier = Modifier.padding(horizontal = 5.dp, vertical = 1.dp)
                                )
                            }
                        }
                    }
                }

                // Hairline divider
                Divider(color = BorderColor.copy(alpha = 0.35f), thickness = 0.5.dp)

                // Attached Files Preview Strip
                if (attachedFiles.isNotEmpty()) {
                    LazyRow(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp),
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        items(attachedFiles, key = { it.id }) { file ->
                            Surface(
                                color = BgPrimary,
                                shape = RoundedCornerShape(8.dp),
                                border = androidx.compose.foundation.BorderStroke(0.8.dp, BorderColor)
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 7.dp, vertical = 3.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Icon(
                                        imageVector = if (file.isImage) Icons.Outlined.Image else Icons.Outlined.Description,
                                        contentDescription = null,
                                        tint = AccentPrimary,
                                        modifier = Modifier.size(13.dp)
                                    )
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Text(
                                        text = file.name,
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Medium,
                                        color = TextPrimary,
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis,
                                        modifier = Modifier.widthIn(max = 110.dp)
                                    )
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Text(
                                        text = formatChatFileSize(file.size),
                                        fontSize = 9.sp,
                                        fontFamily = FontFamily.Monospace,
                                        color = TextTertiary
                                    )
                                    Spacer(modifier = Modifier.width(2.dp))
                                    Icon(
                                        imageVector = Icons.Default.Close,
                                        contentDescription = "Remove file",
                                        tint = TextTertiary,
                                        modifier = Modifier
                                            .size(14.dp)
                                            .clip(CircleShape)
                                            .clickable {
                                                attachedFiles = attachedFiles.filter { it.id != file.id }
                                            }
                                            .padding(1.dp)
                                    )
                                }
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(3.dp))

                // Unified Typing Space Row: [+] [Mic] [Text Area] [Send]
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(start = 2.dp, end = 2.dp, top = 2.dp, bottom = 2.dp),
                    verticalAlignment = Alignment.Bottom
                ) {
                    // Attach '+' Button for Photos and Files
                    Surface(
                        onClick = { filePickerLauncher.launch("*/*") },
                        modifier = Modifier
                            .size(36.dp)
                            .shadow(elevation = 1.dp, shape = CircleShape),
                        shape = CircleShape,
                        color = BgPrimary,
                        border = androidx.compose.foundation.BorderStroke(0.8.dp, BorderColor)
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Icon(
                                imageVector = Icons.Default.Add,
                                contentDescription = "Attach photos or files",
                                tint = TextSecondary,
                                modifier = Modifier.size(18.dp)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.width(4.dp))

                    // Microphone Voice-to-Text Button
                    Surface(
                        onClick = {
                            val intent = Intent(android.speech.RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                                putExtra(
                                    android.speech.RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                                    android.speech.RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
                                )
                                putExtra(android.speech.RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault())
                                putExtra(android.speech.RecognizerIntent.EXTRA_PROMPT, "Speak to Aarka AI...")
                            }
                            try {
                                speechRecognizerLauncher.launch(intent)
                            } catch (e: Exception) {
                                Toast.makeText(context, "Speech recognition not available on this device", Toast.LENGTH_SHORT).show()
                            }
                        },
                        modifier = Modifier
                            .size(36.dp)
                            .shadow(elevation = 1.dp, shape = CircleShape),
                        shape = CircleShape,
                        color = BgPrimary,
                        border = androidx.compose.foundation.BorderStroke(0.8.dp, BorderColor)
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Icon(
                                imageVector = Icons.Outlined.Mic,
                                contentDescription = "Voice input",
                                tint = AccentPrimary,
                                modifier = Modifier.size(18.dp)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.width(5.dp))

                    // Multiline Input Text Area
                    BasicTextField(
                        value = text,
                        onValueChange = { if (it.length <= 4000) text = it },
                        modifier = Modifier
                            .weight(1f)
                            .heightIn(min = 38.dp, max = 120.dp)
                            .padding(horizontal = 4.dp, vertical = 7.dp)
                            .focusRequester(focusRequester)
                            .onFocusChanged { isFocused = it.isFocused },
                        textStyle = TextStyle(
                            color = TextPrimary,
                            fontSize = 13.5.sp,
                            lineHeight = 18.5.sp
                        ),
                        cursorBrush = SolidColor(AccentPrimary),
                        maxLines = 5,
                        decorationBox = { innerTextField ->
                            Box(contentAlignment = Alignment.CenterStart) {
                                if (text.isEmpty()) {
                                    Text(
                                        text = "Ask Aarka anything... (@ skills)",
                                        color = TextTertiary,
                                        fontSize = 12.5.sp,
                                        lineHeight = 18.sp
                                    )
                                }
                                innerTextField()
                            }
                        }
                    )

                    Spacer(modifier = Modifier.width(6.dp))

                    // Beautiful Elevated Circular Send / Stop Button directly in the typing space right side
                    if (isTyping) {
                        Surface(
                            onClick = onStop,
                            modifier = Modifier
                                .size(38.dp)
                                .shadow(
                                    elevation = 3.dp,
                                    shape = CircleShape,
                                    ambientColor = Color(0x33DC2626),
                                    spotColor = Color(0x4DDC2626)
                                ),
                            shape = CircleShape,
                            color = ErrorRed
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Box(
                                    modifier = Modifier
                                        .size(11.dp)
                                        .background(Color.White, RoundedCornerShape(2.5.dp))
                                )
                            }
                        }
                    } else {
                        val canSend = text.isNotBlank() || attachedFiles.isNotEmpty()
                        val buttonScale by animateFloatAsState(
                            targetValue = if (canSend) 1f else 0.94f,
                            animationSpec = spring(dampingRatio = 0.7f, stiffness = Spring.StiffnessMedium),
                            label = "sendScale"
                        )

                        Surface(
                            onClick = {
                                if (canSend) {
                                    val finalPayload = if (attachedFiles.isNotEmpty()) {
                                        val fileHeaders = attachedFiles.joinToString("\n\n") { file ->
                                            if (file.textContent != null) {
                                                "[Attached File: ${file.name} (${formatChatFileSize(file.size)})]\n```\n${file.textContent}\n```"
                                            } else {
                                                "[Attached ${if (file.isImage) "Photo" else "File"}: ${file.name} (${formatChatFileSize(file.size)})]"
                                            }
                                        }
                                        if (text.isNotBlank()) "$fileHeaders\n\n${text.trim()}" else fileHeaders
                                    } else {
                                        text.trim()
                                    }

                                    onSend(finalPayload)
                                    text = ""
                                    attachedFiles = emptyList()
                                }
                            },
                            enabled = canSend,
                            modifier = Modifier
                                .size(38.dp)
                                .scale(buttonScale)
                                .then(
                                    if (canSend) {
                                        Modifier.shadow(
                                            elevation = 4.dp,
                                            shape = CircleShape,
                                            ambientColor = AccentPrimary.copy(alpha = 0.35f),
                                            spotColor = AccentPrimary.copy(alpha = 0.5f)
                                        )
                                    } else Modifier
                                ),
                            shape = CircleShape,
                            color = if (canSend) Color.Transparent else BgPrimary,
                            border = if (!canSend) androidx.compose.foundation.BorderStroke(1.dp, BorderColor) else null
                        ) {
                            Box(
                                modifier = Modifier
                                    .fillMaxSize()
                                    .clip(CircleShape)
                                    .then(
                                        if (canSend) {
                                            Modifier.background(
                                                brush = Brush.verticalGradient(
                                                    colors = listOf(
                                                        Color(0xFFE56A47),
                                                        Color(0xFFB84F2E)
                                                    )
                                                )
                                            )
                                        } else Modifier
                                    ),
                                contentAlignment = Alignment.Center
                            ) {
                                Icon(
                                    imageVector = Icons.Default.ArrowUpward,
                                    contentDescription = "Send message",
                                    tint = if (canSend) Color.White else AccentPrimary.copy(alpha = 0.40f),
                                    modifier = Modifier
                                        .size(18.dp)
                                        .offset(y = (-0.5).dp)
                                )
                            }
                        }
                    }
                }
            }
        }

        // Legal Accuracy Disclaimer below card
        Text(
            text = "Aarka AI can make mistakes. Verify critical facts and financial models.",
            fontSize = 9.sp,
            color = TextTertiary,
            textAlign = TextAlign.Center,
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 4.dp, bottom = 1.dp)
        )
    }
}

// ====================================================================
//  COMPACT SIDEBAR CONTENT
// ====================================================================

@Composable
fun AarkaSidebarContent(
    conversations: List<Conversation>,
    activeId: String?,
    searchQuery: String,
    userName: String,
    userEmail: String,
    isGuest: Boolean,
    onSearchChange: (String) -> Unit,
    onSelect: (String) -> Unit,
    onNewChat: () -> Unit,
    onRename: (String, String) -> Unit,
    onDelete: (String) -> Unit,
    onCloseDrawer: () -> Unit,
    onSettingsClick: () -> Unit,
    onSkillsClick: () -> Unit,
    onNavigateToAuth: () -> Unit = {},
    onLogout: () -> Unit
) {
    var renamingConvId by remember { mutableStateOf<String?>(null) }
    var renameText by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .statusBarsPadding()
            .navigationBarsPadding()
            .padding(10.dp)
    ) {
        // Sidebar Header: Sparkle Squircle + Aarka AI + Close Icon
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(24.dp)
                        .clip(RoundedCornerShape(7.dp))
                        .background(AccentMuted)
                        .border(1.dp, AccentBorder, RoundedCornerShape(7.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.AutoAwesome,
                        contentDescription = null,
                        tint = AccentPrimary,
                        modifier = Modifier.size(13.dp)
                    )
                }
                Spacer(modifier = Modifier.width(6.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Aarka ", fontWeight = FontWeight.Bold, fontSize = 14.sp, color = TextPrimary)
                    Text("AI", fontWeight = FontWeight.Bold, fontSize = 14.sp, color = AccentPrimary)
                }
            }

            IconButton(onClick = onCloseDrawer, modifier = Modifier.size(24.dp)) {
                Icon(Icons.Default.Close, contentDescription = "Close", tint = TextTertiary, modifier = Modifier.size(14.dp))
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        // Primary Action: "+ New Conversation" in solid Terracotta
        Button(
            onClick = onNewChat,
            modifier = Modifier
                .fillMaxWidth()
                .height(34.dp)
                .shadow(elevation = 1.dp, shape = RoundedCornerShape(9.dp)),
            shape = RoundedCornerShape(9.dp),
            colors = ButtonDefaults.buttonColors(containerColor = AccentPrimary),
            contentPadding = PaddingValues(horizontal = 10.dp)
        ) {
            Icon(Icons.Default.Add, contentDescription = null, tint = Color.White, modifier = Modifier.size(13.dp))
            Spacer(modifier = Modifier.width(4.dp))
            Text("New Conversation", fontWeight = FontWeight.SemiBold, fontSize = 11.5.sp, color = Color.White)
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Search conversations pill
        OutlinedTextField(
            value = searchQuery,
            onValueChange = onSearchChange,
            placeholder = { Text("Search conversations...", fontSize = 11.sp, color = TextTertiary) },
            leadingIcon = { Icon(Icons.Outlined.Search, contentDescription = null, tint = TextTertiary, modifier = Modifier.size(13.dp)) },
            modifier = Modifier
                .fillMaxWidth()
                .height(36.dp),
            shape = RoundedCornerShape(8.dp),
            colors = OutlinedTextFieldDefaults.colors(
                focusedContainerColor = BgPrimary,
                unfocusedContainerColor = BgPrimary,
                focusedBorderColor = AccentBorder,
                unfocusedBorderColor = BorderColor
            ),
            singleLine = true
        )

        Spacer(modifier = Modifier.height(8.dp))

        // Chronologically Grouped List
        val grouped = remember(conversations) { groupConversationsByDate(conversations) }

        LazyColumn(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(3.dp)
        ) {
            grouped.forEach { (groupName, convList) ->
                if (convList.isNotEmpty()) {
                    item {
                        Text(
                            text = groupName.uppercase(),
                            color = TextTertiary,
                            fontSize = 8.5.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 0.8.sp,
                            modifier = Modifier.padding(start = 4.dp, top = 6.dp, bottom = 2.dp)
                        )
                    }

                    items(convList, key = { it.id }) { conv ->
                        val isActive = conv.id == activeId
                        var showMenu by remember { mutableStateOf(false) }

                        Surface(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(8.dp))
                                .clickable { onSelect(conv.id) },
                            color = if (isActive) AccentMuted else Color.Transparent,
                            border = if (isActive) androidx.compose.foundation.BorderStroke(1.dp, AccentBorder) else null,
                            shape = RoundedCornerShape(8.dp)
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Icon(
                                    imageVector = Icons.Outlined.ChatBubbleOutline,
                                    contentDescription = null,
                                    tint = if (isActive) AccentPrimary else TextTertiary,
                                    modifier = Modifier.size(13.dp)
                                )
                                Spacer(modifier = Modifier.width(6.dp))

                                if (renamingConvId == conv.id) {
                                    BasicTextField(
                                        value = renameText,
                                        onValueChange = { renameText = it },
                                        modifier = Modifier.weight(1f),
                                        textStyle = TextStyle(fontSize = 11.5.sp, color = TextPrimary, fontWeight = FontWeight.Bold),
                                        singleLine = true
                                    )
                                    IconButton(
                                        onClick = {
                                            onRename(conv.id, renameText)
                                            renamingConvId = null
                                        },
                                        modifier = Modifier.size(20.dp)
                                    ) {
                                        Icon(Icons.Default.Check, contentDescription = "Confirm", tint = AccentPrimary, modifier = Modifier.size(13.dp))
                                    }
                                } else {
                                    Text(
                                        text = conv.title,
                                        modifier = Modifier.weight(1f),
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis,
                                        fontSize = 11.sp,
                                        fontWeight = if (isActive) FontWeight.SemiBold else FontWeight.Normal,
                                        color = if (isActive) AccentPrimary else TextPrimary
                                    )

                                    Box {
                                        IconButton(
                                            onClick = { showMenu = true },
                                            modifier = Modifier.size(18.dp)
                                        ) {
                                            Icon(Icons.Default.MoreVert, contentDescription = "Options", tint = TextTertiary, modifier = Modifier.size(13.dp))
                                        }
                                        DropdownMenu(
                                            expanded = showMenu,
                                            onDismissRequest = { showMenu = false },
                                            modifier = Modifier.background(BgSecondary)
                                        ) {
                                            DropdownMenuItem(
                                                text = { Text("Rename", fontSize = 11.sp, color = TextPrimary) },
                                                onClick = {
                                                    renameText = conv.title
                                                    renamingConvId = conv.id
                                                    showMenu = false
                                                },
                                                leadingIcon = { Icon(Icons.Outlined.Edit, contentDescription = null, modifier = Modifier.size(13.dp), tint = TextSecondary) }
                                            )
                                            DropdownMenuItem(
                                                text = { Text("Delete", fontSize = 11.sp, color = ErrorRed) },
                                                onClick = {
                                                    onDelete(conv.id)
                                                    showMenu = false
                                                },
                                                leadingIcon = { Icon(Icons.Outlined.Delete, contentDescription = null, modifier = Modifier.size(13.dp), tint = ErrorRed) }
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        Divider(color = BorderColor, modifier = Modifier.padding(vertical = 6.dp))

        // Autonomous Skills Shortcut
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(8.dp))
                .clickable(onClick = onSkillsClick),
            color = BgPrimary,
            border = androidx.compose.foundation.BorderStroke(1.dp, BorderColor),
            shape = RoundedCornerShape(8.dp)
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Outlined.AutoAwesome, contentDescription = null, tint = AccentPrimary, modifier = Modifier.size(13.dp))
                Spacer(modifier = Modifier.width(6.dp))
                Text("Autonomous Skills", fontWeight = FontWeight.SemiBold, fontSize = 11.sp, color = TextPrimary)
                Spacer(modifier = Modifier.weight(1f))
                Surface(color = AccentMuted, shape = RoundedCornerShape(3.dp)) {
                    Text("19", fontSize = 8.sp, fontWeight = FontWeight.Bold, color = AccentPrimary, modifier = Modifier.padding(horizontal = 4.dp, vertical = 0.5.dp))
                }
            }
        }

        Spacer(modifier = Modifier.height(6.dp))

        // Guest Auth Banner (Google / GitHub)
        if (isGuest) {
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(8.dp))
                    .clickable(onClick = {
                        onCloseDrawer()
                        onNavigateToAuth()
                    }),
                color = AccentMuted,
                border = androidx.compose.foundation.BorderStroke(1.dp, AccentBorder),
                shape = RoundedCornerShape(8.dp)
            ) {
                Column(
                    modifier = Modifier.padding(horizontal = 9.dp, vertical = 7.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            painter = painterResource(id = com.aarkaai.app.R.drawable.ic_google_logo),
                            contentDescription = null,
                            modifier = Modifier.size(13.dp),
                            tint = Color.Unspecified
                        )
                        Spacer(modifier = Modifier.width(5.dp))
                        Icon(
                            painter = painterResource(id = com.aarkaai.app.R.drawable.ic_github_logo),
                            contentDescription = null,
                            modifier = Modifier.size(13.dp),
                            tint = TextPrimary
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            "Sign In / Sync Account",
                            fontWeight = FontWeight.Bold,
                            fontSize = 11.sp,
                            color = AccentPrimary
                        )
                    }
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        "Connect Google or GitHub to save chats",
                        fontSize = 8.5.sp,
                        color = TextSecondary
                    )
                }
            }
            Spacer(modifier = Modifier.height(6.dp))
        }

        // User Profile & Settings Footer
        Surface(
            modifier = Modifier.fillMaxWidth(),
            color = BgPrimary,
            shape = RoundedCornerShape(8.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, BorderColor)
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(26.dp)
                        .clip(CircleShape)
                        .background(AccentPrimary),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = (userName.firstOrNull() ?: 'A').uppercase(),
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                        fontSize = 11.sp
                    )
                }

                Spacer(modifier = Modifier.width(6.dp))

                Column(
                    modifier = Modifier
                        .weight(1f)
                        .clickable(enabled = isGuest) {
                            if (isGuest) {
                                onCloseDrawer()
                                onNavigateToAuth()
                            }
                        }
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = userName,
                            fontWeight = FontWeight.Bold,
                            fontSize = 11.sp,
                            color = TextPrimary,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                        if (isGuest) {
                            Spacer(modifier = Modifier.width(3.dp))
                            Surface(color = WarningAmber.copy(alpha = 0.15f), shape = RoundedCornerShape(2.dp)) {
                                Text("GUEST", fontSize = 7.sp, fontWeight = FontWeight.Bold, color = WarningAmber, modifier = Modifier.padding(horizontal = 2.dp, vertical = 0.5.dp))
                            }
                        }
                    }
                    Text(
                        text = userEmail,
                        fontSize = 8.5.sp,
                        color = TextTertiary,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }

                IconButton(onClick = onSettingsClick, modifier = Modifier.size(22.dp)) {
                    Icon(Icons.Outlined.Settings, contentDescription = "Settings", tint = TextSecondary, modifier = Modifier.size(13.dp))
                }

                IconButton(onClick = onLogout, modifier = Modifier.size(22.dp)) {
                    Icon(Icons.AutoMirrored.Outlined.Logout, contentDescription = "Logout", tint = ErrorRed, modifier = Modifier.size(13.dp))
                }
            }
        }
    }
}

private fun groupConversationsByDate(conversations: List<Conversation>): Map<String, List<Conversation>> {
    val now = System.currentTimeMillis()
    val oneDay = 24 * 60 * 60 * 1000L
    val today = mutableListOf<Conversation>()
    val yesterday = mutableListOf<Conversation>()
    val last7Days = mutableListOf<Conversation>()
    val older = mutableListOf<Conversation>()

    for (c in conversations) {
        val diff = now - c.createdAt
        when {
            diff < oneDay -> today.add(c)
            diff < 2 * oneDay -> yesterday.add(c)
            diff < 7 * oneDay -> last7Days.add(c)
            else -> older.add(c)
        }
    }

    val result = linkedMapOf<String, List<Conversation>>()
    if (today.isNotEmpty()) result["Today"] = today
    if (yesterday.isNotEmpty()) result["Yesterday"] = yesterday
    if (last7Days.isNotEmpty()) result["Previous 7 Days"] = last7Days
    if (older.isNotEmpty()) result["Older"] = older
    return result
}

// ====================================================================
//  MESSAGE LIST & COMPACT BUBBLES
// ====================================================================

@Composable
fun MessageList(
    messages: List<ChatMessage>,
    showTimestamps: Boolean,
    density: String,
    onRlhf: (messageId: String, rating: Int) -> Unit,
    onRegenerate: (assistantMessageId: String) -> Unit
) {
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()
    val imeBottom = WindowInsets.ime.getBottom(LocalDensity.current)

    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            scope.launch {
                listState.animateScrollToItem(messages.size - 1)
            }
        }
    }

    LaunchedEffect(imeBottom) {
        if (imeBottom > 0 && messages.isNotEmpty()) {
            scope.launch {
                listState.animateScrollToItem(messages.size - 1)
            }
        }
    }

    LazyColumn(
        state = listState,
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(top = 8.dp, bottom = 8.dp),
        verticalArrangement = Arrangement.spacedBy(if (density == "compact") 4.dp else 8.dp)
    ) {
        items(messages, key = { it.id }) { message ->
            if (message.isUser) {
                UserMessageBubble(message, showTimestamps)
            } else {
                AiMessageRow(message, showTimestamps, onRlhf, onRegenerate)
            }
        }
    }
}

@Composable
fun UserMessageBubble(message: ChatMessage, showTimestamps: Boolean) {
    val timeStr = remember(message.timestamp) {
        SimpleDateFormat("h:mm a", Locale.getDefault()).format(Date(message.timestamp))
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 10.dp),
        horizontalArrangement = Arrangement.End
    ) {
        Column(horizontalAlignment = Alignment.End) {
            Surface(
                modifier = Modifier
                    .widthIn(max = 260.dp)
                    .shadow(elevation = 0.5.dp, shape = RoundedCornerShape(14.dp, 14.dp, 2.dp, 14.dp)),
                color = UserBubbleBg,
                shape = RoundedCornerShape(14.dp, 14.dp, 2.dp, 14.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, BorderColor)
            ) {
                Text(
                    text = message.text,
                    color = TextPrimary,
                    fontSize = 12.5.sp,
                    lineHeight = 17.sp,
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp)
                )
            }
            if (showTimestamps) {
                Text(
                    text = timeStr,
                    fontSize = 8.sp,
                    color = TextTertiary,
                    modifier = Modifier.padding(top = 2.dp, end = 3.dp)
                )
            }
        }
    }
}

@Composable
fun AiMessageRow(
    message: ChatMessage,
    showTimestamps: Boolean,
    onRlhf: (messageId: String, rating: Int) -> Unit,
    onRegenerate: (assistantMessageId: String) -> Unit
) {
    val context = LocalContext.current
    val timeStr = remember(message.timestamp) {
        SimpleDateFormat("h:mm a", Locale.getDefault()).format(Date(message.timestamp))
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 10.dp),
        horizontalArrangement = Arrangement.Start,
        verticalAlignment = Alignment.Top
    ) {
        // Compact Sparkle Squircle Avatar: 22dp x 22dp
        Box(
            modifier = Modifier
                .padding(top = 2.dp)
                .size(22.dp)
                .clip(RoundedCornerShape(6.dp))
                .background(AccentMuted)
                .border(1.dp, AccentBorder, RoundedCornerShape(6.dp)),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = Icons.Default.AutoAwesome,
                contentDescription = "Aarka AI",
                tint = AccentPrimary,
                modifier = Modifier.size(11.dp)
            )
        }

        Spacer(modifier = Modifier.width(8.dp))

        Column(modifier = Modifier.weight(1f)) {
            // Header: Model Label + Time
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = when {
                        message.modelUsed?.contains("Gemini", ignoreCase = true) == true || message.modelUsed == "gemini-3.7" -> "Gemini 3.7"
                        message.modelUsed?.contains("Claude", ignoreCase = true) == true || message.modelUsed?.contains("sonnet", ignoreCase = true) == true -> "Claude Sonnet 5"
                        else -> "Aarka AI"
                    },
                    fontWeight = FontWeight.Bold,
                    fontSize = 11.sp,
                    color = TextPrimary
                )
                if (showTimestamps) {
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = "· $timeStr",
                        fontSize = 8.sp,
                        color = TextTertiary
                    )
                }
            }

            Spacer(modifier = Modifier.height(3.dp))

            if (message.isLoading) {
                TypingIndicator()
            } else {
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .shadow(elevation = 0.5.dp, shape = RoundedCornerShape(2.dp, 12.dp, 12.dp, 12.dp)),
                    color = BgSecondary,
                    shape = RoundedCornerShape(2.dp, 12.dp, 12.dp, 12.dp),
                    border = androidx.compose.foundation.BorderStroke(1.dp, BorderColor)
                ) {
                    Box(modifier = Modifier.padding(9.dp)) {
                        MarkdownText(markdown = message.text, isError = message.isError)
                    }
                }

                if (!message.isError) {
                    AarkaResponseActionBar(
                        message = message,
                        onRlhf = onRlhf,
                        onRegenerate = onRegenerate
                    )
                }
            }
        }
    }
}

@Composable
fun AarkaResponseActionBar(
    message: ChatMessage,
    onRlhf: (messageId: String, rating: Int) -> Unit,
    onRegenerate: (assistantMessageId: String) -> Unit
) {
    val context = LocalContext.current
    var copied by remember { mutableStateOf(false) }

    LaunchedEffect(copied) {
        if (copied) {
            delay(2000)
            copied = false
        }
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(top = 4.dp, bottom = 2.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        // 1. Copy button: [📋 Copy]
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier
                .clip(RoundedCornerShape(6.dp))
                .clickable {
                    val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                    val clip = ClipData.newPlainText("Aarka AI Response", message.text)
                    clipboard.setPrimaryClip(clip)
                    copied = true
                    Toast.makeText(context, "Copied to clipboard", Toast.LENGTH_SHORT).show()
                }
                .padding(horizontal = 4.dp, vertical = 3.dp)
        ) {
            Icon(
                imageVector = Icons.Outlined.ContentCopy,
                contentDescription = "Copy",
                modifier = Modifier.size(13.dp),
                tint = if (copied) AccentPrimary else TextSecondary
            )
            Spacer(modifier = Modifier.width(3.dp))
            Text(
                text = if (copied) "Copied" else "Copy",
                fontSize = 11.sp,
                fontWeight = FontWeight.Normal,
                color = if (copied) AccentPrimary else Color(0xFF4A88C7)
            )
        }

        // 2. Thumbs Up button: [👍]
        val isThumbUp = message.rlhfRating == 1
        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(6.dp))
                .clickable { onRlhf(message.id, if (isThumbUp) 0 else 1) }
                .padding(horizontal = 4.dp, vertical = 3.dp),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = if (isThumbUp) Icons.Filled.ThumbUp else Icons.Outlined.ThumbUp,
                contentDescription = "Good response",
                modifier = Modifier.size(13.dp),
                tint = if (isThumbUp) AccentPrimary else TextSecondary
            )
        }

        // 3. Thumbs Down button: [👎]
        val isThumbDown = message.rlhfRating == -1
        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(6.dp))
                .clickable { onRlhf(message.id, if (isThumbDown) 0 else -1) }
                .padding(horizontal = 4.dp, vertical = 3.dp),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = if (isThumbDown) Icons.Filled.ThumbDown else Icons.Outlined.ThumbDown,
                contentDescription = "Bad response",
                modifier = Modifier.size(13.dp),
                tint = if (isThumbDown) ErrorRed else TextSecondary
            )
        }

        // 4. Retry button: [🔄 Retry]
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier
                .clip(RoundedCornerShape(6.dp))
                .clickable { onRegenerate(message.id) }
                .padding(horizontal = 4.dp, vertical = 3.dp)
        ) {
            Icon(
                imageVector = Icons.Outlined.Refresh,
                contentDescription = "Retry",
                modifier = Modifier.size(13.5.dp),
                tint = TextSecondary
            )
            Spacer(modifier = Modifier.width(3.dp))
            Text(
                text = "Retry",
                fontSize = 11.sp,
                fontWeight = FontWeight.Normal,
                color = Color(0xFF4A88C7)
            )
        }

        // 5. Export button: [📥 Export] -> Direct PDF and Word Doc export (no generic text share)
        var showExportMenu by remember { mutableStateOf(false) }

        Box {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier
                    .clip(RoundedCornerShape(6.dp))
                    .clickable { showExportMenu = true }
                    .padding(horizontal = 4.dp, vertical = 3.dp)
            ) {
                Icon(
                    imageVector = Icons.Outlined.FileDownload,
                    contentDescription = "Export",
                    modifier = Modifier.size(13.5.dp),
                    tint = TextSecondary
                )
                Spacer(modifier = Modifier.width(3.dp))
                Text(
                    text = "Export",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Normal,
                    color = Color(0xFF4A88C7)
                )
            }

            DropdownMenu(
                expanded = showExportMenu,
                onDismissRequest = { showExportMenu = false },
                modifier = Modifier
                    .background(BgSecondary)
                    .border(1.dp, BorderColor, RoundedCornerShape(12.dp))
            ) {
                DropdownMenuItem(
                    text = {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Outlined.PictureAsPdf,
                                contentDescription = null,
                                tint = Color(0xFFD96645),
                                modifier = Modifier.size(16.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "Export as PDF (.pdf)",
                                fontSize = 12.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = TextPrimary
                            )
                        }
                    },
                    onClick = {
                        showExportMenu = false
                        exportAsPdf(context, "Aarka AI Response", listOf(message))
                    }
                )
                Divider(color = BorderColor, thickness = 0.5.dp)
                DropdownMenuItem(
                    text = {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Outlined.Article,
                                contentDescription = null,
                                tint = Color(0xFF2563EB),
                                modifier = Modifier.size(16.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "Export as Word (.doc)",
                                fontSize = 12.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = TextPrimary
                            )
                        }
                    },
                    onClick = {
                        showExportMenu = false
                        exportAsWord(context, "Aarka AI Response", listOf(message))
                    }
                )
            }
        }

        Spacer(modifier = Modifier.weight(1f))

        // Processing time badge if present
        message.processingTime?.let { time ->
            Text(
                text = "⏱ ${String.format("%.1f", time)}s",
                fontSize = 8.sp,
                color = TextTertiary,
                fontFamily = FontFamily.Monospace
            )
        }
    }
}

@Composable
fun MarkdownText(markdown: String, isError: Boolean = false) {
    val context = LocalContext.current
    val textColor = if (isError) ErrorRed else TextPrimary
    val textColorArgb = textColor.toArgb()

    val markwon = remember(context) {
        val density = context.resources.displayMetrics.density
        val fontScale = context.resources.configuration.fontScale
        val textSizePx = 12.5f * density * fontScale
        Markwon.builder(context)
            .usePlugin(StrikethroughPlugin.create())
            .usePlugin(TablePlugin.create(context))
            .usePlugin(MarkwonInlineParserPlugin.create())
            .usePlugin(JLatexMathPlugin.create(textSizePx) { builder ->
                builder.inlinesEnabled(true)
            })
            .build()
    }

    AndroidView(
        factory = { ctx ->
            TextView(ctx).apply {
                setTextColor(textColorArgb)
                textSize = 12.5f
                setLineSpacing(3f, 1f)
            }
        },
        update = { textView ->
            textView.setTextColor(textColorArgb)
            val cleanedMarkdown = ChatViewModel.cleanAssistantText(markdown)
            val processedMarkdown = cleanedMarkdown
                .replace("\\[", "$$")
                .replace("\\]", "$$")
                .replace("\\(", "$$")
                .replace("\\)", "$$")
            markwon.setMarkdown(textView, processedMarkdown)
        }
    )
}

@Composable
fun TypingIndicator() {
    val infiniteTransition = rememberInfiniteTransition(label = "typing")

    Row(
        modifier = Modifier.padding(vertical = 6.dp),
        horizontalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        repeat(3) { index ->
            val alpha by infiniteTransition.animateFloat(
                initialValue = 0.3f,
                targetValue = 1f,
                animationSpec = infiniteRepeatable(
                    animation = tween(600, delayMillis = index * 200),
                    repeatMode = RepeatMode.Reverse
                ),
                label = "dot_$index"
            )
            Box(
                modifier = Modifier
                    .size(5.dp)
                    .clip(CircleShape)
                    .background(AccentPrimary.copy(alpha = alpha))
            )
        }
    }
}
