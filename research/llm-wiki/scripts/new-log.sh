#!/bin/bash
# 새 로그 항목 생성 스크립트 (multi-repo wiki 패턴용)
# 사용법: ./new-log.sh "타이틀" ["상세내용"]
# 예: ./new-log.sh "크론 스케줄 변경: 오전 9시로 이동"

TIMESTAMP=$(date +%Y-%m-%d-%H%M)
YEAR=$(date +%Y)
LOREPO="${1:-$HOME/.hermes/log-repo}"

mkdir -p "$LOREPO/$YEAR"

if [ -n "$2" ]; then
  TITLE="$2"
else
  read -p "로그 제목: " TITLE
fi

FILE="$LOREPO/$YEAR/$TIMESTAMP.md"

cat > "$FILE" << EOF
# [$(date '+%Y-%m-%d %H:%M')] $TITLE

## Summary

${3:-TODO: 내용 추가}

## Changes

### Added / Created


### Updated / Changed


### Removed / Archived


EOF

echo "✅ Created: $FILE"
echo ""
echo "Next steps:"
echo "  1. Edit: $FILE" 
echo "  2. cd $LOREPO && git add \$YEAR/$TIMESTAMP.md"
echo "  3. Update index.md if needed"
echo "  4. git commit -m 'log: $TITLE' && git push"
