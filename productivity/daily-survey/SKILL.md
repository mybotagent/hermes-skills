---
name: daily-survey
description: Hermes 내장 clarify 툴(버튼)로 매일 아침 생활습관 설문 진행
category: productivity
---

# Daily Survey (일일 생활습관 체크리스트)

## ⚡ 중요: 모드 구분 (HARD RULE)

이 스킬은 **실행 컨텍스트에 따라 동작이 완전히 다름**:

| 모드 | 실행자 | 할 일 | clarify 사용? |
|------|--------|-------|:---:|
| **크론 모드** | cron job (유저 없음) | 리마인더 텍스트 전송만 | **🚫 절대 금지** |
| **인터랙티브 모드** | live session (유저 있음) | clarify로 설문 진행 | ✅ 사용 |

> 🚨 **크론 모드에서 clarify 호출하면 Broken pipe 에러 + 유저 대기 불가로 무조건 실패**
>
> 크론이 이 스킬을 로드했을 때 → 아래 **크론 모드** 섹션만 보고, **인터랙티브 모드** 섹션은 무시할 것.

---

## 🕐 크론 모드 (Cron Job 전용)

크론이 이 스킬을 로드했을 때의 **유일한 임무**: 리마인더 텍스트를 전송하는 것.

**절대 하지 말 것:**
- ❌ `clarify` 툴 호출 (Broken pipe)
- ❌ CSV 파일 읽기/쓰기 (크론 작업 아님)
- ❌ 설문 직접 실행
- ❌ `send_message` 툴 호출 (응답 텍스트가 자동 전송됨)
- ❌ **크론 skills 배열에 이 스킬 유지** (프롬프트가 자급자족형이면 skills에서 제거하는 것이 더 안전함 — 인터랙티브 지침이 에이전트를 혼란시켜 Broken pipe 유발 가능)

**할 일 (단순 텍스트 응답):**
1. 아래 아침 템플릿 메시지를 그대로 출력
2. 끝

### 🌅 아침 템플릿
```
🌅 굿모닝! 오늘 아침 생활습관 체크 시간입니다.

수면/운동/감정/신체/수분 — 5문항 준비되어 있어요.

시작하시려면 "ㅇ"이라고 입력해주세요. (또는 "시작")
```

---

## 💬 인터랙티브 모드 (Live Session 전용)

유저(live session)가 **"ㅇ"** 또는 **"시작"** 이라고 응답했을 때만 실행. 아침에 5문항을 **한번에** 모두 진행한다 (AM/PM 분할 금지).

### 설문 문항 — 2가지 타입

| 타입 | 항목 | 설문 방식 |
|------|------|----------|
| **달성형** | 수면, 운동, 수분 | ✅/❌ (달성/미달) |
| **점수형** | 감정, 신체 | 좋음/보통/나쁨 |

### 아침 5문항 (전체)

| # | 항목 | 타입 | 질문 | clarify choices |
|---|------|:----:|------|-----------------|
| 1 | 😴 수면 | 달성형 | 어젯밤 수면 시간은? | `["7시간 이상 (충분)","5~7시간 (보통)","3~5시간 (부족)","3시간 미만 (매우 부족)"]` |
| 2 | 🏃 운동 | 달성형 | 오늘 운동했나요? | `["했음","안함"]` |
| 3 | 😊 감정 | 점수형 | 오늘 감정 상태는? | `["좋음 (Good)","보통 (Neutral)","나쁨 (Bad)"]` |
| 4 | 💪 신체 | 점수형 | 오늘 신체 컨디션은? | `["좋음 (Good)","보통 (Neutral)","나쁨 (Bad)"]` |
| 5 | 💧 수분 | 달성형 | 물 1L 이상 드셨나요? | `["1L 이상","1L 미만"]` |

### 실행 순서

1. 유저가 "ㅇ" 또는 "시작" 입력 → 5문항 **순차적으로** `clarify` 툴 호출
   - 질문 텍스트에 진행상황 표시 (예: "1/5 💊 ...")
2. 각 항목 응답 수집 후 `~/.hermes/survey/log.csv` 에 append
   - 수면 매핑: "7시간 이상 (충분)"→yes, "5~7시간 (보통)"→yes, "3~5시간 (부족)"→no, "3시간 미만 (매우 부족)"→no
3. 완료 메시지 전송

### CSV 로깅

```csv
date,time,exercise,sleep,mood,physical,water
2026-06-17,09:22,yes,yes,neutral,good,yes
```

- **7개 필드**: date, time, exercise, sleep, mood, physical, water
- sleep = yes(충분) / no(부족)
- mood = good / neutral / bad
- physical = good / neutral / bad
- exercise, water = yes / no
- **trailing comma 금지**: 빈 값은 그냥 생략 (예: `2026-06-13,06:11,,,yes,,`)

---

## 📊 시각화 (이미지 생성)

### 히트맵 (GitHub README 자동 갱신) — **2026-07-05 신규**

`~/.hermes/survey/gen_heatmap.py` — 5 metric × N days 히트맵 PNG 생성.

- **출력**: `~/.hermes/survey/heatmap_latest.png` (~33KB, 947×490)
- **자동 push**: `~/.hermes/scripts/sync_survey_repo.sh` → `~/daily-survey/heatmap.png`
- **GitHub**: `https://github.com/mybotagent/daily-survey/blob/main/heatmap.png`
- **README 렌더링**: `![Survey Heatmap](heatmap.png)` — GitHub에서 바로 보임
- **색상**: 🟢 달성/좋음 · 🟡 보통 · 🔴 미달/나쁨 · ⚪ 데이터 없음
- **셀 라벨**: 달성형=OK/NO, 점수형=G/N/B

### 달성률 카드 (기존)

설문 데이터 요청 시 `python3 ~/.hermes/survey/gen_stats.py` 실행:

1. **달성률 카드** (`stats_v8.png`): 세로 1열, 2가지 타입 구분:

| 타입 | 표시 방식 | 예시 |
|------|----------|------|
| **달성형** (수면/운동/수분) | OK(달성) / NO(미달) | `OK3  NO1` |
| **점수형** (감정/신체) | G(좋음) / N(보통) / B(나쁨) | `G2  N2  B1` |

**레이아웃**: 라벨 | 분수+% (48px) | 세부내역(OK/G/N/B) | 퍼센트바 | %수치
**색상**: 🟢≥70% 🟡40~69% 🔴<40%

### 시각화 주의사항
| 하지 말 것 | 이유 → 대체 |
|-----------|-------------|
| 이모지(✅❌😊) 사용 | CJK 폰트 미지원 → 네모 깨짐 → `OK/NO/G/N/B` 텍스트 사용 |
| Chromium headless screenshot | snap 샌드박스 Permission denied → matplotlib 직접 사용 |

### 생성 스크립트
- `~/.hermes/survey/gen_stats.py` — 최종 시각화 스크립트 (matplotlib)
- 전송: `send_message(message=f"MEDIA:/path/to/img.png\n\n캡션", target=...)`

## 📦 데이터 저장소

모든 설문 데이터는 `mybotagent/daily-survey` (private)에서 관리:
- **log.csv** — 원본 데이터
- **scripts/analysis.ipynb** — Jupyter 노트북 (전체 통계 시각화, GitHub에서 자동 랜더링)
- **동기화 cron:** `survey-repo-sync` (fe96a2422b91) — 매일 12:00 KST 자동 push

## ⚠️ 피해야 할 것 (수정 이력)

- **clarify open-ended 금지**: 각 문항은 반드시 `choices`(버튼)로 제시할 것. `question`만 넣고 `choices`를 생략하는 open-ended(텍스트 직접입력) 방식 금지. 사용자는 버튼 클릭만으로 답변하기를 기대함. (`choices` 배열은 skill의 문항 테이블에 명시되어 있음)
- **AM/PM 분할 금지**: 과거 AM=수면만, PM=5문항으로 분할했으나 -> 아침에 한번에 5문항으로 통일
- **meds(복약)/diet(식사) 제거**: 2026-06-17에 water(수분)로 교체. 앞으로 복약/식사 질문 금지
- **수면 질문 방식**: "12시 전 취침 + 7h15m" 기준에서 "수면시간 선택형"으로 변경
- **CSV 7필드**: 이전 8필드(date,time,meds,exercise,sleep,mood,physical,diet) → 7필드로 축소

## 🛠️ Cron Sync Script 패턴 (PNG 자동 갱신)

`~/.hermes/scripts/sync_survey_repo.sh` 표준 구조 — **데이터 + 시각화 + push**를 한 번에:

```bash
#!/usr/bin/env bash
# sync_survey_repo.sh — Push survey data + heatmap PNG to GitHub repo
set -e

SRC="$HOME/.hermes/survey/log.csv"
DST="$HOME/daily-survey/log.csv"
HEATMAP_SRC="$HOME/.hermes/survey/heatmap_latest.png"
HEATMAP_DST="$HOME/daily-survey/heatmap.png"
GEN_SCRIPT="$HOME/.hermes/survey/gen_heatmap.py"

# 1. Copy latest CSV
cp "$SRC" "$DST"

# 2. Regenerate PNG from latest CSV
python3 "$GEN_SCRIPT"

# 3. Copy PNG to repo (overwrite atomically)
cp "$HEATMAP_SRC" "$HEATMAP_DST"

cd "$HOME/daily-survey"

# 4. Silent if nothing changed (cron no-op)
if git diff --quiet; then
    echo "No changes to survey repo"
    exit 0
fi

# 5. Commit + push
git add log.csv heatmap.png
git commit -m "update: survey data + heatmap $(date '+%Y-%m-%d')"
git push origin main
echo "Pushed survey update + heatmap: $(date '+%Y-%m-%d %H:%M')"
```

**설계 원칙:**
- **no_agent 모드** (cron `no_agent: true`) — 스크립트 stdout이 그대로 전송됨. LLM 호출 없음 → 토큰 0
- **변경 감지 시에만 push** — `git diff --quiet` 체크 → 같은 데이터면 push 안 함 (GitHub 노이즈 감소)
- **CSV와 PNG 동시 commit** — 둘 다 같은 트랜잭션으로 묶어서 일관성 유지
- **deterministic PNG** — matplotlib는 같은 데이터로 항상 같은 PNG 생성 → PNG 변경 = 데이터 변경 신호

### Push 후 검증 (수동 or 별도 cron)

자동 push 직후, 첫 1회는 수동으로 검증해볼 것 (이후 cron 믿어도 됨):

```bash
# 1. 로컬과 원격 SHA 일치 확인
cd ~/daily-survey && git ls-remote origin main
# Expected: local SHA == remote SHA

# 2. PNG 헤더 검증 (실제 이미지로 디코드 가능한지)
file heatmap.png
# Expected: "PNG image data, W x H, 8-bit/color RGBA, non-interlaced"

# 3. README가 PNG를 참조하는지 확인
grep -n 'heatmap' README.md
# Expected: ![Survey Heatmap](heatmap.png) line found
```

더 정밀한 검증 (private repo raw fetch, byte-for-byte diff 등)은 `github-private-repo-access` 스킬의 `references/verify-after-push.md` 참고.

### Common Pitfall: README는 push 안 됨

PNG만 push하고 README는 그대로 두면, README의 `![heatmap](heatmap.png)` 참조가 깨질 위험. **README도 함께 갱신 + commit + push 해야 함.** 또는 README를 PNG 경로와 무관하게 generic (`heatmap.png`)으로 작성해두면 PNG 교체만으로도 동작.
