package com.aarkaa.ai.ui.skills

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
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
import com.aarkaa.ai.data.api.SkillModel
import com.aarkaa.ai.data.api.SkillSummary
import kotlinx.coroutines.launch

@Composable
fun SkillsScreen() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val api = remember { AarkaaApplication.instance.apiClient.createService<AarkaaApiService>() }

    val skills = remember { mutableStateListOf<SkillSummary>() }
    var selectedSkill by remember { mutableStateOf<SkillModel?>(null) }
    var isLoading by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        isLoading = true
        scope.launch {
            try {
                val list = api.listSkills()
                skills.clear()
                skills.addAll(list)
            } catch (e: Exception) {
                // Ignore for offline preview
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
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("Agent Skills Registry", color = TextPrimary, fontSize = 20.sp, fontWeight = FontWeight.Bold)
            IconButton(
                onClick = {
                    selectedSkill = SkillModel(name = "new-skill", content = "# Custom Skill\nDescribe instructions here.")
                }
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add Skill", tint = AccentCyan)
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        if (isLoading) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = AccentCyan)
            }
        } else if (selectedSkill != null) {
            var skillName by remember { mutableStateOf(selectedSkill!!.name) }
            var skillContent by remember { mutableStateOf(selectedSkill!!.content) }

            Card(
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxSize()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    OutlinedTextField(
                        value = skillName,
                        onValueChange = { skillName = it },
                        label = { Text("Skill Identifier") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = skillContent,
                        onValueChange = { skillContent = it },
                        label = { Text("SKILL.md Instruction Content") },
                        modifier = Modifier
                            .fillMaxWidth()
                            .weight(1f)
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.End
                    ) {
                        TextButton(onClick = { selectedSkill = null }) {
                            Text("Back", color = TextSecondary)
                        }
                        Spacer(modifier = Modifier.width(8.dp))
                        Button(
                            onClick = {
                                scope.launch {
                                    try {
                                        api.createSkill(SkillModel(name = skillName.trim(), content = skillContent))
                                        Toast.makeText(context, "Skill saved!", Toast.LENGTH_SHORT).show()
                                        selectedSkill = null
                                    } catch (e: Exception) {
                                        Toast.makeText(context, "Save Error: " + e.message, Toast.LENGTH_LONG).show()
                                    }
                                }
                            },
                            colors = ButtonDefaults.buttonColors(containerColor = AccentCyan)
                        ) {
                            Text("Save Skill", color = DarkBackground)
                        }
                    }
                }
            }
        } else {
            LazyColumn {
                items(skills) { item ->
                    Card(
                        colors = CardDefaults.cardColors(containerColor = DarkSurface),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp)
                            .clickable {
                                scope.launch {
                                    try {
                                        val full = api.getSkill(item.name)
                                        selectedSkill = full
                                    } catch (e: Exception) {
                                        Toast.makeText(context, "Failed to load skill", Toast.LENGTH_SHORT).show()
                                    }
                                }
                            }
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Text(item.name, color = AccentCyan, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                            if (item.description.isNotEmpty()) {
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(item.description, color = TextSecondary, fontSize = 13.sp)
                            }
                        }
                    }
                }
            }
        }
    }
}
