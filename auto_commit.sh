#!/bin/bash
cd /Users/att/passivbot_configs || exit

# Run fswatch loop
/opt/homebrew/bin/fswatch -o . \
  -e ".*\.DS_Store$" \
  -e ".*\.swp$" \
  -e ".*\.tmp$" \
  -e ".*\.log$" \
  | while read f; do
    sleep 10
    git add .
    if ! git diff --cached --quiet; then
      git commit -m "Auto-sync $(date)"
      git push
    fi
done
