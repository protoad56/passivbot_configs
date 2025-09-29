#!/bin/bash
cd /Users/att/passivbot_configs || exit

# Run fswatch loop
/opt/homebrew/bin/fswatch -o . | while read f; do
  git add .
  git commit -m "Auto-sync $(date)"
  git push 
done
