#!/bin/bash
# Obsidian vault → Quartz content 동기화 + 배포
VAULT="$HOME/Library/CloudStorage/GoogleDrive-chaedamflow@gmail.com/내 드라이브/Obsidian"
CONTENT="/Volumes/Seoyul2T/Coding/quartz-notes/content"

rsync -av --delete \
  --exclude='.obsidian' \
  --exclude='.trash' \
  "$VAULT/" "$CONTENT/"

cd /Volumes/Seoyul2T/Coding/quartz-notes
git add -A
git commit -m "docs: sync notes $(date +%Y-%m-%d)" 2>/dev/null
git push 2>/dev/null

echo "동기화 완료"
