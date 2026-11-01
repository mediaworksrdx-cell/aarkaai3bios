import json
import sys
sys.path.insert(0, ".")
from scripts.remediation_data import get_finance_answers, get_trading_answers

fa = get_finance_answers()
print("=== FA Q03 ===")
print(fa.get(3, "NOT FOUND")[:300])

print("\n=== FA Q08 ===")
print(fa.get(8, "NOT FOUND")[:300])

ta = get_trading_answers()
print("\n=== TA Q03 ===")
print(ta.get(3, "NOT FOUND")[:300])
