# AI Coding Assistant

A Claude Code-style coding agent that can read, write, and run code in a workspace.

---

## Setup

### 1. Install dependencies
```bash
pip install anthropic
```

### 2. Set your API key
```bash
export ANTHROPIC_API_KEY=your-key-here
```
Get a key at: https://console.anthropic.com

### 3. Create a workspace
```bash
mkdir workspace
```

---

## Usage

### Interactive mode
```bash
python cli.py
```

### Single-shot mode
```bash
python cli.py "create a Flask REST API with a /health endpoint"
python cli.py "add error handling to app.py"
python cli.py "write tests for utils.py"
```

### Custom workspace
```bash
python cli.py --workspace ./my-project
```

### CLI commands
| Command | What it does |
|---|---|
| `/reset` | Clear conversation history |
| `/files` | List workspace files |
| `/exit` | Quit |

---

## File Structure

```
codegent/
├── cli.py          ← entry point (run this)
├── agent.py        ← agentic loop
├── tools.py        ← file/shell tools the LLM can call
├── prompts.py      ← system prompts for different modes
└── workspace/      ← your project files go here
```

---

## How It Works

```
You type a message
       ↓
cli.py → agent.chat(message)
       ↓
LLM called with tools available
       ↓
  LLM calls tool?  ──YES──→  execute_tool() → result fed back → loop
       ↓ NO
  Final text response
       ↓
Printed to terminal
```

---

## Customizing the Agent

### Change the system prompt
In `agent.py`, replace `SYSTEM_PROMPT` with one from `prompts.py`:
```python
from prompts import get_prompt
# then in CodeAgent.__init__:
self.system_prompt = get_prompt("senior_dev")  # or "debugger", "architect"
```

### Add a new tool
In `tools.py`:
1. Write a new function
2. Add it to `TOOL_DEFINITIONS` (the JSON schema)
3. Add it to the dispatcher in `execute_tool()`

### Add memory (future)
Store `self.history` to a file between sessions to give the agent persistent memory.

---

## Example Session

```
You: create a simple todo app in Python

  🔧 list_files(directory='.')
     → 📁 ./  (empty)
  🔧 write_file(path='todo.py', content='...')
     → ✓ Written 847 chars to todo.py
  🔧 run_command(command='python todo.py --help')
     → usage: todo.py [-h] {add,list,done,remove} ...

─────────────────────────────────────────────
I've created todo.py — a command-line todo app with:
- `add <task>` to add a task
- `list` to show all tasks
- `done <id>` to mark complete
- `remove <id>` to delete

Try: python todo.py add "Build something cool"
─────────────────────────────────────────────
```
