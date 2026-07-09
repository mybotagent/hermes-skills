---
name: skill-dynamic-selection
description: "프로필 기반 스킬 동적 선택 — Phase ②. 태스크에 맞는 스킬만 로드하여 토큰 효율화."
version: 1.1.0
author: 채니봇
tags: [hermes, skills, profile, dynamic-selection]
---

# Skill Dynamic Selection — Phase ②

## 개요

5개 프로필 중 현재 태스크에 맞는 프로필의 스킬만 로드. 불필요한 스킬 제외 → 토큰 절약 + 노이즈 감소.

회의 (2026-06-28→29): aiprofit + 채니봇 + plannerbot 합의.
Linear: SHO-21 (Phase ① 완료), SHO-24 (Phase ② 진행중)

## Phase ① 검증 (2026-06-29) ✅

모든 명령어 정상 동작 확인:

| 명령어 | 상태 | 비고 |
|--------|------|------|
| `active` | ✅ | 현재: 개발(8개 스킬) |
| `switch <프로필>` | ✅ | 개발↔투자 전환 확인 |
| `skills` | ✅ | 현재 프로필 스킬 리스트 출력 |
| `log` | ✅ | 전환 이력 2건 기록됨 |
| `analyze` | ✅ | "투자" 추천 (히스토리 기반) |
| `mix 개발 투자` | ✅ | 혼합 프로필 11개 스킬 로드 |
| `suggested 투자` | ✅ | preload 문자열 출력 |

### Phase ① → Phase ② 갭 분석
- analyze가 transition history만 보는데, 실제 세션 컨텍스트(최근 메시지/도구) 분석은 미구현
- mix 프로필 동작하나 unload 로직 없음 (수동 전환 시 이전 프로필 스킬이 남아있을 수 있음)
- Phase ① 기능(수동 전환)은 완전함. Phase ② 자동화는 analyze 고도화 필요.

## 프로필 목록 (Phase ②)

| 프로필 | 스킬 수 | 사용처 |
|--------|---------|--------|
| 🛠️ 개발 | 8 | 코드 작업, PR 리뷰, 리팩토링 |
| 📊 투자 | 3 | 주식 분석, 포트폴리오 리서치 |
| 📋 회의 | 6 | PM, Kanban, 일정 관리 |
| 🔬 연구 | 6 | 웹 리서치, 문서 조사 |
| ⚙️ 운영 | 7 | 인프라, 크론, 에러 대응 |

## Phase ② 핵심 개선

### 1. 태스크 컨텍스트 기반 자동 프로필 추천
- 현재 세션의 메시지/도구 사용 패턴 분석 → 적합 프로필 자동 추천 (TODO: 현재는 transition history 기반)
- `skill_profile.py analyze` 명령어로 세션 컨텍스트 분석

### 2. 스킬 로드 최적화
- 불필요한 스킬 제외 → 입력 토큰 30~50% 절약
- 프로필 전환 시 이전 프로필 스킬 언로드 (TODO: mix 사용 시 unload 확인 필요)

### 3. 혼합 프로필 (Multi-profile)
- 2개 이상 프로필이 동시에 필요한 복합 태스크 지원
- 예: "투자 리서치 중 발견한 종목 코드 분석" → 📊투자 + 🛠️개발

### 4. 전환 로그 기반 학습
- `~/.hermes/profile_transitions.jsonl` 데이터 → Phase ③ LLM 자동 라우터 학습

## 모델 다양화 현황 (2026-06-29)

Insights(30일): model diversity = ZERO. DeepSeek-v4-flash만 95/96 세션 사용.

**DeepSeek 내 테스트 완료 (4개):**
- `deepseek-v4-flash` — 기본
- `deepseek-v4-pro` — ✅ 응답 정상
- `deepseek-chat` (V3) — ✅ 응답 정상
- `deepseek-reasoner` (R1) — ✅ 응답 정상

**Five-Model Flight: 4/5** (1개 더 필요)
**Provider Polyglot: 1/2** (다른 provider API key 필요)

**Unlock 조건:** .env에 추가 provider 키 등록 필요
- OpenRouter (OPENROUTER_API_KEY) — 추천, 100+ 모델
- Gemini (GOOGLE_API_KEY) — 무료 티어
- nous — OAuth 로그인

## 사용법

### 현재 프로필 확인
```
python3 ~/.hermes/scripts/skill_profile.py active
```

### 프로필 전환
```
python3 ~/.hermes/scripts/skill_profile.py switch <프로필명>
```

### 태스크 분석 → 프로필 추천
```
python3 ~/.hermes/scripts/skill_profile.py analyze
```

### 현재 프로필의 스킬 리스트
```
python3 ~/.hermes/scripts/skill_profile.py skills
```

### 전환 기록 확인
```
python3 ~/.hermes/scripts/skill_profile.py log
```

### 혼합 프로필 활성화
```
python3 ~/.hermes/scripts/skill_profile.py mix 개발 투자
```

### CLI: 스킬 preload 문자열
```
python3 ~/.hermes/scripts/skill_profile.py suggested <프로필명>
# → "writing-plans,test-driven-development,github-pr-workflow,..."
```
CLI에서: `hermes -s "$(python3 ~/.hermes/scripts/skill_profile.py suggested 개발)"`

## Phase ③ 로드맵 (별도 회의)
- LLM 자동 라우터: 전환 로그 학습 → 컨텍스트 기반 자동 프로필 전환
- 사용자 피드백 루프: "이 프로필이 맞나요?" → 학습 데이터 축적
- 크론 태스크 프로필 사전 할당

## 전환 로그

`~/.hermes/profile_transitions.jsonl` 에 자동 기록. Phase ③(LLM 자동 라우터) 학습 데이터로 사용.
