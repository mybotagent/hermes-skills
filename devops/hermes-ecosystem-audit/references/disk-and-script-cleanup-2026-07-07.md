# Disk + Cron + Script Cleanup (2026-07-07 검증 사례)

> 실제 측정 데이터 + 절차 + Pitfall. 다음 audit 시 baseline.

## 📊 측정 결과 (BEFORE/AFTER)

### Disk 회수 (~4.3GB)

| 항목 | Before | After | 회수 | 안전성 |
|---|---:|---:|---:|:---:|
| `~/.cache/pip` | 2.5G | 4.6M | **2.5GB** | ✅ |
| `~/.cache/uv` | 1.4G | 0 | **1.4GB** | ✅ |
| state-snapshots/state.db | 234M | 96M (gz) | **138MB** | ⚠️ |
| state.db-wal | 282M | 0 | **282MB** | ✅ |
| state.db (vacuum) | 275M | 268M | **7MB** | ✅ |
| **합계** | | | **~4.3GB** | |

### Cron NEVER-실행 판정

```
총 39개 cron, NEVER: 10개
정체 후보 (NEVER): 10개
진짜 실패: 0개  ← 모두 정상 (방금 등록 또는 미래 scheduled)
```

**결론**: cron `last_run=NEVER`는 **future-scheduled**인 경우가 대부분. 즉시 고장으로 처리하면 안 됨.

### Orphan Script Detection

```
총 35 scripts → cron 참조 22개 → orphan 13개
실제 삭제 가능: 3개
  - auto_merge_smoke_test.sh (1회성 테스트, 1.3KB)
  - dashboard_proxy.py (nginx로 대체됨, 5KB)
  - memory_lazy_fetch.py (memory_query.py로 supersede, 3.9KB)
skill/tool용 orphan 10개: 보존 (cross-reference 검증 후)
```

## 🔧 검증된 절차

### 1. Cron NEVER 판정 (regex)

```python
import re
text = open('/tmp/cron_list.txt').read()
blocks = re.split(r'(?=\n\s*[a-z0-9]{12}\s+\[active\])', text)
for b in blocks:
    m_id = re.match(r'\s*([a-z0-9]{12})\s+\[active\]', b)
    m_name = re.search(r'Name:\s+(.+)', b)
    m_last = re.search(r'Last run:\s+(\S+)', b)
    m_next = re.search(r'Next run:\s+(\S+)', b)
    if m_last:  # 정상
        continue
    # last_run=NEVER → next_run 비교
    if m_next:
        next_time = datetime.fromisoformat(m_next.group(1)[:19])
        now = datetime.now(timezone.utc)
        if next_time > now:
            continue  # 정상 (미래 scheduled)
        else:
            print(f'❌ FAIL: {m_id.group(1)} next_run이 과거')
```

### 2. Orphan Script Detection

```bash
# cron이 참조하는 script 목록
hermes cron list > /tmp/cron_list.txt
grep -oE 'Script:\s+\S+\.(py|sh)' /tmp/cron_list.txt | awk '{print $2}' | sort -u > /tmp/cron_scripts.txt

# 디렉토리 전체 script
ls ~/.hermes/scripts/ > /tmp/all_scripts.txt

# diff
comm -23 /tmp/all_scripts.txt /tmp/cron_scripts.txt  # orphan 후보

# 각 orphan 후보 cross-reference
for s in $(comm -23 /tmp/all_scripts.txt /tmp/cron_scripts.txt); do
  grep -rln "$s" ~/.hermes/skills/ 2>/dev/null | head -3
done
```

### 3. WAL Checkpoint

```bash
sqlite3 ~/.hermes/state.db "PRAGMA wal_checkpoint(TRUNCATE)"
# 활성 DB 안전, 즉시 효과
```

## ⚠️ Pitfall

1. **state.db vacuum은 효과 미미** (이미 압축됨). WAL checkpoint가 효과적.
2. **state-snapshots 압축 시 gzip만** (원본 삭제 전 검증 필수 — `zcat state.db.gz | sqlite3 ... ".tables"` 가능 확인).
3. **브라우저 캐시 (camoufox/puppeteer/playwright)는 사용 중일 수 있음** → 자동 정리 금지.
4. **cron 등록 후 24시간 이내**는 NEVER 정상. 즉시 고장 close 금지.
5. **orphan script 삭제 전** 반드시 grep으로 wiki/skills/.local/bin/ cross-reference.
6. **memory_query.py supersede memory_lazy_fetch.py** 시 — 30분 이내에 사용자가 호출한 적 없는지 확인 후 삭제.

## 📌 영구화 결정

- `cb2ee5fafc5d` memory daily auto-compact cron (매일 06:30 KST, 사용자 룰: 90%)
- `memory_query.py` skill (21 keys → wiki lazy fetch)
- disk cleanup 패턴은 다음 audit Step 1에 추가

## 🔗 Cross-ref

- `hermes-ecosystem-audit` SKILL.md §Disk + Cron + Script Cleanup Patterns
- `self-improvement-loop` SKILL.md §🆕 Idle-time 자율 hygiene 워크플로우
- `memory-query` skill (Tool-as-Memory)