"""
AARKAAI Production Operational Tooling – Emergency Rollback CLI.
Usage:
  python scripts/trigger_emergency_rollback.py --action rollback --reason "SLA breach"
  python scripts/trigger_emergency_rollback.py --action rearm
  python scripts/trigger_emergency_rollback.py --action status
"""
import sys
import argparse
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.rollback_automation import rollback_controller

def main():
    parser = argparse.ArgumentParser(description="AARKAAI Emergency Rollback Controller")
    parser.add_argument("--action", choices=["rollback", "rearm", "status"], required=True)
    parser.add_argument("--reason", default="Manual operator command", help="Reason for rollback")
    parser.add_argument("--operator", default="cli_operator", help="Operator ID")

    args = parser.parse_args()

    if args.action == "rollback":
        state = rollback_controller.trigger_rollback(args.reason, args.operator)
        print(f"ROLLBACK EXECUTED: reason='{state.reason}' | CODE_MODE=False | MCP=False")
    elif args.action == "rearm":
        state = rollback_controller.rearm_staging(args.operator)
        print(f"REARM EXECUTED: Controlled Staging Active (CODE_MODE=True, MCP=True, IS_PRODUCTION=False)")
    elif args.action == "status":
        status = rollback_controller.get_status()
        import json
        print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()
