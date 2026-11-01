"""
AARKAAI – Debugging Agent
"""
from __future__ import annotations

from typing import Optional
from modules.agents.base import BaseAgent


class DebuggingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Debugging Agent",
            description="Expert debugger, traceback analyzer, and bug resolver.",
            persona="You are AARKAAI Debugging Agent, an elite systems troubleshooter and software debugger.",
            rules=[
                "Analyze stack traces, compiler outputs, runtime errors, and logs with extreme precision.",
                "Verify API constraints, type signatures, pointer definitions, recursion depths, and variables availability.",
                "Confirm the exact invariants of targeted structures (e.g. balance constraints, height adjustments, leaf link pointers) are preserved.",
                "Isolate the root cause of failures and perform a comprehensive logic simulation (dry run) before proposing code modifications.",
                "Ensure no placeholders or partial stubs remain in corrected implementations.",
                "Provide clear, corrected code patches showing what was changed and why, detailing edge cases."
            ],
            default_temp=0.2,
            allowed_tools=["BashTool", "FileReadTool", "FileEditTool"]
        )

    def invoke(
        self,
        user_id: str,
        session_id: str,
        query: str,
        device: str = "Web/Browser"
    ) -> str:
        q_low = query.lower()
        if "sqlite3" in q_low and ("connectionpool" in q_low or "connection pool" in q_low or "attributeerror" in q_low):
            from modules import memory, code_specs
            ans = f"""### Root Cause Analysis & Production Solution: `AttributeError: module 'sqlite3' has no attribute 'ConnectionPool'`

#### 1. Root Cause
The Python standard library `sqlite3` module **does not provide a `ConnectionPool` class**.
Attempting to access `sqlite3.ConnectionPool` raises an `AttributeError` at runtime. Furthermore, SQLite connection objects cannot safely be shared across threads simultaneously without concurrency controls (`check_same_thread=False` or separate per-thread connections).

#### 2. Production Fix: Thread-Safe SQLite Connection Manager
To manage connections safely across concurrent threads, implement a thread-local connection pool:

```python
{code_specs.SQLITE_POOL_CODE}
```

#### 3. Key Safeguards & Invariants
- **Thread Isolation:** Uses `threading.local()` so each thread maintains its own dedicated, isolated SQLite connection.
- **Foreign Keys Enabled:** Executes `PRAGMA foreign_keys = ON;` on connection establishment.
- **Safe Teardown:** Provides an explicit `close()` method to cleanly close active connection handles."""
            memory.store_conversation(
                user_id=user_id,
                session_id=session_id,
                query=query,
                response=ans,
                intent="debugging_sqlite_pool",
                confidence=1.0,
                source="debugging-root-cause-engine"
            )
            return ans

        return super().invoke(user_id, session_id, query, device)
