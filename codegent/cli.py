"""
cli.py — Step 3: The CLI Interface

Run this to start an interactive coding assistant in your terminal.

Usage:
    python cli.py                        # interactive mode
    python cli.py "fix the bug in app.py"  # single-shot mode
    python cli.py --workspace ./myproject  # specify workspace

Commands while running:
    /reset    — clear conversation history
    /files    — list workspace files
    /exit     — quit
"""

import os
import sys
import argparse
from pathlib import Path

# Force stdout/stderr to use UTF-8 on terminals that don't support unicode by default
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ─── Parse arguments ──────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="AI Coding Assistant")
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Single prompt to run (non-interactive mode)"
    )
    parser.add_argument(
        "--workspace", "-w",
        default="./workspace",
        help="Path to the workspace directory (default: ./workspace)"
    )
    parser.add_argument(
        "--model", "-m",
        default="claude-sonnet-4-6",
        help="Model to use"
    )
    return parser.parse_args()


# ─── Pretty printing ──────────────────────────────────────────────────────────

def print_banner(workspace: str):
    print("\n" + "═" * 55)
    print("  🤖  AI Coding Assistant")
    print(f"  📁  Workspace: {workspace}")
    print("═" * 55)
    print("  Commands: /reset  /files  /exit")
    print("═" * 55 + "\n")

def print_response(text: str):
    print("\n" + "─" * 55)
    print(text)
    print("─" * 55 + "\n")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    # Set workspace env var so tools.py picks it up
    workspace = str(Path(args.workspace).resolve())
    os.environ["AGENT_WORKSPACE"] = workspace
    Path(workspace).mkdir(parents=True, exist_ok=True)

    # Import agent after setting env var
    from agent import CodeAgent
    agent = CodeAgent(model=args.model)

    # Single-shot mode
    if args.prompt:
        print(f"\n🤖 Running: {args.prompt}\n")
        response = agent.chat(args.prompt)
        print_response(response)
        return

    # Interactive mode
    print_banner(workspace)

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! 👋")
            break

        if not user_input:
            continue

        # Built-in commands
        if user_input == "/exit":
            print("\nGoodbye! 👋")
            break
        elif user_input == "/reset":
            agent.reset()
            continue
        elif user_input == "/files":
            from tools import list_files
            print(list_files("."))
            continue

        # Send to agent
        print()
        try:
            response = agent.chat(user_input)
            print_response(response)
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
