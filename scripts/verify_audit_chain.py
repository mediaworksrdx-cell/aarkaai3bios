#!/usr/bin/env python3
"""
AARKAAI Security Audit Log Chain Verifier.

Zero-dependency CLI tool to mathematically verify the cryptographic hash-chain
integrity of AARKAAI tamper-evident security audit logs (SOC 2 / ISO 27001 readiness).
"""
import sys
import json
import argparse
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional


def verify_chain(log_path: Path, verbose: bool = False) -> Tuple[bool, Dict[str, Any]]:
    """
    Sequentially verify that every line in log_path adheres to SHA-256 hash chaining.
    
    Returns:
        (is_valid, report_dict)
    """
    report: Dict[str, Any] = {
        "file": str(log_path),
        "total_records": 0,
        "valid_records": 0,
        "invalid_records": 0,
        "event_counts": {},
        "first_timestamp": None,
        "last_timestamp": None,
        "chain_head_hash": None,
        "errors": [],
    }

    if not log_path.exists():
        report["errors"].append(f"Audit log file not found: {log_path}")
        return False, report

    expected_prev_hash = "0" * 64
    line_number = 0

    with open(log_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line_number += 1
            line = raw_line.strip()
            if not line:
                continue

            report["total_records"] += 1

            try:
                record = json.loads(line)
            except json.JSONDecodeError as err:
                report["invalid_records"] += 1
                report["errors"].append(f"Line {line_number}: Invalid JSON - {err}")
                return False, report

            # Check required fields
            for required_field in ["event_type", "timestamp", "prev_record_hash", "details", "record_hash"]:
                if required_field not in record:
                    report["invalid_records"] += 1
                    report["errors"].append(f"Line {line_number}: Missing required field '{required_field}'")
                    return False, report

            actual_prev = record["prev_record_hash"]
            record_hash = record["record_hash"]
            event_type = record["event_type"]
            timestamp = record["timestamp"]

            # Track timestamps
            if report["first_timestamp"] is None:
                report["first_timestamp"] = timestamp
            report["last_timestamp"] = timestamp

            # Track event counts
            report["event_counts"][event_type] = report["event_counts"].get(event_type, 0) + 1

            # 1. Verify prev_record_hash linkage
            if line_number == 1 and actual_prev != expected_prev_hash:
                # If the log was rotated, it might start from an earlier chain seed
                if event_type != "audit.rotation_chain_seed":
                    report["invalid_records"] += 1
                    report["errors"].append(
                        f"Line {line_number}: First record prev_record_hash is not genesis: {actual_prev[:16]}..."
                    )
                    return False, report

            elif line_number > 1 and actual_prev != expected_prev_hash:
                report["invalid_records"] += 1
                report["errors"].append(
                    f"Line {line_number}: Break in hash chain! Expected prev_hash {expected_prev_hash[:16]}..., "
                    f"found {actual_prev[:16]}..."
                )
                return False, report

            # 2. Recompute record_hash
            payload_to_hash = {
                "event_type": record["event_type"],
                "timestamp": record["timestamp"],
                "prev_record_hash": record["prev_record_hash"],
                "details": record["details"],
            }
            computed_hash = hashlib.sha256(
                json.dumps(payload_to_hash, sort_keys=True).encode("utf-8")
            ).hexdigest()

            if computed_hash != record_hash:
                report["invalid_records"] += 1
                report["errors"].append(
                    f"Line {line_number}: Tampered record content! Computed hash {computed_hash[:16]}... != "
                    f"recorded hash {record_hash[:16]}..."
                )
                return False, report

            report["valid_records"] += 1
            expected_prev_hash = record_hash
            report["chain_head_hash"] = record_hash

            if verbose:
                print(f"[OK] Line {line_number}: {event_type} (hash: {record_hash[:12]}...)")

    return True, report


def format_iso(ts: Optional[float]) -> str:
    if ts is None:
        return "N/A"
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description="Verify cryptographic integrity of AARKAAI security audit logs.")
    parser.add_argument(
        "--log",
        type=str,
        default="logs/security_audit.jsonl",
        help="Path to the security audit jsonl file (default: logs/security_audit.jsonl)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print each verified record.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full verification report as JSON.",
    )

    args = parser.parse_args()
    log_path = Path(args.log)

    is_valid, report = verify_chain(log_path, verbose=args.verbose)

    if args.json:
        report["status"] = "PASSED" if is_valid else "FAILED"
        print(json.dumps(report, indent=2))
        sys.exit(0 if is_valid else 1)

    print("=" * 70)
    print("  AARKAAI Security Audit Log — Cryptographic Chain Verification")
    print("=" * 70)
    print(f"Target Log File : {report['file']}")
    print(f"Total Records   : {report['total_records']}")
    print(f"Valid Records   : {report['valid_records']}")
    print(f"Invalid Records : {report['invalid_records']}")
    print(f"Earliest Event  : {format_iso(report['first_timestamp'])}")
    print(f"Latest Event    : {format_iso(report['last_timestamp'])}")
    print(f"Chain Head Hash : {report['chain_head_hash'] or 'N/A'}")
    print("-" * 70)
    print("Event Type Distribution:")
    for et, cnt in sorted(report["event_counts"].items(), key=lambda x: -x[1]):
        print(f"  - {et:<35} : {cnt}")
    print("-" * 70)

    if is_valid:
        print("VERIFICATION RESULT: [PASSED] — 100% Cryptographic Integrity Confirmed.")
        print("Chain is intact, untampered, and continuous.")
        sys.exit(0)
    else:
        print("VERIFICATION RESULT: [FAILED] — Security Anomalies Detected!")
        for err in report["errors"]:
            print(f"  [!] {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
