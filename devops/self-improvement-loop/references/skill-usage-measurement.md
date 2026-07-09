# Skill Usage Measurement — SQLite state.db 쿼리 레시피

> idle-time 자율 hygiene 워크플로우의 **Phase 1 (WHAT)** 핵심 데이터 소스.
> skill 사용 빈도 → uninstall 후보 분류 → 사용자 결정 보고.

## 데이터 소스

- `~/.hermes/state.db` — 모든 에이전트 세션 메시지/도구 호출 영구 저장
- 테이블: `messages` (role, tool_name, tool_calls, content, timestamp)
- `tool_name='skill_view'`인 행의 `content` JSON에서 `name` 필드 추출

## 측정 쿼리 (재현)

```bash
cd ~/.hermes

# 1) 최근 90일 skill_view 호출 빈도
sqlite3 state.db "SELECT content FROM messages \
  WHERE tool_name='skill_view' \
  AND timestamp > strftime('%s','now','-90 days');" | \
  python3 -c "
import sys, json, re
seen = {}; n = 0
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    try: d = json.loads(line)
    except: continue
    s = json.dumps(d) if isinstance(d,(dict,list)) else ''
    m = re.search(r'\"name\"\s*:\s*\"([a-z][a-z0-9_-]+)\"', s)
    if m:
        seen[m.group(1)] = seen.get(m.group(1),0)+1
        n += 1
print(f'total: {n}')
for k,v in sorted(seen.items(), key=lambda x:-x[1]):
    print(f'{v:4} {k}')
"
```

## 통합 Used 결정 (cron + 90d skill_view)

```bash
# cron이 참조하는 스킬
hermes cron list 2>&1 > /tmp/cronlist.txt
CRON_USED=$(grep -oE "Skills:[[:space:]]+[a-z][^[:space:]]*(, [a-z][^[:space:]]*)*" /tmp/cronlist.txt | \
  sed 's/Skills:[[:space:]]*//' | tr ',' '\n' | tr -d ' ' | sort -u)

# 통합 used
ALL_USED=$(echo -e "$USED_90D\n$CRON_USED" | sort -u | grep -v '^$')

# uninstall 후보 (디스크 only, used X)
ALL_DISK=$(ls -d ~/.hermes/skills/*/ | xargs -n1 basename | sort)
comm -23 <(echo "$ALL_DISK") <(echo "$ALL_USED")
```

## 주의사항 (Pitfall)

| 함정 | 회피법 |
|---|---|
| `tool_calls` JSON이 NULL처럼 보임 | `content` 컬럼에 결과 JSON이 들어있음, `tool_name`만 카운트 가능 |
| 90일 윈도우 짧음 | 180일로 늘리면 안정적이지만 데이터 부족 시 top만 의미 있음 |
| 카테고리 폴더 vs 실제 스킬 | `~/.hermes/skills/category/skill-name/SKILL.md` 구조. 카테고리 단위 uninstall ❌, 실제 SKILL.md 단위로 결정 |
| 메모리/위키에 명시 참조된 스킬 | 자동 uninstall ❌. `grep "skill_view\|load(skill=" ~/.hermes/memory/ ~/.hermes/wiki/`로 cross-check |
| Cron의 `Skills:` 필드 파싱 | `awk`로 split, 쉼표+공백 trim, sort -u |

## 검증된 결과 예시 (2026-07-07)

- 90일 skill_view 호출 83건, top: fair-value-portfolio(16) / daily-survey(8) / self-healing-cron(8)
- cron 참조 7개 + skill_view 27개 = used 27 / unused 32 카테고리
- 보고만, **자동 uninstall ❌** (사용자 의도 보존 가능성)

## 활용 위치

- `self-improvement-loop` SKILL.md "Idle-time 자율 hygiene 워크플로우" 섹션의 **Phase 1 WHAT 입력**
- `daily-repo-orchestrator` 가 owner 레포 진단 시 "이 레포에 어떤 스킬이 매핑되는가" cross-ref

## 데이터 신뢰도

| 측정 | 신뢰도 | 비고 |
|---|---|---|
| skill_view 90d | high | 직접 호출 = 강한 사용 신호 |
| cron skills | high | 자동 호출 = 강한 사용 신호 |
| 메모리/위키 참조 | medium | 명시 참조만 잡힘 (암묵 사용은 놓침) |
| 카테고리 폴더 크기 | low | 큰 카테고리 = 안 쓰는 스킬 다수 포함 가능, 의미 없음 |

## 메모리 사용량 정밀 측정 (memory_alert.py, 2026-07-07 검증)

> memory.md cap 2,200 chars 정확 측정. byte count의 ±25% 오차 → ±0% 도달.

**문제**: `wc -c` (byte count)는 UTF-8 multibyte (한글/이모지) 섞이면 ±25% 오차.
**해결**: `wc -m` (codepoint count, multibyte safe).

```python
import subprocess
from pathlib import Path

CAP_CHARS = 2200  # memory.md cap
MEMORY_FILE = Path.home() / ".hermes/memories" / "MEMORY.md"

def count_chars(path: Path) -> int:
    """wc -m: Unicode codepoint count. byte count가 아닌 문자 단위."""
    result = subprocess.run(["wc", "-m", str(path)], capture_output=True, text=True, timeout=5)
    parts = result.stdout.strip().split()
    return int(parts[0]) if parts else 0

mem_chars = count_chars(MEMORY_FILE)
if mem_chars / CAP_CHARS >= 0.9:
    print(f"⚠ MEMORY ALERT: {mem_chars}/{CAP_CHARS} chars"); sys.exit(1)
```

**검증 (2026-07-07)**: memory tool 응답 "2,191 chars" == `wc -m` 2,191 chars 완전 일치.
**ratio**: UTF-8 평균 1.32 bytes/char.

전체 구현: `~/.hermes/scripts/memory_alert.py` (check/stats/fix 3개 서브커맨드).
kanban `t_d627dfea` close. cron 등록은 별도 epic (memory_alert_cron).