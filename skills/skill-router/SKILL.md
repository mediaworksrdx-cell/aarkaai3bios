---
name: skill-router
description: >
  Teaches an LLM how to use a skill routing system where skills are stored as
  SKILL.md files indexed by a vector database, and the model fetches relevant
  skill docs at runtime via a get_skill(name) tool call. Use this skill whenever
  you are building or operating a self-hosted LLM that needs to dynamically load
  task-specific instructions based on the user's query. Also use when the model
  needs to decide whether to consult a skill, how to call get_skill(), how to
  read the returned docs, and how to apply them before responding.
---

# Skill Router

You are an LLM equipped with a **skill routing system**. Skills are reusable
instruction documents (SKILL.md files) stored in a registry. Each skill covers
a specific task or domain. You have access to a tool that lets you fetch a
skill's full documentation on demand.

---

## Your Tool

```
get_skill(name: str) -> str
```

- **Input**: the skill's `name` (its identifier, e.g. `"pdf-reader"`, `"sql-formatter"`)
- **Output**: the full contents of that skill's `SKILL.md` file as a string
- Call this **before** attempting any task the skill covers
- You may call it multiple times in one turn if multiple skills are relevant

---

## How to Decide When to Use a Skill

At the start of each user request, ask yourself:

> "Is this a specialized or multi-step task that likely has a skill for it?"

**Call `get_skill` when:**
- The task involves a specific file format (PDF, DOCX, XLSX, PPTX, etc.)
- The task is a known domain with established best practices (SQL, data pipelines, API design, etc.)
- You're unsure of the exact steps, tools, or output format expected
- The task is multi-step and errors early would cascade

**Skip `get_skill` when:**
- The task is simple and conversational ("summarize this paragraph")
- You're confident you already have everything you need
- You already fetched the relevant skill this turn

---

## How to Find the Right Skill Name

You also have access to a skill listing tool:

```
list_skills() -> list[dict]
```

Each entry has:
- `name` — the identifier to pass to `get_skill()`
- `description` — one or two sentences about what the skill covers

**Workflow when unsure of the skill name:**
1. Call `list_skills()` to browse available skills
2. Read descriptions to find the best match
3. Call `get_skill(name)` with the matching name

If the list is long, scan descriptions for keywords from the user's query.

---

## How to Apply a Skill

Once you've called `get_skill()` and received the skill docs:

1. **Read the full document** before doing anything else
2. **Follow its instructions** — treat them as authoritative for this task
3. **Use any tools, scripts, or formats it specifies**
4. If the skill references other files (e.g. `references/api.md`), fetch those
   too via `get_skill()` if they seem relevant

The skill doc overrides your defaults. If the skill says "always output JSON",
do that even if you'd normally use prose.

---

## Transparency

When you call `get_skill()`, briefly tell the user what you're doing:

> "Let me check the skill docs for this task first."

After reading, you can optionally summarize what the skill told you to do before
proceeding — especially helpful for complex multi-step tasks.

---

## Example Turn

**User**: Convert this CSV to a formatted Excel report with charts.

**Model (internal reasoning)**:
- This is a file format + data viz task → likely has a skill
- Skill name is probably something like `xlsx` or `excel-report`

**Model (action)**:
```
list_skills()  →  finds "xlsx": "Create and format Excel spreadsheets..."
get_skill("xlsx")  →  reads full SKILL.md
```

**Model (response)**:
> "I've pulled up the Excel skill. I'll follow its formatting guidelines and
> use openpyxl to build the report. Here's what I'll do: ..."

---

## Skill Document Format

Every SKILL.md starts with YAML frontmatter:

```yaml
---
name: skill-name
description: When to use this skill and what it does.
---
```

The body contains instructions in Markdown. Treat the body as your operating
manual for the duration of the task.

---

## What to Do If No Skill Matches

If `list_skills()` returns nothing relevant, proceed with your best judgment
and tell the user:

> "I don't have a specific skill for this, so I'll use general knowledge."

Never hallucinate a skill name. Only call `get_skill()` with names from
`list_skills()` output.
