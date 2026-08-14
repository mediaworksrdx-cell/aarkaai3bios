"""
agent.py — Step 2: The Agentic Loop

This is the core of the system.
It calls the LLM, handles tool calls, feeds results back,
and keeps looping until the LLM gives a final text response.

How it works:
  1. Send user message + conversation history to LLM
  2. LLM either responds with text (done) or calls a tool
  3. If tool call → execute it → add result to history → go to 1
  4. If text → print it → wait for next user message
"""

import os
import json
import anthropic
from tools import TOOL_DEFINITIONS, execute_tool

# ─── System prompt ────────────────────────────────────────────────────────────
# This tells the LLM who it is and how to behave.

SYSTEM_PROMPT = """You are an expert coding assistant with access to a workspace.
You can read files, write files, list directories, run commands, and search code.

Guidelines:
- Always read relevant files before editing them
- Write complete file contents when using write_file (never partial)
- After writing a file, confirm what you did and why
- If something fails, read the error carefully and fix it
- Think step by step for complex tasks
- Ask for clarification if the task is ambiguous

The workspace is your sandbox — feel free to explore it with list_files first.
"""

# ─── The Agent class ──────────────────────────────────────────────────────────

class CodeAgent:
    def __init__(self, model: str = "claude-sonnet-4-6", max_iterations: int = 20):
        self.client = anthropic.Anthropic()
        self.model = model
        self.max_iterations = max_iterations
        self.history = []  # full conversation history

    def chat(self, user_message: str) -> str:
        """
        Send a message and run the agentic loop until we get a final response.
        Returns the final text response.
        """
        # Add user message to history
        self.history.append({
            "role": "user",
            "content": user_message
        })

        iterations = 0

        while iterations < self.max_iterations:
            iterations += 1

            # ── Call the LLM ──────────────────────────────────────────────────
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=self.history,
            )

            # ── Check stop reason ─────────────────────────────────────────────
            # "end_turn"    → LLM is done, has a text answer
            # "tool_use"    → LLM wants to call one or more tools
            # "max_tokens"  → hit token limit (treat as done)

            if response.stop_reason == "end_turn" or response.stop_reason == "max_tokens":
                # Extract text from response
                final_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_text += block.text

                # Add assistant response to history
                self.history.append({
                    "role": "assistant",
                    "content": response.content
                })

                return final_text

            elif response.stop_reason == "tool_use":
                # Add assistant's tool call(s) to history
                self.history.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Execute each tool call and collect results
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_args = block.input
                        tool_use_id = block.id

                        print(f"  🔧 {tool_name}({_fmt_args(tool_args)})")

                        # Run the tool
                        result = execute_tool(tool_name, tool_args)

                        print(f"     → {result[:120]}{'...' if len(result) > 120 else ''}")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result,
                        })

                # Add tool results to history and loop
                self.history.append({
                    "role": "user",
                    "content": tool_results
                })

            else:
                # Unknown stop reason — bail out
                return f"Unexpected stop reason: {response.stop_reason}"

        return "Error: reached max iterations without a final response."

    def reset(self):
        """Clear conversation history to start fresh."""
        self.history = []
        print("🔄 Conversation reset.")


# ─── Helper ───────────────────────────────────────────────────────────────────

def _fmt_args(args: dict) -> str:
    """Format tool args for display, truncating long values."""
    parts = []
    for k, v in args.items():
        v_str = str(v)
        if len(v_str) > 60:
            v_str = v_str[:60] + "..."
        parts.append(f"{k}={repr(v_str)}")
    return ", ".join(parts)
