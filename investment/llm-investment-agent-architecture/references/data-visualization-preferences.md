# Data Visualization Preferences — Investment Portfolio Charts

> Absorbed from standalone `data-visualization` skill (2026-06-28).

## 🎨 Style Preferences (HARD RULES)

| 속성 | 규칙 |
|------|------|
| 배경 | `#0d1117` (GitHub Dark) |
| 테마 | GitHub Contributions 스타일 |
| 출력 형식 | **PNG 이미지** (matplotlib). 절대 text/ASCII/HTML로 출력 금지 |
| 폰트 | WenQuanYi Zen Hei (`/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc`) |
| 폰트 크기 | **크게** — 레이블 16pt+, 숫자 64pt (stats 카드), 제목 36pt |
| 텍스트 | **최소화** — 불필요한 범례/설명 제거. 숫자/심볼 위주 |
| 색상 팔레트 | 초록 `#3fb950`(양호) / 노랑 `#d29922`(보통) / 빨강 `#f85149`(미흡) / 회색 `#8b949e`(메타) |

## 📐 레이아웃 원칙

1. **분할 전송**: 하나에 다 담지 말고 2~3개 이미지로 나눠서 전송
   - 히트맵(트렌드) + 숫자 카드(통계) 분리
2. **화면 꽉 채우기**: 이미지 크기는 12×10 inch 이상, 여백 최소화
3. **숫자 우선**: 달성률/통계는 "2/3" 같은 분수 형태로, 64px 폰트
4. **심볼 축약** (공간 절약):
   - G=양호(good) N=보통(neutral) B=미흡(bad)
   - Y=달성(yes) N=미달(no)
   - ·=데이터없음

## 📦 구현 (matplotlib)

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

CJK_FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
cjk = FontProperties(fname=CJK_FONT, size=<n>)

fig = plt.figure(figsize=(12, 10))
fig.patch.set_facecolor('#0d1117')
ax = fig.add_subplot()
ax.set_facecolor('#0d1117')

plt.savefig('/tmp/chart.png', dpi=150, bbox_inches='tight',
            facecolor='#0d1117', edgecolor='none')
plt.close()
```

## 🚚 전송

```python
send_message(
    message=f"MEDIA:/tmp/chart.png\\n\\n제목 텍스트",
    target="discord:채널 / 토픽 id"
)
```

MEDIA: 경로를 메시지에 포함하면 Discord에 이미지가 첨부됨.

## 🔧 한글 폰트 문제

```python
# 사용 가능한 CJK 폰트 확인
fc-list :lang=ko
# 설치:
# sudo apt install fonts-wqy-zenhei  # WenQuanYi
# sudo apt install fonts-noto-cjk    # Noto Sans CJK
```

matplotlib에 한글 폰트가 없으면 `UserWarning: Glyph XXXX missing from font(s) DejaVu Sans` 발생. 반드시 CJK 폰트 지정.

## 🚫 안티패턴

- ❌ 텍스트/ASCII 테이블로 데이터 출력 (가독성 나쁨)
- ❌ HTML 파일 생성 (사용자가 직접 열어야 함)
- ❌ emoji를 matplotlib 레이블에 사용 (Glyph missing 경고)
- ❌ 데이터가 적은데 30일 히트맵 생성 (빈 칸だらけ → 무의미)
- ❌ 작은 폰트 (12pt 이하) — 사용자가 항상 "글씨가 너무 작다"고 불평
