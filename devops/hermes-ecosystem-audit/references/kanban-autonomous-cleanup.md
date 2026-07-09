# Kanban Autonomous Cleanup — 2026-07-07

> 자율 모드에서 Kanban 백로그를 자동 정리한 실제 절차. 38 → 13개 ready 감소.
> 다른 세션에서 Kanban 정리가 필요할 때 따라할 수 있는 receipt.

## 트리거

사용자가 다음 중 하나를 말하면 자율 Kanban 정리 모드 발동:
- "작업이 없을 때 알아서 수정할 것 계속 수정"
- "내가 요청하지 않아도 자율 진행"
- "Kanban 정리해줘" + (backlog / dup / false-positive 컨텍스트)

## 워크플로우 (8단계)

### Step 1: 현재 ready/backlog 상태 스냅샷
```bash
hermes kanban boards         # 보드 목록
hermes kanban list           # 전체 태스크 (READY/DONE/BACKLOG)
hermes kanban list | grep -cE "^\▶ "   # ready 카운트
```

### Step 2: Cron skills 참조 추출 (자동 uninstall 분석용)
```bash
hermes cron list > /tmp/cronlist.txt
grep -oE "Skills:[[:space:]]+[a-z][^[:space:]]*(, [a-z][^[:space:]]*)*" /tmp/cronlist.txt \
  | sed 's/Skills:[[:space:]]*//' | tr ',' '\n' | tr -d ' ' | sort -u
```
> `crontab -l`은 hermes가 자체 스케줄러를 쓰면 비어있음. **반드시 `hermes cron list`** 사용.

### Step 3: Skill 사용 빈도 (state.db 90일)
```bash
sqlite3 ~/.hermes/state.db "
SELECT content FROM messages
WHERE tool_name='skill_view'
  AND timestamp > strftime('%s','now','-90 days');" | \
python3 -c "
import sys, json, re
seen={}
for line in sys.stdin:
    try: d=json.loads(line.strip())
    except: continue
    s=json.dumps(d) if isinstance(d,(dict,list)) else ''
    m=re.search(r'\"name\"\s*:\s*\"([a-z][a-z0-9_-]+)\"', s)
    if m: seen[m.group(1)]=seen.get(m.group(1),0)+1
for k,v in sorted(seen.items(), key=lambda x:-x[1]):
    print(f'{v:4} {k}')
"
```

### Step 4: 중복 작업 분류 (dup detection)

**Rule 1**: 같은 created timestamp + 비슷한 제목 = duplicate
```bash
hermes kanban show t_xxxx | grep -E "^Task|created:" | head -3
```

**Rule 2**: body가 비어있고 제목만 있을 때 = 제목 패턴으로 dup 판단
- "[Audit Action N]" 패턴 → 동일 audit epic 하위 task 묶음
- "Kanban 백로그 재평가" 패턴 → 같은 메타 작업 (한 번에 1개만 유지)
- "Wiki SCHEMA.md lint 8종" 패턴 → 1개 canonical 유지

**Rule 3**: safe close 요건
- ✅ false-positive close (실제 검증으로 부재 확인 후)
- ✅ dup close (동일 제목 + 같은 created)
- ✅ already-done epic close (서브 task 모두 Done 확인 후)
- ✅ 검증-only close (merge conflict 마커 등 검색 결과 0건 확인 후)
- ❌ audit/설계/정책 task (사용자 결정 영역)

### Step 5: 작업 close 패턴

```bash
# dup close — 어떤 본문을 남길지 (close되는 쪽)
hermes kanban complete t_xxxx \
  --summary 'duplicate of t_yyyy (same body, ...). keeping t_yyyy' \
  --metadata '{"resolution":"dup","canonical":"t_yyyy"}'

# false-positive close — 검증 결과 명시
hermes kanban complete t_xxxx \
  --summary 'false-positive: <actual evidence>. <expected pattern>' \
  --metadata '{"resolution":"false-positive","verified_path":"..."}'

# audit Action N — 처리한 내용 또는 미처리 사유 명시
hermes kanban complete t_xxxx \
  --summary 'audit Action N 검토 결과 ... 결정 (진행/유지/통합)' \
  --metadata '{"audit":"2026-07-03","action":N,"decision":"..."}'
```

### Step 6: 의미 있는 작업 (의미 있는 결과물 만들기)

단순 정리만 하지 말고 의미 있는 산출물 1~2개 만들기. 이번 세션:
- `~/.hermes/scripts/memory_alert.py` 작성 (memory_entries ±0% 측정)
  - `wc -m` (codepoint count) — UTF-8 multibyte safe
  - 메모리 tool 응답 (2,191 chars) == `wc -m` 결과 완전 일치 검증

### Step 7: 로그 작성
```bash
LOGS_DIR=~/mybotagent/hermes-logs/logs/$(date +%Y)
mkdir -p "$LOGS_DIR"
cat > "$LOGS_DIR/$(date +%Y-%m-%d-%H%M)-autonomous-cleanup-round-N.md" <<'EOF'
# Autonomous Cleanup Round N — DATE

## 처리 (총 N개 close)
### Dup 정리 (N)
- t_xxx ≡ t_yyy
### Epic/Auto 완료 (N)
### 검증 (N)

## 의미 있는 산출물
- <script path> — <purpose>
EOF
```

### Step 8: 사용자 보고 (한국어)
- 처리 N개 close, ready M → K
- 카테고리별 그룹 (dup / false-positive / audit / epic / 검증)
- 잔여 ready 큰 그림 (메타 / 정책 / 실행 가능 분류)
- 의미 있는 산출물 하이라이트

## Pitfalls

### 1. `crontab -l` 사용 금지
Hermes는 자체 cron 스케줄러 사용. `hermes cron list`가 single source.

### 2. `hermes kanban show` body가 비어있을 수 있음
생성 시 body 미기입 → 제목만으로 dup 판단. created timestamp로 보강.

### 3. 자동 uninstall 절대 금지
90일 0회 사용이라도 사용자 의도 보존 가능 (실험/예비용). **보고만**하고 사용자 결정.

### 4. 정책/설계 task는 close 금지
- "Phase X: 자동 압축 정책 합의" → 사용자 합의 필요
- "memory → wiki watcher DESIGN.md" → 사용자 DESIGN 결정 필요
- "Cron Deliver Target Mismatch → Thread Registry" → 채니봇 작업
- 이런 task는 unassign + 'waiting_user_decision' comment만.

### 5. Skill 디렉토리는 카테고리 폴더 (실제 uninstall 시)
`ls ~/.hermes/skills/` 결과는 **카테고리 폴더** (apple/, creative/, github/...). 실제 SKILL.md는 그 안에. uninstall 보고 시 카테고리 단위로 보고.

### 6. Linear 이슈는 Kanban과 별도
같은 작업이 SHO-XX (Linear) + t_xxxx (Kanban)에 둘 다 있을 수 있음. SHO는 사용자 결정, Kanban은 자율 close OK.

### 7. 중복 close 순서
오래된 created + 더 큰 ID close, 새 것 유지. 단, created 동일하면 ID 알파벳순 큰 쪽 close (해시 무관).

## 결과 패턴 (이번 세션)

| 라운드 | ready 변화 | close 수 | 의미 있는 산출물 |
|---|---|---|---|
| 1 (작업 없을 때) | 38 → 32 | 6 | false-positive 정리 |
| 2 (자율 진행) | 23 → 13 | 9 | memory_alert.py 작성 |

각 라운드 = ~30분 작업. 사용자가 명시적으로 중단 안 하면 다음 idle 시 계속 가능.