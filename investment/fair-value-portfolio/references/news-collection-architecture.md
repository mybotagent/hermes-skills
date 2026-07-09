# 뉴스 수집 아키텍처 (2026-06-07)

## 데이터 소스

| 시장 | 출처 | 구현 | 상태 |
|:----|:----|:-----|:----:|
| 🇺🇸 미국 | Finnhub API | `collect_macro_context.py` → `fetch_finnhub_news()` | ✅ 무료 티어 일 300회 |
| 🇰🇷 한국 | 네이버 증권 (BeautifulSoup) | `collect_macro_context.py` → `fetch_naver_news()` | ✅ 서버사이드 렌더링 페이지 스크래핑 |

## 실행 위치

- `~/trading-agents-nuri/src/collect_macro_context.py`
- 18:35 파이프라인 Phase 0.5에서 subprocess로 호출됨
- 18:30 LLM 매크로 크론이 저장한 `macro_context.json`을 읽고, 필터 통과 종목의 뉴스를 추가로 수집하여 병합

## 흐름

```
18:30 LLM 크론 → web_search → macro_context.json (매크로 데이터 + 글로벌 뉴스)
                    ↓
18:35 pipeline.py Phase 0.5 → collect_macro_context.py 실행
                    ├── macro_context.json 읽기 (매크로 데이터 보존)
                    ├── filtered_top10.json 읽기 (7종목)
                    ├── Finnhub API 호출 (US 종목만, KR은 스킵)
                    ├── 네이버 증권 스크래핑 (KR 종목만, US는 스킵)
                    └── 병합 저장 → macro_context.json (뉴스 포함)
                    ↓
                    Phase 2 LangGraph → 각 Agent가 macro_context.stocks[].news 활용
```

## 코드 구조

```python
def fetch_finnhub_news(ticker: str) -> list[dict]:
    """Finnhub API로 당일 뉴스 3건 수집. Rate limit(429) 감지."""
    
def fetch_naver_news(code: str) -> list[dict]:
    """네이버 증권 메인페이지(main.naver)에서 뉴스 제목 3건 수집.
    EUC-KR 디코딩 + BeautifulSoup 파싱.
    news_news.naver 페이지는 JS렌더링이라 미작동 — main.naver 사용."""

def main():
    # 1. macro_context.json 읽기 (18:30 LLM 크론 출력)
    # 2. filtered_top10.json or daily_snapshot.json에서 종목 리스트 읽기
    # 3. 각 종목별 뉴스 수집 (US=Finnhub, KR=Naver)
    # 4. 병합 저장
```

## 주의사항

- **Finnhub rate limit**: 429 응답 시 빈 배열 반환 (retry 없음)
- **네이버 인코딩**: EUC-KR, BeautifulSoup 필수
- **한국주 Finnhub 미지원**: Finnhub은 한국 주식 뉴스를 제공하지 않으므로 의도적으로 KR_TICKERS 스킵
- **18:30 매크로 크론 미실행 시**: macro_context.json이 없으면 collect_macro_context.py가 빈 컨텍스트로 Finnhub 뉴스만 수집
