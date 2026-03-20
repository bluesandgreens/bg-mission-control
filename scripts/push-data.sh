#!/bin/bash
# Push data files to GitHub after refresh
cd /tmp/mc-live
git add data/
git commit -m "data: auto-refresh $(date '+%Y-%m-%d %H:%M')" --allow-empty
git push origin main
