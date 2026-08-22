#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# AARKAAI — Git History Scrub Script
#
# PURPOSE: Remove all traces of committed secrets from Git history.
# WARNING: This rewrites Git history. All collaborators must re-clone.
#
# PREREQUISITES:
#   pip install git-filter-repo
#
# USAGE:
#   bash scrub_git_history.sh
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  AARKAAI — Git History Scrub                            ║"
echo "║  This will PERMANENTLY rewrite Git history.             ║"
echo "║  All collaborators must re-clone after this operation.  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
if ! command -v git-filter-repo &> /dev/null; then
    echo "ERROR: git-filter-repo not found. Install with: pip install git-filter-repo"
    exit 1
fi

echo "Scrubbing the following files from ALL Git history:"
echo "  - .env                    (production credentials)"
echo "  - orbital-heaven-*.json   (GCP service account key)"
echo "  - aarkaai.db              (SQLite with user data)"
echo "  - urls.db                 (SQLite with URL data)"
echo ""

read -p "Are you sure you want to proceed? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Step 1/3: Running git filter-repo..."
git filter-repo --invert-paths \
  --path .env \
  --path .env.production \
  --path .env.local \
  --path orbital-heaven-504004-s2-df5a0ce91659.json \
  --path aarkaai.db \
  --path urls.db \
  --force

echo ""
echo "Step 2/3: Verifying files are removed from history..."
for file in ".env" "orbital-heaven-504004-s2-df5a0ce91659.json" "aarkaai.db" "urls.db"; do
    count=$(git log --all --diff-filter=A --name-only --pretty=format:"" -- "$file" 2>/dev/null | grep -c "$file" || true)
    if [ "$count" -gt 0 ]; then
        echo "  WARNING: $file still found in $count commits!"
    else
        echo "  OK: $file fully removed from history"
    fi
done

echo ""
echo "Step 3/3: To push the rewritten history to remote:"
echo "  git remote add origin <your-remote-url>"
echo "  git push origin --force --all"
echo "  git push origin --force --tags"
echo ""
echo "IMPORTANT: After pushing, ALL collaborators must:"
echo "  1. Delete their local clone"
echo "  2. Re-clone from the remote"
echo "  3. Set up their .env from .env.example"
echo ""
echo "Done. Remember to rotate ALL credentials listed in the audit report."
