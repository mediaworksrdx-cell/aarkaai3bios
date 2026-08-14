---
name: skill-creator
description: Create, test, validate, and iteratively improve specialized skills for AARKAAI.
---

# Skill Creator Skill

This skill allows AARKAAI to act as a "Skill Creator" to design, refine, test, and maintain custom skills (e.g., CSV tools, data parsing tools, API integration templates) on top of AARKAAI.

## High-Level Workflow
1. **Understand Requirements**: Talk with the user to decide what the skill should do and how it should do it.
2. **Draft SKILL.md**: A skill file MUST be a markdown document with a YAML frontmatter header containing exactly:
   ```yaml
   ---
   name: skill-name-with-hyphens
   description: clear description of the skill
   ---
   ```
3. **Validate**: Call `ValidateSkillTool` to ensure the YAML syntax and structure are perfect.
4. **Create**: Use `CreateSkillTool` or `UpdateSkillTool` to save the skill.
5. **Test**: Run test cases with `TestSkillTool` using representative prompts. Help the user evaluate results both qualitatively and quantitatively.
6. **Iterate**: Improve the skill based on test feedback until completion.

## Structure of a Good Skill File
A premium skill document contains:
- Clear installation / dependency instructions.
- Fully commented, drop-in code recipes/templates (e.g., python scripts, styling sheets).
- Troubleshooting guides and edge case handling.
