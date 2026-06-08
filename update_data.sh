#!/usr/bin/env bash
# Fetch fresh data from Stadtverbesserer API, score, build, and push.
# Run this locally whenever you want to refresh the dashboard data.
set -euo pipefail

echo "📡 Fetching reports from API..."
uv run --with requests --with pandas fetch_reports.py

echo "📊 Scoring reports and mapping spatial data..."
uv run --with pandas --with numpy --with pyproj --with shapely score_reports.py

echo "📦 Building data.js..."
uv run generate_data_js.py

echo "🚀 Committing and pushing..."
git add stadtverbesserer_snapshot.json stadtverbesserer_snapshot.csv \
        classified_reports.json classified_reports.csv data.js

if ! git diff --cached --quiet; then
  git commit -m "Auto-update reports data: $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
  git push
  echo "✅ Done! Data updated and pushed."
else
  echo "ℹ️  No changes in data files. Nothing to push."
fi
