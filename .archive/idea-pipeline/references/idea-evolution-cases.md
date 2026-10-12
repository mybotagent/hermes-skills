# Idea Evolution 사례집 (2026-07-04)

## 사례 1: v1→v2→v3 빠른 진화 (같은 날)

**트리거**: 사용자가 같은 자리에서 컨셉을 3번 변경.

```
사용자: "지금 기획안 던져봐 하나"
→ v1 작성 (글로벌 Micro-SaaS 가격실험)

사용자: "카카페이나 네이버페이가 연결되어야함"
→ v2 (한국형 SaaS 보일러플레이트, 토스 추가)

사용자: "글로벌 말고 한국형 saas 구축"
→ v3 (글로벌 ❌, 한국형 ✅, 8모듈 풀스택)
```

**처리**: 매번 `pending/2026-07-04-now.md` 파일 **덮어쓰기** + 본문 v 표시.

## 사례 2: 잘못된 파일 명시적 제거

**트리거**: 사용자가 짧은 시간에 컨셉을 여러 번 바꾼 후 "잘못 만든 파일 모두 제거하고" 지시.

```
2026-07-04 시퀀스:
  v1 (글로벌) → v2 (한국형) ✅ 승인 → v3 (글로벌❌, 한국형✅) → v4 (마크 저커버거) → v5 (FastCampus) → v6 (코드패스트/미트루)

  사용자: "잘못 만든 파일 모두 제거하고"
  
  처리:
    rm pending/2026-07-04.md           # v1
    rm pending/2026-07-04-now2.md      # B2B 미들웨어
    rm pending/2026-07-04-now3.md      # Mark DSL
    rm pending/2026-07-04-now4.md      # 마크 저커버거
    rm pending/2026-07-04-now5.md      # FastCampus
    # approved/2026-07-04-now.md 유지 ✅ (사용자가 이미 승인한 것)
```

**교훈**: approved/ 파일은 사용자 명시적 명령 없이 절대 삭제 ❌. pending/에서만 정리.

## 사례 3: 컨셉 반복 변경 패턴

**관찰**: 같은 자리에서 컨셉 3회 변경 (마크 저커버거 → FastCampus → 코드패스트/미트루).

**처리**:
- 매번 새 파일 생성 (덮어쓰기 ❌)
- 사용자가 명시적 "제거" 명령 시에만 일괄 삭제
- 새 컨셉 파일에 차이 표 1개 섹션 포함 (매니페스트 vs 차별점 vs 수익 모델)

## 사례 4: idea_move.sh가 git reset으로 사라진 사건

**증상**: `git reset --hard origin/main` 후 DESIGN.md, README.md, OPERATIONS.md, idea_move.sh 모두 사라짐.

**원인**: 로컬 master에 작업 → origin main과 충돌 → 강제 reset으로 로컬 master의 commit이 사라짐.

**회복**:
1. `write_file`로 모든 파일 재생성
2. `git add -A && git commit && git push origin main`

**예방**: 처음부터 `git checkout -b main`으로 시작.

## 함정 회피 규칙

1. **확인 질문 최소화**: 사용자가 자율모드면 컨셉 변경 시 confirm ❌, 즉시 새 파일 작성
2. **승인 ≠ 새 기획안**: 사용자가 승인해도 기존 기획안과 동일/보강이면 ❌ (P2)
3. **컨셉 단절 명확화**: "X 말고" 패턴 → 새 파일 + 차이 표 + approved/와 비교 표
4. **자율모드 OFF**: 같은 세션에서 좌절 시그널 1회 받으면 그 후엔 결과만 제출 (clarify ❌)
5. **cron prompt에 `{date_kst}`**: 직접 date 계산 ❌ (cron 시스템이 자동 주입)
6. **idea_move.sh 자동 push**: approve/execute 시에만. reject는 push ❌