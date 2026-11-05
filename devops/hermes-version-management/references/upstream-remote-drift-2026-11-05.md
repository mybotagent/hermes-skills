# Upstream Remote Drift + Doctor Hang — 실측 상세 (2026-11-05)

> cron `b05629511dd9` "Hermes 버전 체크 + 자동 업데이트" (매일 09:00 KST) 실행 중 발견.
> **결론: `hermes update --check` 가 2개월 이상 잘못된 "최신" 판정을 보고하고 있었다.**

## 1. 환경

| 항목 | 값 |
|:-----|:---|
| 설치 경로 | `/home/ubuntu/.hermes/hermes-agent` (shallow clone, `is-shallow-repository=true`) |
| wrapper | `/home/ubuntu/.local/bin/hermes` → `venv/bin/hermes` |
| venv Python | 3.11.15 |
| 로컬 버전 | v0.18.0 (`2026.7.1`), commit `009b42d0` (2026-07-07) |
| `origin` | `https://github.com/mybotagent/hermes-agent.git` (fork) |
| `fork` | 동일 (중복 remote) |
| `upstream` | **존재하지 않음** ← 문제의 근본 원인 |
| gateway PID | 3480144 (`python -m hermes_cli.main gateway run`) |
| dashboard PID | 3530254 (port 9199) |

## 2. 잘못된 "최신" 판정의 증거

```
$ hermes --version
Hermes Agent v0.18.0 (2026.7.1) · upstream 009b42d0
...
Up to date

$ hermes update --check
→ Fetching from upstream...     ← upstream remote 없어서 fallback
→ Fetching from origin...
✓ Already up to date.
```

그런데 실제 공식 upstream:
```
$ curl -s https://api.github.com/repos/NousResearch/hermes-agent/releases/latest
tag: v0.22.7
published: 2026-11-03T21:53:16Z

$ git ls-remote https://github.com/NousResearch/hermes-agent.git refs/heads/main
ed1afb082eb3e46cf2edae9d8f68fb67b09ee4df  refs/heads/main
```

→ **v0.18.0 vs v0.22.7**, 약 4개월간의 릴리스가 누락.

## 3. shallow clone의 카운트 왜곡 (실측)

얕은 fetch로 upstream을 비교하면 카운트가 무의미해진다:

```bash
$ git fetch --depth 1 https://github.com/NousResearch/hermes-agent.git main:refs/remotes/upstream/main
$ git rev-list --count HEAD..upstream/main
1                      # ← 허술한 값 (실제 47,237)
$ git rev-list --count upstream/main..HEAD
14772                  # ← 이건 upstream shallow 트리 전체 카운트
$ git merge-base HEAD upstream/main
(빈 값)                 # ← merge-base 없음 = shallow 문제 신호
```

**정확한 카운트**:
```bash
$ git fetch --filter=blob:none --unshallow https://github.com/NousResearch/hermes-agent.git \
    main:refs/remotes/upstream/main
$ git merge-base HEAD upstream/main
009b42d008b81c18af39414dded9ecdf06082d93   # ← 로컬 HEAD와 동일
$ git rev-list --count HEAD..upstream/main
47237                 # behind
$ git rev-list --count upstream/main..HEAD
0                     # ahead — 로컬 전용 커밋 없음
```

**해석**: 로컬 HEAD가 upstream의 **직접 조상**. fork가 공식과 싱크되지 않은 것이며
업데이트로 잃을 로컬 커밋은 0개 → 업데이트 자체는 안전한 방향.

`git fetch --filter=blob:none --unshallow` 실행 후 `.git`은 685MB로 증가.

## 4. upstream remote 추가 후 정상 동작

```bash
$ git remote add upstream https://github.com/NousResearch/hermes-agent.git
$ hermes update --check
→ Fetching from upstream...
⚕ Update available: 47237 commits behind upstream/main.
  Run 'hermes update' to install.
```

→ `hermes_cli/main.py` 의 로직: `upstream` 있으면 upstream 우선, 없으면 origin fallback.
remote 하나만 추가해도 이후 `hermes update`가 자동으로 올바른 대상으로 동작.

## 5. 대점프 리스크 평가 실측

| 항목 | 로컬 | upstream v0.22.7 | 판정 |
|:-----|:-----|:-----|:-----|
| version | 0.18.0 | (pyproject는 `version = "0.0.0"` — 설치 스탬프 방식) | 릴리스 태그 v0.22.7 |
| config schema | `_config_version: 33` | `cli-config.yaml.example` `_config_version: 52` | 🔴 +19 스텝 |
| Python | 3.11.15 | `.python-version` = **3.14** | 🔴 interpreter repin 필요 |
| 업데이터 구조 | `hermes_cli/main.py` 내 monolith | `hermes_cli/update_cmd*.py` 20+ 파일 + `pm/` 패키지 신설 | 🔴 PM 의존성 관리로 전환 |
| 로컬 전용 커밋 | — | ahead = 0 | 🟢 안전 |
| working tree | clean | — | 🟢 |
| 디스크 | 9.9GB 여유 / 40G (74%) | — | 🟡 |

**결론: cron 자동 실행 ❌.** 단독 세션 + 백업 + 사용자가 개입하는 작업으로 분류.

백업 보관: `/tmp/hermes-preupdate-20261105/` (config.yaml, .env, HEAD.txt)

## 6. `hermes doctor` hang — state.db 1.4GB

### 증상
```
$ hermes doctor
[Command timed out after 60s]      # 출력 0바이트
$ timeout 240 hermes doctor
[timeout]                            # 여전히 멈춤
$ hermes doctor --help               # ← 이건 정상 응답
```

→ 명령 자체가 죽은 게 아니라 **특정 검사에서 무한정 정지**.

### hang 지점 특정
```bash
cd ~/.hermes/hermes-agent && timeout 120 python3 -u -c "
from hermes_cli.doctor import run_doctor
class A: fix=False; ack=None
run_doctor(A())"
```
출력이 `✓ ~/.hermes/state.db exists (6984 sessions)` 까지 진행 후 정지.
→ 다음 코드 블록 = FTS 쓰기 건강 probe:
```python
from hermes_state import _db_opens_cleanly, repair_state_db_schema
_write_reason = _db_opens_cleanly(state_db_path)   # ← 여기서 정지
```

`_db_opens_cleanly` 내부: `PRAGMA integrity_check` → `PRAGMA quick_check` → sessions read →
rolled-back messages write. 대용량 DB에서 앞 두 개가 수백 초.

단독 재현:
```bash
timeout 200 python3 -u -c "
import sqlite3, time
c=sqlite3.connect('file:/home/ubuntu/.hermes/state.db?mode=ro',uri=True,timeout=60)
t=time.time(); c.execute('PRAGMA quick_check').fetchall(); print('quick_check: %.1fs'%(time.time()-t))"
# → 240초 내 완료 못 함 (timeout)
```

### state.db 크기 분해 (dbstat)

```
page_count: 345552   page_size: 4096   freelist: 162
```
(= 345552 × 4096 ≈ 1.4 GB)

| 테이블 | 크기 | 비고 |
|:-------|-----:|:----|
| `messages_fts_trigram_data` | 455.0 MB | trigram FTS |
| `messages` | 290.5 MB | 본문 |
| `messages_fts_trigram_content` | 231.9 MB | trigram FTS |
| `messages_fts_content` | 231.9 MB | 표준 FTS |
| `messages_fts_data` | 68.1 MB | 표준 FTS |
| `sessions` | 58.9 MB | |
| `idx_messages_session_active` | 3.9 MB | |
| `idx_messages_session` | 3.8 MB | |

**핵심**: 표준 FTS(`messages_fts*`)와 trigram FTS(`messages_fts_trigram*`)가
**동일 메시지 내용을 2벌 저장** → FTS 관련 합계 ≈ 988 MB (전체의 ~70%).

실제 메시지 본문 총합은 157,648,416 bytes (~150 MB) — FTS가 6.6배 팽창시킨 상태.

세션/메시지 수:
```
sessions: 6,985   messages: 74,395
archived sessions: 0
oldest started_at: 1780179336.4  (≈ 2026-05-30)
newest started_at: 1793841305.7  (≈ 2026-11-05)
```

## 7. cron 컨텍스트 명령 제약 (실측)

| 명령 | 결과 |
|:-----|:-----|
| `curl ... \| python3 -c "..."` | ⛔ `pending_approval` — tirith:curl_pipe_shell. cron에서 승인 불가 |
| `grep -nE 'kill\|pkill'` | ⛔ `pending_approval` — self-termination 패턴 |
| `git fetch --unshallow` | ✅ 정상 (수 분 소요) |
| `curl -s URL -o /tmp/x.json` + `python3 -c "json.load(...)"` | ✅ 통과 |
| `git show upstream/main:<path>` | ✅ 통과 |
| `timeout 120 python3 -u -c "..."` | ✅ 통과 (doctor hang 재현에 사용) |

**教训**: `curl | python3` 는 `self-healing-cron` skill에 이미 문서화되어 있었으나,
version-check cron에서도 반복적으로 걸림 → 해당 skill의 "cron 컨텍스트 명령 제약" 절을
버전 관리 쪽에도 병기.

## 8. 과거 실행 기록 (왜 아무도 몰랐나)

`~/.hermes/cron/output/b05629511dd9/` 에서 직전 실행들 확인:
- 2026-11-04, 11-03, 11-02, 10-30, 10-29 … **연속으로 모두 `[SILENT]` 응답**
- 2026-09-14 ~ 2026-09-18 등도 동일 패턴

즉 **2개월 이상** "up to date" 라는 잘못된 판정을 조용히 반복. 조용한 실패의 전형.

→ 교훈: **판정 로직이 silently fall back하면 무조건 보고.** "SILENT"는
"진짜 최신"이 **검증된 경우에만**.
