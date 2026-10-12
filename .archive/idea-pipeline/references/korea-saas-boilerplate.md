# 한국형 SaaS 보일러플레이트 도메인 (8모듈)

## 시장 갭 (2026-07-04 확인)

GH `ai saas boilerplate` 검색 = 472,700건 (글로벌 폭증)
한국형 풀스택 (`kakao+naver+toss` 통합) = **0건**

→ 1인 개발자가 매번 "결제 + 로그인 + 장바구니 + 세금 + 분석" 5종 인프라를 한글로 다시 만듦

## 8모듈 표준

### 1. 결제 (필수)
- **토스페이먼츠 v2** — https://docs.tosspayments.com/
- **카카오페이 API** — https://developers.kakao.com/docs/latest/ko/kakaopay
- **네이버페이 API** — https://developer.pay.naver.com/
- 통합 어댑터 패턴: provider enum + common interface

### 2. 인증 (필수)
- **카카오 OAuth** — developers.kakao.com (JavaScript SDK)
- **네이버 OAuth** — developers.naver.com (JavaScript SDK)
- **이메일 fallback** — magic link or password
- Supabase Auth / NextAuth 양쪽 다 통합 필요 (글로벌 솔루션 미흡)

### 3. 장바구니 (선택)
- 옵션/수량/재고 관리
- 한국형 옵션 패턴: 옵션상품/추가옵션/묶음 할인
- 비동기 재고 차감 (Supabase realtime)

### 4. 세금/세무 (필수)
- **홈택스 세금계산서** API or 스마일신세무/링크허브 연동
- 부가세 자동 계산 (PG 매출 기준)
- 사업자등록번호 검증 (국세청 API)

### 5. 데이터 분석 자동화 (필수)
- PG webhook 자동 수집 (3종 통합)
- 일별/월별 매출 집계 cron
- 대시보드: 매출 / 환불 / VAT / 코호트 / LTV
- Next.js + Recharts/Visx
- 글로벌 대안: Plausible/PostHog — 한국 PG 통합 ❌

### 6. 배포 (필수)
- Vercel 한국 리전 or AWS Seoul
- 도메인/SSL 자동 (Cloudflare or Let's Encrypt)

### 7. UI 키트 (필수)
- 한국형 디자인 토큰 (Pretendard / IBM Plex Sans KR)
- 다크모드 + 한글 typography
- 한국 결제 버튼 스타일 (카카오 노란색 / 네이버 초록 / 토스 파란색)

### 8. AI 코어 (선택)
- Claude API + LangGraph
- 한국어 프롬프트 템플릿

## 도메인 비범위

- ❌ 글로벌 SaaS 보일러플레이트와 경쟁
- ❌ Stripe 단독 결제 (한국 시장 한정)
- ❌ 영어 UI / 영문 마케팅 / 영문 글로벌 배포
- ❌ 한국형 결제·세무 인프라 자체 개발 (기존 SDK/API 활용만)

## 수익 모델

| 가격대 | 타겟 |
|---|---|
| ₩299,000 1회 | 1인 SaaS 개발자, MVP 단계 |
| ₩899,000 1회 | 1인 SaaS 개발자, 프로덕트 단계 |
| ₩1,290,000 1회 | 1인 SaaS 개발자, 멀티 제품 |
| ₩29,000/월 구독 | 업데이트 + 신규 PG 통합 |
| ₩39,000/월 구독 | 분석 자동화 + 우선 지원 |

## GH 검색 검증

```bash
# 한국형 풀스택 0건 확인
curl -sL "https://api.github.com/search/repositories?q=kakao+naver+toss+language:typescript&sort=stars" \
  | python3 -c "import json,sys; print(f'결과: {json.load(sys.stdin)[\"total_count\"]}건')"

# 글로벌 SaaS 보일러플레이트 다수 확인
curl -sL "https://api.github.com/search/repositories?q=ai+saas+boilerplate+language:typescript&sort=stars&per_page=5" \
  | python3 -c "import json,sys; [print(f'⭐ {r[\"stargazers_count\"]:5d} | {r[\"full_name\"]}') for r in json.load(sys.stdin).get('items',[])]"
```

## 작성일

2026-07-04