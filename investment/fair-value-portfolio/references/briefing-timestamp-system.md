# Briefing 시스템 — Timestamp, Market Status, Cron Timing

> `collect_stock_briefings.sh` + `collect_briefings.py` 조합.
> 대시보드 표시: 오늘 브리핑만 표시, stale 데이터 금지, 시간 표시, 시장 상태 표시.

## Timestamp 파이프라인

1. **브리핑 생성** (08:10 KST): Discord cron output 파일명에 시간 포함 → `2026-07-17_08-22-43.md`
2. **collect_stock_briefings.sh**: cron output 파일명 `_08-22-43`에서 `08:22` 추출 → `.md` 파일 하단에 `⏱️ 생성: 2026-07-17 08:22 KST` 푸터 추가
3. **collect_briefings.py**: `load_briefing()`에서 `⏱️ 생성:` 푸터 정규식으로 시간 추출

### 시간 추출 정규식 (`collect_briefings.py`)
```python
# 1순위: collect_stock_briefings.sh가 추가한 푸터
time_m = re.search(r'⏱️\s*생성:\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s*KST', text)

# 2순위: 원본 cron output 파일명 (YYYY-MM-DD_HH-MM-SS.md) — 과거 포맷
# 3순위: 문서 내 HH:MM KST 패턴
# 4순위: fallback — 빈 문자열
```

### collect_stock_briefings.sh 수정 (2026-07-17)

`extract_report()`가 `tmp_file` → `mv → target_file` 한 후, target 파일 하단에 timestamp 추가:
```bash
cron_base=$(basename "$latest")
time_part=$(echo "$cron_base" | sed -n 's/^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}_\([0-9]\{2\}\)-\([0-9]\{2\}\)-.*/\1:\2/p')
if [ -n "$time_part" ]; then
    echo "" >> "$target_file"
    echo "---" >> "$target_file"
    echo "⏱️ 생성: $date_str $time_part KST" >> "$target_file"
    echo "---" >> "$target_file"
fi
```

## Cron Timing — 생성 전에 수집 금지

**문제**: collect_stock_briefings.sh(08:15)가 브리핑 cron(08:10, ~08:22 소요)보다 먼저 실행 → 변경 감지 실패.

**해결**: collect cron을 08:50으로 지연:
```
schedule: "50 8 * * 1-5"  # 08:10 briefing → 08:50 collect (40분 버퍼)
```

오후도 동일: 18:00 briefing → 18:40 collect (40분 버퍼) — 현재는 18:40으로 설정되어 있음.

## Market Status — 대시보드 표시

JS 코드 (portfolio_dashboard.html, metric cards 직후):

```javascript
var now=new Date();
var kst=new Date(now.toLocaleString('en-US',{timeZone:'Asia/Seoul'}));
var kstH=kst.getHours(),kstD=kst.getDay();
var isWeekend=kstD===0||kstD===6;
var usOpen=!isWeekend&&(kstH>=23||kstH<6);     // US장: 23:30~06:00 KST
var krOpen=!isWeekend&&kstH>=9&&kstH<15;       // KR장: 09:00~15:30 KST
var usStatus=isWeekend?'휴장':(usOpen?'⚡ 장중':'장마감');
var krStatus=isWeekend?'휴장':(krOpen?'⚡ 장중':'장마감');
document.getElementById('sub').innerHTML+='| 🇺🇸 '+usStatus+' | 🇰🇷 '+krStatus+' | 요일';
```

## 주의사항

1. **collect_briefings.py는 오늘 날짜만 로드**: stale 어제 브리핑 노출 금지. 오늘 브리핑 없으면 `note` 필드 반환.
2. **Vercel 강제 배포**: 파일 내용이 동일하면 `git commit`이 안 됨. `date +%s > .force`로 강제 갱신.
3. **git push 충돌**: `hermes-stock-briefings` 리포가 rebase 필요 시 `git pull --rebase`로 해결.
4. **JS try/catch 중첩 주의**: 기존 try/catch 체인에 새 `try{...}`를 삽입할 때 catch가 어느 try에 속하는지 반드시 확인. 매크로 try catch가 브리핑 try를 잡아먹는 버그 발생 (2026-07-17).
