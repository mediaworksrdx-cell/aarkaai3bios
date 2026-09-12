package com.aarkaai.app.ui.skills

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aarkaai.app.ui.theme.*

data class SkillItem(val name: String, val description: String)
data class SkillCategory(val title: String, val icon: ImageVector, val skills: List<SkillItem>)

val ALL_SKILL_CATEGORIES = listOf(
    SkillCategory(
        title = "Finance & Quantitative Math",
        icon = Icons.Outlined.TrendingUp,
        skills = listOf(
            SkillItem("finance", "Quantitative portfolio construction, Sharpe/Sortino ratios, risk models, and Black-Scholes pricing."),
            SkillItem("dcf-valuation", "Institutional 3-statement Discounted Cash Flow models with WACC & terminal sensitivity tables."),
            SkillItem("market-microstructure", "Order book dynamics, limit orders, spread analysis, and execution slippage modeling.")
        )
    ),
    SkillCategory(
        title = "System Architecture & Engineering",
        icon = Icons.Outlined.Layers,
        skills = listOf(
            SkillItem("architecture", "Distributed systems design, CAP theorem trade-offs, consensus (Raft/Paxos), and microservices."),
            SkillItem("codebase-design", "Deep module interfaces, information hiding, seam placement, and AI-navigable architectures."),
            SkillItem("domain-modeling", "Ubiquitous language construction, DDD entity boundaries, and architectural decision records."),
            SkillItem("design-an-interface", "Parallel multi-agent interface exploration and radical API design comparisons.")
        )
    ),
    SkillCategory(
        title = "Code Quality, Refactoring & QA",
        icon = Icons.Outlined.Code,
        skills = listOf(
            SkillItem("tdd", "Test-driven development, red-green-refactor cycles, and comprehensive integration testing."),
            SkillItem("request-refactor-plan", "Safe incremental refactoring plans broken down into tiny, verifiable commits."),
            SkillItem("diagnosing-bugs", "Root-cause hypothesis generation and regression testing for complex runtime defects."),
            SkillItem("qa", "Interactive QA sessions and conversational GitHub issue filing with domain context."),
            SkillItem("review", "Parallel standards and PRD spec reviews across branch diffs."),
            SkillItem("resolving-merge-conflicts", "Semantic git merge conflict resolution preserving codebase invariants.")
        )
    ),
    SkillCategory(
        title = "Document Generation & Publishing",
        icon = Icons.Outlined.Description,
        skills = listOf(
            SkillItem("pdf", "Strict 6-page high-density executive report generator with embedded Base64 matplotlib charts."),
            SkillItem("obsidian-vault", "Bidirectional markdown knowledge bases, wikilinks, and structured index notes.")
        )
    ),
    SkillCategory(
        title = "Autonomous Subagents & Orchestration",
        icon = Icons.Outlined.Memory,
        skills = listOf(
            SkillItem("skill-router", "Vector FAISS semantic skill discovery and automatic priority execution pipeline."),
            SkillItem("ai-ml", "Dataset pipeline review, training methodologies, evaluation benchmarks, and inference profiling."),
            SkillItem("git-guardrails", "Pre-execution git command interception blocking destructive pushes or resets."),
            SkillItem("setup-pre-commit", "Husky pre-commit hooks with lint-staged, Prettier, and type-checking enforcement.")
        )
    )
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SkillsScreen(
    onNavigateBack: () -> Unit,
    onSkillSelect: (String) -> Unit = {}
) {
    var searchQuery by remember { mutableStateOf("") }

    val filteredCategories = remember(searchQuery) {
        if (searchQuery.isBlank()) {
            ALL_SKILL_CATEGORIES
        } else {
            ALL_SKILL_CATEGORIES.mapNotNull { cat ->
                val matching = cat.skills.filter {
                    it.name.contains(searchQuery, ignoreCase = true) ||
                    it.description.contains(searchQuery, ignoreCase = true) ||
                    cat.title.contains(searchQuery, ignoreCase = true)
                }
                if (matching.isNotEmpty()) cat.copy(skills = matching) else null
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = "Autonomous Skills",
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
                                text = "19 Skills",
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
                colors = TopAppBarDefaults.topAppBarColors(containerColor = BgPrimary)
            )
        },
        containerColor = BgPrimary
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Search Input
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp)
            ) {
                OutlinedTextField(
                    value = searchQuery,
                    onValueChange = { searchQuery = it },
                    placeholder = { Text("Search skills or domain areas…", fontSize = 13.sp, color = TextTertiary) },
                    leadingIcon = { Icon(Icons.Default.Search, contentDescription = null, tint = TextTertiary, modifier = Modifier.size(20.dp)) },
                    trailingIcon = {
                        if (searchQuery.isNotEmpty()) {
                            IconButton(onClick = { searchQuery = "" }) {
                                Icon(Icons.Default.Clear, contentDescription = "Clear", tint = TextTertiary, modifier = Modifier.size(18.dp))
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedContainerColor = BgSecondary,
                        unfocusedContainerColor = BgSecondary,
                        focusedBorderColor = AccentPrimary,
                        unfocusedBorderColor = BorderColor
                    ),
                    singleLine = true
                )
            }

            // Skills List
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
                contentPadding = PaddingValues(bottom = 24.dp, top = 8.dp)
            ) {
                items(filteredCategories) { category ->
                    CategorySection(
                        category = category,
                        onSkillClick = { skill ->
                            onSkillSelect("/${skill.name} ")
                            onNavigateBack()
                        }
                    )
                }
            }
        }
    }
}

@Composable
private fun CategorySection(
    category: SkillCategory,
    onSkillClick: (SkillItem) -> Unit
) {
    Column {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.padding(bottom = 8.dp)
        ) {
            Icon(
                imageVector = category.icon,
                contentDescription = null,
                tint = AccentPrimary,
                modifier = Modifier.size(16.dp)
            )
            Spacer(modifier = Modifier.width(6.dp))
            Text(
                text = category.title,
                fontWeight = FontWeight.Bold,
                fontSize = 12.sp,
                letterSpacing = 0.5.sp,
                color = TextSecondary
            )
        }

        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            category.skills.forEach { skill ->
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, BorderColor, RoundedCornerShape(12.dp))
                        .clickable { onSkillClick(skill) },
                    color = BgSecondary,
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Surface(
                                color = AccentMuted,
                                shape = RoundedCornerShape(6.dp)
                            ) {
                                Text(
                                    text = "/${skill.name}",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace,
                                    color = AccentPrimary,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp)
                                )
                            }
                            Text(
                                text = "Tap to use",
                                fontSize = 10.sp,
                                color = TextTertiary
                            )
                        }
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = skill.description,
                            fontSize = 12.sp,
                            color = TextSecondary,
                            lineHeight = 16.sp
                        )
                    }
                }
            }
        }
    }
}
