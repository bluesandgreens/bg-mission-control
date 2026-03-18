#!/usr/bin/env bash
# refresh.sh — Regenerate dashboard data, commit, and push to GitHub Pages
# Usage: ./scripts/refresh.sh [--period today|yesterday|YYYY-MM-DD]
# Cron example (every 30 min): */30 * * * * cd /path/to/mc-live && ./scripts/refresh.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

PERIOD="${1:---period}"
PERIOD_VAL="${2:-today}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting data refresh..."

# Run the data generation script
python3 "$SCRIPT_DIR/generate-data.py" --period "$PERIOD_VAL" --output data/dashboard-data.json

# Check if there are changes to commit
if git diff --quiet data/dashboard-data.json 2>/dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] No data changes detected. Skipping commit."
    exit 0
fi

# Stage and commit the updated data
git add data/dashboard-data.json
git commit -m "chore: refresh dashboard data $(date '+%Y-%m-%d %H:%M')"

# Push to remote
git push origin main

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Data refreshed and pushed successfully."
