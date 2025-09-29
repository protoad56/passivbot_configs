#!/bin/bash
cd /Users/att/passivbot_configs || exit

# Run fswatch loop
/opt/homebrew/bin/fswatch -o . | while read f; do
  git add .
  git commit -m "Auto-sync $(date)"
  # Only commit if there are staged changes
  if ! git diff --cached --quiet; then
    git commit -m "Auto-sync $(date)"
    git push
  fi
done
