import sys
sys.path.insert(0, "/home/ubuntu/aarkaai3b")
from modules.aarkaa_engine import _build_final_prompt

p, t, temp = _build_final_prompt("The RBI unexpectedly increases the repo rate by 75 basis points", "[Finance Data] TGT: 143", intent="general_query")
print("PROMPT BUILT SUCCESSFULLY! TOKENS:", t)
