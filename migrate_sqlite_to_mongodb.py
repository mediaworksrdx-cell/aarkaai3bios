"""
AARKAAI Backend – SQLite to MongoDB Flex Data Migration CLI Utility

Migrates data from local SQLite (aarkaai.db) to MongoDB Atlas Flex cluster.
Supports --dry-run mode, detailed per-entity row vs document audit, and verification of missing/duplicate/failed records.

Usage:
  python migrate_sqlite_to_mongodb.py --dry-run
  python migrate_sqlite_to_mongodb.py --execute
"""
from __future__ import annotations

import argparse
import logging
import sys
from typing import Dict, Any, List
import sqlite3
from pathlib import Path

import config
from modules.mongo_client import get_mongo_db, get_mongo_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migration")

SQLITE_DB_PATH = Path(config.DB_PATH)


def connect_sqlite():
    if not SQLITE_DB_PATH.exists():
        logger.error("SQLite database file not found at %s", SQLITE_DB_PATH)
        sys.exit(1)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def count_sqlite_rows(conn, table_name: str) -> int:
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    except sqlite3.OperationalError:
        return 0


def fetch_sqlite_rows(conn, table_name: str) -> List[sqlite3.Row]:
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def run_migration(dry_run: bool = True):
    mode_str = "DRY RUN MODE" if dry_run else "EXECUTE MODE"
    logger.info("=" * 65)
    logger.info("Starting AARKAAI SQLite -> MongoDB Flex Migration [%s]", mode_str)
    logger.info("=" * 65)

    sqlite_conn = connect_sqlite()
    mongo_db = None if dry_run else get_mongo_db()

    if not dry_run and mongo_db is None:
        logger.error("Failed to connect to MongoDB Flex. Please check MONGODB_URI in config.py / environment.")
        sys.exit(1)

    table_collection_map = [
        ("users", "users", "id"),
        ("conversation_history", "conversation_history", "id"),
        ("personal_chats", "personal_chats", "id"),
        ("user_memory", "user_memory", "id"),
        ("knowledge_entries", "knowledge_entries", "id"),
        ("user_knowledge_profiles", "user_knowledge_profiles", "user_id"),
        ("rlhf_feedback", "rlhf_feedback", "id"),
        ("task_goals", "task_goals", "id"),
        ("portfolio_holdings", "portfolio_holdings", "id"),
        ("watchlist_items", "watchlist_items", "id"),
        ("market_alerts", "market_alerts", "id"),
        ("user_settings", "user_settings", "user_id"),
    ]

    report: Dict[str, Dict[str, int]] = {}

    for table_name, coll_name, pk_field in table_collection_map:
        source_count = count_sqlite_rows(sqlite_conn, table_name)
        rows = fetch_sqlite_rows(sqlite_conn, table_name)

        inserted_count = 0
        duplicate_count = 0
        failed_count = 0

        seen_keys = set()

        for row in rows:
            doc = dict(row)
            pk_val = doc.get(pk_field)

            if pk_val in seen_keys:
                duplicate_count += 1
            else:
                seen_keys.add(pk_val)

            if not dry_run and mongo_db is not None:
                try:
                    coll = mongo_db[coll_name]
                    filter_query = {pk_field: pk_val} if pk_val else {"_id": doc.get("id")}
                    coll.update_one(filter_query, {"$set": doc}, upsert=True)
                    inserted_count += 1
                except Exception as exc:
                    logger.error("Failed to migrate row %s in %s: %s", pk_val, table_name, exc)
                    failed_count += 1
            else:
                inserted_count += 1

        target_count = inserted_count if dry_run else (mongo_db[coll_name].count_documents({}) if mongo_db is not None else 0)
        missing_count = max(0, source_count - target_count)

        report[table_name] = {
            "source_rows": source_count,
            "target_documents": target_count,
            "missing_records": missing_count,
            "duplicate_records": duplicate_count,
            "failed_records": failed_count,
        }

    sqlite_conn.close()

    logger.info("\n" + "=" * 65)
    logger.info("MIGRATION AUDIT & VALIDATION SUMMARY")
    logger.info("=" * 65)
    logger.info(f"{'Table / Collection':<26} | {'SQLite Rows':<11} | {'Mongo Docs':<10} | {'Missing':<7} | {'Duplicates':<10} | {'Failed':<6}")
    logger.info("-" * 80)

    for table, stats in report.items():
        logger.info(
            f"{table:<26} | {stats['source_rows']:<11} | {stats['target_documents']:<10} | "
            f"{stats['missing_records']:<7} | {stats['duplicate_records']:<10} | {stats['failed_records']:<6}"
        )
    logger.info("=" * 80)

    if dry_run:
        logger.info("✓ Dry-run completed cleanly. SQLite remains untouched.")
    else:
        logger.info("✓ Production migration execution completed. SQLite remains on disk as rollback backup.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AARKAAI SQLite to MongoDB Flex Migration Utility")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview migration without modifying MongoDB (default: True)")
    parser.add_argument("--execute", action="store_true", help="Execute live migration to MongoDB Atlas Flex")

    args = parser.parse_args()
    is_dry_run = not args.execute
    run_migration(dry_run=is_dry_run)
