# Python DRY_RUN 파싱 — 안전 패턴 + 로그 라벨 함정

> 출처: 2026-07-08 — `hermes_disk_hygiene.py` (cron `0e095c406dae`) 작성 중 두 번 hit 한 함정.
> Python cron script 의 DRY-first 모드 결정 시 필수 참조.

## 1. ❌ 깨지기 쉬운 패턴

```python
DRY_RUN = os.environ.get("DRY_RUN", "1") == "0"
```

**왜 깨지나** (실측 3가지):

1. **`.env` 에 `DRY_RUN=` (빈 문자열)**: bash `set -a; source .env` 로 자동 export → `"1" == "0"` False → **의도와 다른 production mode** 로 진입. `.env` 의 trailing 빈 줄 / `unset` 흔적에서 자주 발생.
2. **bash `DRY_RUN=1 python3 foo.py`**: env 값은 `"1"` 인데 코드는 False (== 비교로 inverted). 코드는 DRY-first 의도인데 호출 컨텍스트에 따라 production 으로 동작.
3. **`DRY_RUN=0` 명시 시**: True 반환 (일치) — 이 경우만 의도대로. **직관과 반대** — env "0" 넣으면 True, env "1" 넣으면 False. 코드 리뷰 시 위험.

## 2. ✅ 안전 패턴 (단일공식)

```python
DRY_RUN = os.environ.get("DRY_RUN", "1") not in ("0", "false", "False", "")
```

**왜 안전한가**:
- env 미설정 / `"1"` / `"true"` / `""` / `"false"` 외 → True (dry safe)
- env `"0"` 또는 `"false"` (대소문자 둘 다) → False (production)
- bash 컨텍스트 (`.env` 자동 source, manual `VAR=val`) 모두 직관대로 동작
- **빈 문자열도 dry** (default 와 일치)

## 3. ❌ 로그 라벨 함정 (DRY-first 분석 망가뜨림)

```python
log(f"DRY_RUN={int(DRY_RUN)}")
# DRY 모드일 때 (True) → "DRY_RUN=1" 출력
# PROD 모드일 때 (False) → "DRY_RUN=0" 출력
# → cron 로그 분석 시 "DRY_RUN=1" 보면 production 으로 오해
# → 역설적으로 "DRY_RUN=1" 은 사실 DRY 모드. 의미가 거꾸로.
```

**실측** (2026-07-08 17:14 UTC, `hermes_disk_hygiene.py` 처음 실행):
```
DRY_RUN=1    ← DRY 모드인데 1 출력 → 혼란
DRY_RUN=0    ← PROD 모드인데 0 출력 → 혼란
```

## 4. ✅ 사람이 읽을 수 있는 라벨

```python
log(f"mode={'DRY' if DRY_RUN else 'PROD'}")
# DRY 모드 → "mode=DRY"
# PROD 모드 → "mode=PROD"
# → cron 로그 grep 한 줄로 모드 확인 가능
```

## 5. Bash wrapper 에서 DRY_RUN 전달 시 패턴

`set -uo pipefail` (not -e) 환경에서:

```bash
#!/usr/bin/env bash
# default DRY, 사용자가 명시적으로 DRY_RUN=0 으로 호출 시 PROD
: "${DRY_RUN:=1}"   # "" or unset → 1 (dry safe)

# python 호출 (env 그대로 inherit)
DRY_RUN="$DRY_RUN" python3 ~/.hermes/scripts/hermes_disk_hygiene.py
```

**함정**: bash `: "${DRY_RUN:=1}"` 는 `set -u` 환경에서 unset 변수만 채움 — env 에 `DRY_RUN=""` 가 있으면 이미 설정된 것으로 보고 덮어쓰지 않음. Python 의 `os.environ.get("DRY_RUN", "1") not in ("0", "false", "False", "")` 가 더 견고 (위 §2 패턴 권장).

## 6. Cron 등록 시 DRY-first 명시

```bash
hermes cron create "50 21 * * *" "...prompt..." \
  --name "🧹 disk hygiene watchdog" \
  --script hermes_disk_hygiene.py \
  --deliver local
# prompt 안에서 DRY_RUN=0 명시 ❌ — 사용자가 confirm 전까지는 절대 안 됨
# default DRY_RUN=1 / True 상태로 cron 등록, 사용자 "prod 켜" 한마디 후 update
```

## 7. 실측 baseline — `hermes_disk_hygiene.py` (cron `0e095c406dae`)

| Mode | env | Python DRY_RUN | 로그 라벨 | 동작 |
|---|---|---|---|---|
| DRY (default) | (unset) | True | `mode=DRY` | 측정 + stdout, mutation 0 |
| DRY (bash export) | `DRY_RUN=1` | True | `mode=DRY` | 동일 |
| PROD (명시) | `DRY_RUN=0` | False | `mode=PROD` | tier별 safe-cleanup 실행 |

→ 사용자가 cron update 또는 manual `DRY_RUN=0 python3 ...` 로만 PROD 진입 가능.

## 8. 안티패턴 추가

| ❌ Anti-pattern | ✅ Fix |
|---|---|
| `DRY_RUN = os.environ.get("DRY_RUN", "1") == "0"` | `DRY_RUN = os.environ.get("DRY_RUN", "1") not in ("0", "false", "False", "")` |
| `log(f"DRY_RUN={int(DRY_RUN)}")` | `log(f"mode={'DRY' if DRY_RUN else 'PROD'}")` |
| `bash : "${DRY_RUN:=1}"` 로 env 에 `DRY_RUN=` 빈 문자열 덮어쓰기 | Python `not in (...)` 패턴이 bash 환경 흡수 |
| cron prompt 안에서 `DRY_RUN=0` 명시 | default dry 등록 → 사용자 confirm 후 `cronjob update` |

## 9. 이 패턴이 적용된 shipped cron

- `0e095c406dae` disk hygiene watchdog (2026-07-08)
- `91059d1e3d31` hermes-config-sync (2026-07-07, bash 기반이지만 같은 DRY-first 정책 적용)

→ 다음에 다른 Python cron script 작성 시 본 패턴 1:1 복사 권장.