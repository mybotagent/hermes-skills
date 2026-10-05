---
tags: [shell, bash, bug-fixes, debugging, meeting-scripts, hermes-scripts]
---

# Shell Script Bug Fixes — Hermes Script 작성 시 발견한 함정

> `meeting_incremental_save.sh` 작성 중 (2026-06-29) 발견한 6개 함정. 다음에 비슷한 bash 도구 만들 때 **미리 회피**하기 위함.

## 1. `set -e` + `grep -c` exit 1

**증상**: `set -e` 활성화 상태에서 `grep -c PATTERN FILE`이 매치 0개면 exit 1 반환 → 스크립트 즉시 종료. 명시적 에러 메시지 없이 조용히 죽음.

**예시 (실패)**:
```bash
set -e
PHASE_COUNT=$(grep -c "^## Phase" "$FILE")  # 매치 0개면 여기서 종료
echo "count: $PHASE_COUNT"  # 실행 안 됨
```

**해결**:
```bash
set +e  # 의도적으로 set -e 비활성 — 각 단계를 명시적으로 처리
# 또는
set -e
PHASE_COUNT=$(grep -c "^## Phase" "$FILE" || true)
```

**aiprofit 워크플로우 노트**: set -e는 "조용히 죽는" anti-pattern. 모든 단계 명시적 처리 + exit code 확인이 더 안전.

## 2. `$(... || echo 0)` multi-line 출력

**증상**: grep -c가 매치 0개면 "0" 출력 + exit 1. `|| echo 0`이 같이 출력됨 → `$(...)` 안에 "0\n0" 두 줄 들어가서 multi-line 변수.

**예시 (실패)**:
```bash
PHASE_COUNT=$(grep -c "^## Phase" "$FILE" 2>/dev/null || echo 0)
echo "$PHASE_COUNT"  # 출력: "0\n0" (newline)
```

**해결**:
```bash
if [ -s "$FILE" ]; then
    PHASE_COUNT=$(grep -c "^## Phase" "$FILE" 2>/dev/null || true)
    PHASE_COUNT="${PHASE_COUNT:-0}"
else
    PHASE_COUNT=0
fi
```

핵심: 파일이 비어 있으면 0, 있을 때만 grep. exit 1은 `|| true`로 흡수.

## 3. `find`에 `-printf` 빼먹음

**증상**: `find DIR -type d`만 쓰면 DIR만 출력됨. `%T@ %p` 형식 (timestamp + path)을 못 잡음. awk 파싱에서 모든 라인이 DIR로 잡혀서 TS는 비어있음 → "DIR=" 다음 줄이 또 "DIR=".

**예시 (실패)**:
```bash
find /home/ubuntu/meeting-notes -mindepth 3 -maxdepth 3 -type d 2>/dev/null
# 출력: /home/ubuntu/meeting-notes/.git/refs/heads
#       /home/ubuntu/meeting-notes/.git/objects/a1
#       ... (path만)
# awk로 TS=path[0], DIR=path[1] 파싱하면 TS=path, DIR=""
```

**해결**:
```bash
find "$DIR" -mindepth 3 -maxdepth 3 -type d -printf '%T@ %p\n' 2>/dev/null
# 출력: 1782738000.33 /home/ubuntu/meeting-notes/.git/refs/heads
#       1782737988.01 /home/ubuntu/meeting-notes/2026/06/28/...
```

## 4. Float TS를 `[ ... -gt ... ]`로 비교

**증상**: `find -printf '%T@'`가 float (예: `1782738000.3366175690`) 반환. bash의 `[ ... -gt ... ]`는 정수만 비교 → "integer expression expected" 에러 + 스크립트 종료.

**예시 (실패)**:
```bash
LATEST_TS=0
TS="1782738000.33"
if [ "$TS" -gt "$LATEST_TS" ]; then  # ← 에러
    LATEST_TS="$TS"
fi
```

**해결**:
```bash
# awk로 float 비교
if [ -z "$LATEST_TS" ] || awk "BEGIN {exit !($TS > $LATEST_TS)}"; then
    LATEST_TS="$TS"
    DATE_DIR="$DIR"
fi
```

또는: `LATEST_TS=""`로 시작 + 첫 iteration는 무조건 set.

## 5. `find -path '*/.git' -prune` 매칭 안 됨

**증상**: 일부 shell 버전에서 `(-path '*/.git' -prune)` 표현식 매칭이 일관 안 됨. .git/objects 같은 하위 디렉토리가 .git으로 시작하는데 `*/.git` 패턴은 정확히 .git만 매치하려 해서 일부 누락.

**예시 (실패)**:
```bash
DATE_DIR=$(find "$NOTES_DIR" -type d -mindepth 2 -maxdepth 3 \( -path '*/.git' -prune \) -o ... -printf '%T@ %p\n' | sort -nr | head -1 | awk '{print $2}')
# 결과: .git/refs/heads 가 잡힘 (.git 자체만 prune되고 하위는 안 됨)
```

**해결**: 후처리 case 문으로 명시적 스킵:
```bash
while IFS= read -r line; do
    DIR=$(echo "$line" | awk '{print $2}')
    [ -z "$DIR" ] && continue
    case "$DIR" in *".git"*) continue ;; esac  # .git 모든 경로 스킵
    case "$DIR" in *"/.git/"*) continue ;; esac
    # ... 처리
done
```

## 6. .git/objects의 pack 파일 ts가 회의 폴더 ts보다 클 수 있음

**증상**: `.git/objects/pack/pack-XXX.pack`은 git commit/push 시마다 mtime 갱신. 회의 폴더 자체의 mtime보다 .git/objects의 mtime이 더 최신일 수 있음. "가장 최근 YYYY/MM/DD 폴더"를 결정할 때 .git이 잘못 선택됨.

**해결**: 두 단계 방어:
1. case로 .git 경로 명시적 스킵 (위 5번)
2. REL regex로 `^[0-9]{4}/[0-9]{2}/[0-9]{2}$` 형식만 매치 — .git은 REL이 ".git"이므로 regex 불일치 → 자동 스킵

```bash
REL="${DIR#$NOTES_DIR/}"
if [[ "$REL" =~ ^[0-9]{4}/[0-9]{2}/[0-9]{2}$ ]]; then
    # ... 처리
fi
```

이중 방어로 .git/objects 잘못 선택 가능성 0.

---

## 일반화된 디버깅 워크플로우 (bash script)

새 bash script 작성 시:

1. **`set +e`로 시작** (조용한 죽음 방지)
2. **빈 파일 가드** — `if [ -s FILE ]; then ... else DEFAULT; fi` 패턴으로 multi-line 회피
3. **`grep -c ... || true`** — exit 1 흡수
4. **`find -printf '%T@ %p\n'`** — timestamp + path 형식 명시
5. **float 비교는 awk** — bash의 `[ -gt ]`는 정수만
6. **.git / .venv / node_modules 등 noise dir은 case로 명시적 스킵**
7. **`bash -x script.sh`** — 실행 추적으로 어디서 죽는지 즉시 확인 가능
8. **`bash -n script.sh`** — syntax 검증 (런타임 X)
9. **에러 메시지 출력** — 스크립트 안에서 `echo "❌ ..."` 패턴으로 어디서 실패했는지 즉시 보임
10. **`heredoc` + `${VAR:-default}`** — 환경 변수 누락 시 안전한 기본값

---

## Reference Script: meeting_incremental_save.sh

전체 70줄 코드, 위 6개 함정 모두 회피한 패턴:

```bash
#!/bin/bash
set +e  # 조용한 죽음 방지

NOTES_DIR="${HOME}/meeting-notes"

# 1) 날짜 폴더 결정 (YYYY/MM/DD)
DATE_DIR=""
if [[ "$1" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    YYYY="${1%-[0-9][0-9]-[0-9][0-9]}"
    MM_DD="${1#*-}"
    MM="${MM_DD%-[0-9][0-9]}"
    DD="${MM_DD#*-}"
    DATE_DIR="$NOTES_DIR/$YYYY/$MM/$DD"
    shift
fi

SLUG="${1:?Usage: $0 [YYYY-MM-DD] HHMM_topic-slug [commit message]}"
CUSTOM_MSG="${2:-}"

# 2) auto-detect: 가장 최근 YYYY/MM/DD (float-safe + .git 스킵)
if [ -z "$DATE_DIR" ] || [ ! -d "$DATE_DIR" ]; then
    DATE_DIR=""
    LATEST_TS=""
    while IFS= read -r line; do
        TS=$(echo "$line" | awk '{print $1}')
        DIR=$(echo "$line" | awk '{print $2}')
        [ -z "$DIR" ] && continue
        case "$DIR" in *".git"*) continue ;; esac
        REL="${DIR#$NOTES_DIR/}"
        if [[ "$REL" =~ ^[0-9]{4}/[0-9]{2}/[0-9]{2}$ ]]; then
            if [ -z "$LATEST_TS" ] || awk "BEGIN {exit !($TS > $LATEST_TS)}"; then
                LATEST_TS="$TS"
                DATE_DIR="$DIR"
            fi
        fi
    done < <(find "$NOTES_DIR" -mindepth 3 -maxdepth 3 -type d -printf '%T@ %p\n' 2>/dev/null)
fi

if [ -z "$DATE_DIR" ] || [ ! -d "$DATE_DIR" ]; then
    echo "❌ meeting-notes 날짜 폴더 없음" >&2
    exit 1
fi

MEETING_DIR="$DATE_DIR/$SLUG"
if [ ! -d "$MEETING_DIR" ]; then
    echo "❌ 회의 폴더 없음: $MEETING_DIR" >&2
    echo "Available in $(basename $DATE_DIR):" >&2
    ls "$DATE_DIR" | sed 's/^/    /' >&2
    exit 1
fi

# 3) Phase / Decision 카운트 (빈 파일 + exit 1 안전)
if [ -s "$MEETING_DIR/discussion.md" ]; then
    PHASE_COUNT=$(grep -c "^## Phase" "$MEETING_DIR/discussion.md" 2>/dev/null || true)
    PHASE_COUNT="${PHASE_COUNT:-0}"
else
    PHASE_COUNT=0
fi

if [ -s "$MEETING_DIR/decisions.md" ]; then
    DECISION_COUNT=$(grep -c "^## " "$MEETING_DIR/decisions.md" 2>/dev/null || true)
    DECISION_COUNT="${DECISION_COUNT:-0}"
else
    DECISION_COUNT=0
fi

NEXT_STEPS_EXISTS="no"
[ -s "$MEETING_DIR/next_steps.md" ] && NEXT_STEPS_EXISTS="yes"

STATUS=$( (grep "^status:" "$MEETING_DIR/agenda.md" 2>/dev/null || true) | head -1 | awk '{print $2}')
[ -z "$STATUS" ] && STATUS="unknown"

# 4) Commit + push
if [ -n "$CUSTOM_MSG" ]; then
    MSG="$CUSTOM_MSG"
else
    SHORT_SLUG=$(basename "$SLUG")
    MSG="Meeting $SHORT_SLUG: incremental snapshot (phases=$PHASE_COUNT, decisions=$DECISION_COUNT, next_steps=$NEXT_STEPS_EXISTS, status=$STATUS)"
fi

echo "📦 Meeting incremental save"
echo "   폴더: $MEETING_DIR"
echo "   phases: $PHASE_COUNT / decisions: $DECISION_COUNT / next_steps: $NEXT_STEPS_EXISTS / status: $STATUS"
echo ""

cd "$NOTES_DIR" || exit 1

CHANGED=$(git status --porcelain)
if [ -z "$CHANGED" ]; then
    echo "✅ 변경 없음 — push 스킵"
    exit 0
fi

git add -A
if git commit -m "$MSG" 2>&1 | head -3; then
    if git push origin main 2>&1 | tail -2; then
        echo "✅ push 완료. 회의 진행 안전."
    else
        echo "⚠️ push 실패 — 로컬에는 저장됨"
    fi
else
    echo "❌ commit 실패"
    exit 1
fi
```
