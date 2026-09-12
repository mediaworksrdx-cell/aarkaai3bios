import json
import sys
sys.path.insert(0, "/home/mediaworksr/aarkaai3b")
from modules import memory

ctx = memory.get_chat_context("guest_visitor", "test_session_qa_10", limit=20)
print(f"Total messages for guest_visitor: {len(ctx)}")
for i, m in enumerate(ctx):
    print(f"[{i}] {m.get('role')}: {m.get('message', '')[:120]}...")
