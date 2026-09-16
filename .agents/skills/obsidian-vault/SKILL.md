---
name: obsidian-vault
description: Search, create, and manage notes in the Obsidian vault with wikilinks and index notes. Use when user wants to find, create, or organize notes in Obsidian.
---

# Obsidian Vault

## Vault location

The vault path is resolved from the environment variable `OBSIDIAN_VAULT_PATH`.

If the variable is not set, auto-detect using the following priority:

1. **Windows native**: `D:\Obsidian Vault\AI Research\`
2. **WSL / Linux**: `/mnt/d/Obsidian Vault/AI Research/`
3. **macOS**: `~/Documents/Obsidian Vault/AI Research/`

To detect the current OS, check for the existence of paths in order. If none exist, ask the user for the vault path before proceeding.

Mostly flat at root level.

## Naming conventions

- **Index notes**: aggregate related topics (e.g., `Ralph Wiggum Index.md`, `Skills Index.md`, `RAG Index.md`)
- **Title case** for all note names
- No folders for organization - use links and index notes instead

## Linking

- Use Obsidian `[[wikilinks]]` syntax: `[[Note Title]]`
- Notes link to dependencies/related notes at the bottom
- Index notes are just lists of `[[wikilinks]]`

## Workflows

### Search for notes

Use the Grep or Find tools directly on the vault path. Example shell commands:

```bash
# Search by filename (use the resolved vault path)
find "$VAULT_PATH" -name "*.md" | grep -i "keyword"

# Search by content
grep -rl "keyword" "$VAULT_PATH" --include="*.md"
```

### Create a new note

1. Use **Title Case** for filename
2. Write content as a unit of learning (per vault rules)
3. Add `[[wikilinks]]` to related notes at the bottom
4. If part of a numbered sequence, use the hierarchical numbering scheme

### Find related notes

Search for `[[Note Title]]` across the vault to find backlinks:

```bash
grep -rl "\[\[Note Title\]\]" "$VAULT_PATH"
```

### Find index notes

```bash
find "$VAULT_PATH" -name "*Index*"
```
