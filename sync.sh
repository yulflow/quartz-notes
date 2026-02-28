#!/bin/bash
# Obsidian vault → Quartz content 동기화 + 배포
# publish: true 노트는 /public/ 경로에도 복사 (인증 없이 접근 가능)
VAULT="$HOME/Library/CloudStorage/GoogleDrive-chaedamflow@gmail.com/내 드라이브/Obsidian"
CONTENT="/Volumes/Seoyul2T/Coding/quartz-notes/content"

# 1. 전체 노트 동기화
rsync -av --delete \
  --exclude='.obsidian' \
  --exclude='.trash' \
  --exclude='templates' \
  "$VAULT/" "$CONTENT/"

# 2. publish: true 노트를 public/ 폴더에 복사
rm -rf "$CONTENT/public"
mkdir -p "$CONTENT/public"

find "$CONTENT" -maxdepth 1 -name "*.md" | while read -r file; do
  if grep -q "^publish: true" "$file" 2>/dev/null; then
    cp "$file" "$CONTENT/public/"
  fi
done

# 하위 폴더도 검색
find "$CONTENT" -mindepth 2 -name "*.md" -not -path "*/public/*" | while read -r file; do
  if grep -q "^publish: true" "$file" 2>/dev/null; then
    rel="${file#$CONTENT/}"
    dir="$CONTENT/public/$(dirname "$rel")"
    mkdir -p "$dir"
    cp "$file" "$dir/"
  fi
done

# public 폴더에 index 생성
cat > "$CONTENT/public/index.md" << 'INDEXEOF'
---
title: Public Notes
publish: true
---

# Public Notes

공개된 노트 목록입니다.
INDEXEOF

# 3. 커밋 + 배포
cd /Volumes/Seoyul2T/Coding/quartz-notes
git add -A
git commit -m "docs: sync notes $(date +%Y-%m-%d)" 2>/dev/null
git push 2>/dev/null

echo "동기화 완료"
echo "공개 노트: $(find "$CONTENT/public" -name "*.md" | wc -l | tr -d ' ')개"
