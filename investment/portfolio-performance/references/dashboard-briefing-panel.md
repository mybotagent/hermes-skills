# Dashboard Briefing Panel — collect_briefings.py + Markdown Table Rendering

> Added 2026-07-17 — 오전(08:10) + 오후(18:00) 브리핑을 대시보드에 동일 표시
> Updated 2026-07-17 — today-only rule, collapsible UX, note handler

## 개요

Discord cron으로 발송되는 시황 브리핑을 대시보드에서도 동일하게 표시.
`collect_briefings.py`가 `~/hermes-stock-briefings/YYYY-MM-DD/*.md`를 읽어 `today_briefings.json` 생성.
Dashboard JS가 fetch → HTML 렌더링.

## 데이터 흐름

```
~/hermes-stock-briefings/2026-07-16/
├── 01-오전-포트폴리오-브리핑.md     ← 08:15 KST
├── 02-미국-증시-브리핑.md           ← 18:40 KST
├── 03-매크로-전략-리포트.md          ← 18:40 KST
└── 04-LangGraph-파이프라인.md        ← 18:50 KST
        ↓
collect_briefings.py
        ↓
data/today_briefings.json            ← 대시보드가 fetch
        ↓
portfolio_dashboard.html             ← #briefingSection에 렌더링
```

## collect_briefings.py

### 핵심 규칙: 오늘 날짜만 (2026-07-17)

**절대 가장 최근 날짜를 찾지 않음**. 오늘 날짜 디렉토리가 없으면 `note` 반환:

```python
def collect() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    result = {"date": today, "periods": [], "note": "오늘 브리핑이 아직 생성되지 않았습니다"}
    today_dir = os.path.join(BRIEFINGS_REPO, today)
    if os.path.isdir(today_dir):
        periods = []
        for fname, label in NAME_MAP.items():
            b = load_briefing(today_dir, fname)
            if b: periods.append(b)
        if periods:
            result = {"date": today, "periods": periods, "count": len(periods)}
    # 항상 OUTPUT에 저장 (note 포함)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result
```

### 마크다운 → JSON 변환

```python
# ## 헤더별 섹션 분리
def extract_sections(md_text: str) -> list[dict]:
    md_text = md_text.strip()  # ← 필수: 첫 줄이 \n## 이면 빈 문자열 생성
    parts = re.split(r'\n(?=## )', md_text)
    for part in parts:
        m = re.match(r'^## (.+)', part)
        title = m.group(1).strip() if m else "General"
        content = re.sub(r'^## [^\n]+\n?', '', part).strip()
        sections.append({"title": title, "content": content})
```

### NAME_MAP key 주의

`NAME_MAP` 키는 **확장자 없음** (`"01-오전-포트폴리오-브리핑"`).
`load_briefing()`에서 자동 `.md` 추가.

### 시간 추출

```python
# 2026-07-16 (목) 18:00 KST → date+time 추출
time_m = re.search(r'(\d{4}-\d{2}-\d{2})\s+\(\w+\)\s+(\d{2}):(\d{2})\s*KST', text)
if time_m:
    time_str = f"{time_m.group(3)}:{time_m.group(4)}"
else:
    time_m2 = re.search(r'(\d{2}):(\d{2})\s*KST', text)
    time_str = time_m2.group(0) if time_m2 else ""
```

### today_briefings.json 구조 (note 버전)

브리핑이 없을 때:
```json
{"date": "2026-07-17", "periods": [], "note": "오늘 브리핑이 아직 생성되지 않았습니다"}
```

브리핑이 있을 때:
```json
{
  "date": "2026-07-16",
  "periods": [
    {
      "filename": "01-오전-포트폴리오-브리핑.md",
      "label": "오전 포트폴리오 브리핑",
      "time": "08:15",
      "sections": [...],
      "full_text": "\\n## 1. 😶 ...\\n\\n| 순위 | 종목 | ... |\\n..."
    }
  ],
  "count": 4
}
```

## 대시보드 JS — Briefing Section

### Note 핸들러 (2026-07-17)

```javascript
try {
  var br = await(await fetch('today_briefings.json?'+Date.now())).json();
  if (br.note) {
    // 브리핑 없음 → 노트 메시지만 표시
    document.getElementById('briefingSection').innerHTML = '...'+br.note+'...';
  } else if (br.periods && br.periods.length) {
    // 정상 브리핑 렌더링
    renderBriefings(br);
  }
} catch(e) { console.log('briefing:', e.message); }
```

### 접이식 UX (2026-07-17)

```html
<details open style="padding:0 12px;cursor:pointer">
  <summary style="list-style:none;display:flex;gap:6px">
    <span>☀️</span> 오전 포트폴리오 브리핑 <span style="font-size:9px;color:var(--muted-soft)">08:15</span>
    <span style="margin-left:auto" class="bft">접기</span>
  </summary>
  <div style="padding:2px 0 12px;border-top:1px solid var(--hairline)">
    ... content ...
  </div>
</details>
```

CSS:
```css
.bft { font-size: 9px; color: var(--muted-soft); }
details[open] .bft { color: var(--primary); }
details summary::-webkit-details-marker { display: none; }
details summary::marker { display: none; }
```

동적 텍스트 변경:
```javascript
document.querySelectorAll('#briefingSection details').forEach(function(d) {
  d.addEventListener('toggle', function() {
    var s = this.querySelector('.bft');
    if (s) s.textContent = this.open ? '접기' : '펼치기';
  });
});
```

- 오전(첫번째) = 기본 `open` → "접기"
- 나머지 = 기본 `closed` → "펼치기"

### 마크다운 → HTML 변환 체인 (순서 중요)

```javascript
fullText=fullText.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); // 1. HTML escape
fullText=fullText.replace(/---+/g,'<hr ...>');                                      // 2. horizontal rules
fullText=fullText.replace(/^#### (.+)$/gm,'...');                                   // 3. h4
fullText=fullText.replace(/^### (.+)$/gm,'...');                                    // 4. h3
fullText=fullText.replace(/^## (.+)$/gm,'...');                                     // 5. h2
fullText=fullText.replace(/\*\*(.+?)\*\*/g,'<b>$1</b>');                            // 6. **bold**
fullText=fullText.replace(/^- (.+)$/gm,'...');                                      // 7. - bullet
fullText=fullText.replace(/^(\|.+\|[\n\r]*)+/gm, function(tbl){...});               // 8. MARKDOWN TABLES
fullText=fullText.replace(/\n{2,}/g,'\n');                                          // 9. collapse newlines
```

### Markdown Table → HTML Table 변환

**알고리즘**:
1. 연속 `|...|` 라인 감지: `/^(\|.+\|[\n\r]*)+/gm`
2. separator 행 찾기: `/^\|[\s:-]+\|/`
3. separator 전 = `<thead><th>`, 후 = `<tbody><td>`
4. `split('|').filter(c => c.trim())` — 첫/마지막 empty cell 제거

**<thead> 닫힘 주의**:
```javascript
// ❌ <th>...</th></thead> — 닫힘 태그 누락 금지
return '<table>' + hcells.map(c => '<th>'+c.trim()+'</th>').join('')
     + '</thead><tbody>' + drows.map(...) + '</tbody></table>';

// ✅ 명시적 <tr> 사용 (브라우저 호환성↑)
return '<table><thead><tr>' + hcells.map(c => '<th>'+c.trim()+'</th>').join('')
     + '</tr></thead><tbody>' + drows.map(...) + '</tbody></table>';
```

**첫 번째 셀 스타일**: `color: var(--primary)` + `white-space: nowrap` (순위/종목명)
**헤더 <th>**: `border-bottom: 2px solid var(--primary)`로 강조

## 함정

### 1. 🔴 NAME_MAP vs 실제 파일명 불일치
`NAME_MAP` 키에 `.md` 없음 → `load_briefing()`에서 자동 `.md` 추가 필요.

### 2. 🔴 빈 sections (extract_sections 실패)
`md_text.strip()` 누락 → `re.split(r'\n(?=## )')`이 빈 문자열 생성.

### 3. 🔴 마크다운 표 깨짐 (2026-07-17)
`fullText.replace(/\|(.+)\|/g, ...)`가 모든 `|...|` span 처리.
→ 연속 `|...|` 라인을 `<table><th><td>`로 변환.

### 4. 🔴 오늘 날짜만 표시 (2026-07-17)
`collect_briefings.py`는 **가장 최근 날짜가 아닌 오늘 날짜만** 검색.
오늘 브리핑이 없으면 stale 데이터 금지 → `note` 필드 반환.

### 5. 🔴 접이식 UX — 동적 텍스트 (2026-07-17)
`summary` 기본 삼각형 마커 숨김(`list-style:none`).
`.bft` 텍스트로 "접기"/"펼치기" 동적 변경 (`toggle` 이벤트).
첫번째 브리핑만 `open`, 나머지는 `closed`.

### 6. 🔴 <thead> 닫힘 보장 (2026-07-17)
`'</thead>'` 태그 누락 시 브라우저에서 표 깨짐.
명시적 `<tr>`로 감싸기: `<thead><tr><th>...</th></tr></thead>`.

### 7. 🔴 .gitignore: data/*.json
`trade-pipeline/.gitignore`가 `data/*.json` 무시 → Vercel 레포로 복사.

### 8. 🔴 JS 문법 검증 (patch 후 필수)
매 patch 후 parens/braces diff 0 확인. `</catch` 문자열 있으면 수정 필요.
