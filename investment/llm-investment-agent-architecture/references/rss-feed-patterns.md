# Google News RSS Feed Search Patterns

> 매크로 리포트 데이터 수집용. `web_search` 도구가 없을 때 terminal() + curl로 사용.

## URL Template
```
https://news.google.com/rss/search?q={URL_ENCODED_KEYWORD}&hl=en-US&gl=US&ceid=US:en
```

## Extract Command
```bash
curl -s "URL" 2>/dev/null | grep -oP '<title>.*?</title>' | head -20
```

처음 2개 타이틀은 항상(`"검색어 - Google News"`, `"Google News"`) 이므로 실제 뉴스는 3번째부터.

---

## 1순위: 반도체·AI (4개 병렬)

### 반도체 업종 전반
```
q=semiconductor+2026+June
q=NVIDIA+TSM+AMD+chip+stock+June+2026
```

### HBM / 메모리
```
q=HBM+DDR5+memory+pricing+2026
q=HBM4+SK+Hynix+Samsung+memory+2026
```

### AI CapEx
```
q=NVIDIA+AI+CapEx+spending+2026
q=Broadcom+AVGO+earnings+June+2026
```

### 반도체 매도/조정
```
q=US+stock+market+semiconductor+selloff+June+5+6+2026
q=Nasdaq+semiconductor+selloff+June+5+2026
```

---

## 2순위: 통화정책 (3개 병렬)

### Fed
```
q=Federal+Reserve+interest+rate+June+2026
q=Kevin+Warsh+Fed+chair+interest+rate+June+2026
```

### 고용/물가
```
q=US+employment+payrolls+May+2026+172000
q=10+year+Treasury+yield+June+2026
```

### ECB / BOJ
```
q=ECB+interest+rate+decision+June+2026
```

---

## 3순위: 지정학 (3개 병렬)

### 미중 갈등 / 관세
```
q=US+China+trade+tariffs+2026
q=Trump+tariffs+forced+labor+2026+60+countries
```

### 이란 / 중동
```
q=Iran+war+oil+Strait+of+Hormuz+June+2026
q=oil+prices+June+2026+OPEC+Iran
```

---

## 4순위: 한국 시장

```
q=KOSPI+foreign+selloff+semiconductor+June+2026
q=USD+KRW+exchange+rate+won+dollar+June+2026
q=SK+Hynix+stock+price+June+5+6+2026
q=COMPUTEX+2026+Jensen+Huang+Lisa+Su+semiconductor
```

---

## 병렬 실행 예시 (4 parallel searches)

```bash
# terminal 4개를 동시에 호출 (timeout=15)
# 각각의 결과에서 <title> 태그 추출
# 흥미로운 기사가 발견되면 추가 검색
```

> ⚠️ **주의**: `delegate_task`로 이 검색들을 위임하지 말 것 — 서브 에이전트가 검색을 실제로 실행하지 않고 계획만 설명하는 경우가 확인됨. 반드시 직접 `terminal()` 호출로 실행할 것.

---

## ⚠️ Pitfalls

### 한글 검색어 400 Error

Google News RSS는 URL에 **한글(hangeul) 문자가 포함되면 HTTP 400(Bad Request)을 반환**한다.
URL 인코딩(percent-encoding)을 해도 실패하는 경우가 있음 → **영문 키워드로만 검색**해야 한다.

| 의도한 검색어 | 대체 영문 키워드 | 결과 |
|:------------|:---------------|:----:|
| `삼성전자 증권 뉴스` | `Samsung+Electronics+stock+news+June+2026` | ✅ 정상 |
| `SK하이닉스 증권 뉴스` | `SK+Hynix+stock+news+June+2026` | ✅ 정상 |
| `에이피알 증권 뉴스` | `APR+Corp+cosmetic+stock+Korea+2026` 또는 `APR+278470+stock` | ✅ 정상 |
| `원/달러 환율` | `USD+KRW+exchange+rate+won+dollar+June+2026` | ✅ 정상 |

**규칙**: Google News RSS에서 한국 종목 뉴스를 검색할 때는 종목코드(005930) 또는 영문 회사명 + "stock" + 시점을 사용. `hl=ko&gl=KR&ceid=KR:ko` 파라미터도 400 Error 가능성이 있으므로 기본 `hl=en-US&gl=US&ceid=US:en` 사용.

### RSS 타이틀만으로는 정확한 수치 추출 어려움

RSS는 `<title>`만 반환하므로 정확한 지표값(WTI exact price, DXY level, 10Y yield)을 알기 어렵다.
제목에서 숫자를 추론하거나, 추가 검색으로 보도 기사 URL을 열어서 확인하는 것이 좋다.

**해결법**: 흥미로운 제목이 보이면 추가 curl 검색으로 더 구체적인 키워드 재검색:
```bash
# 더 구체적인 키워드로 재검색 (수치 포함)
curl -s "https://news.google.com/rss/search?q=WTI+crude+oil+97+dollar+June+2026&hl=en-US&gl=US&ceid=US:en" 2>/dev/null | grep -oP '<title>.*?</title>' | head -5
```
