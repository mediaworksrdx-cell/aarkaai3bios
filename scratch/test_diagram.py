import sys
from modules.agents.verifier import _is_corrupted_diagram, _repair_system_diagram

diagram_text = """
│
├── Request Flow Diagram ──────────────────────┐
│ │
└── URL Shortening Service (Service A)         ├──> │
 │
 │        ├──┘
 ├──────────┤
 User Interaction (API)
 │
 ┌──────────┴────────────────┐
 │                           │
                                Storage Layer (Database B)       │
                                 └───┬──────┼───────────────────┘
 ▼         │
 API Gateway      │
 ┌───────────┴───────┐
 │                  │
 Auth & Rate-Limiting   ├──> │
 │
 ├┘
"""

print("Is corrupted diagram:", _is_corrupted_diagram(diagram_text))
