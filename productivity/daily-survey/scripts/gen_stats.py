#!/usr/bin/env python3
"""Generate stats card — 달성형(yes/no) + 점수형(good/neutral/bad) 구분 (no emoji)

   Output: ~/.hermes/survey/stats_v8.png (달성률 카드)
   Usage:  python3 ~/.hermes/survey/gen_stats.py

   이모지 미사용 (CJK 폰트 WenQuanYi Zen Hei)

   달성형(수면/운동/수분): OK(달성) NO(미달)
   점수형(감정/신체): G(좋음) N(보통) B(나쁨)

   CSV 파싱 주의: 7개 필드 (date,time,exercise,sleep,mood,physical,water)
   trailing comma 금지
"""

import csv
from io import StringIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import os

CJK_FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'

with open(os.path.expanduser('~/.hermes/survey/log.csv')) as f:
    raw = f.read()

reader = csv.DictReader(StringIO(raw))
rows = list(reader)

day_data = {}
for r in rows:
    d = r['date']
    if d not in day_data:
        day_data[d] = {'sleep':None,'exercise':None,'mood':None,'physical':None,'water':None}
    dd = day_data[d]
    t = r['time']
    if t < '12:00' and r.get('sleep') and r['sleep'].strip():
        dd['sleep'] = r['sleep']
    for col in ['exercise','mood','physical','water']:
        if r.get(col) and r[col].strip():
            dd[col] = r[col]

metrics = [
    ('sleep',    '수면', '달성'),
    ('exercise', '운동', '달성'),
    ('mood',     '감정', '점수'),
    ('physical', '신체', '점수'),
    ('water',    '수분', '달성'),
]

results = []
for key, label, mtype in metrics:
    vals = [day_data[d].get(key) for d in sorted(day_data.keys())]
    valid = [v for v in vals if v is not None]
    if not valid:
        results.append((label, '-', 0, 0, mtype, []))
        continue
    n = len(valid)
    if mtype == '달성':
        yes = sum(1 for v in valid if v == 'yes')
        no = n - yes
        pct = int(yes / n * 100)
        results.append((label, f'{yes}/{n}', pct, n, mtype,
                        [('OK', yes, '#3fb950'), ('NO', no, '#f85149')]))
    else:
        good = sum(1 for v in valid if v == 'good')
        neutral = sum(1 for v in valid if v == 'neutral')
        bad = sum(1 for v in valid if v == 'bad')
        achieved = good + neutral
        pct = int(achieved / n * 100)
        results.append((label, f'{achieved}/{n}', pct, n, mtype,
                        [('G', good, '#3fb950'), ('N', neutral, '#d29922'), ('B', bad, '#f85149')]))

def rc(pct):
    return '#3fb950' if pct >= 70 else ('#d29922' if pct >= 40 else '#f85149')

fig, ax = plt.subplots(figsize=(12, 12))
fig.patch.set_facecolor('#0d1117')
ax.set_facecolor('#0d1117')
ax.axis('off')

f_title = FontProperties(fname=CJK_FONT, size=32, weight='bold')
f_label = FontProperties(fname=CJK_FONT, size=22)
f_rate  = FontProperties(fname=CJK_FONT, size=48, weight='bold')
f_pct   = FontProperties(fname=CJK_FONT, size=20, weight='bold')
f_detail_label = FontProperties(fname=CJK_FONT, size=15)
f_detail_num = FontProperties(fname=CJK_FONT, size=24, weight='bold')
f_type   = FontProperties(fname=CJK_FONT, size=12)
f_legend = FontProperties(fname=CJK_FONT, size=13)

ax.text(0.5, 0.96, 'Survey Stats', fontsize=32, color='#f0f6fc',
        fontproperties=f_title, ha='center', transform=ax.transAxes)

row_ys = [0.80, 0.65, 0.50, 0.35, 0.20]

for idx, (label, rate_str, pct, n, mtype, details) in enumerate(results):
    y = row_ys[idx]
    color = rc(pct)
    ax.text(0.06, y, label, fontsize=22, color='#8b949e',
            fontproperties=f_label, ha='left', va='center', transform=ax.transAxes)
    badge_x = 0.06 + 0.05
    badge_color = '#1c2128'
    bw, bh = 0.055, 0.03
    ax.add_patch(plt.Rectangle((badge_x, y-bh/2), bw, bh, facecolor=badge_color, edgecolor='none', transform=ax.transAxes, clip_on=False))
    ax.text(badge_x + bw/2, y, '달성' if mtype == '달성' else '점수',
            fontsize=11, color='#8b949e', fontproperties=f_type, ha='center', va='center', transform=ax.transAxes)
    ax.text(0.32, y, rate_str, fontsize=48, color=color,
            fontproperties=f_rate, ha='center', va='center', transform=ax.transAxes)
    dx = 0.52
    for sym, count, c in details:
        ax.text(dx, y, f'{sym}', fontsize=15, color=c,
                fontproperties=f_detail_label, ha='center', va='center', transform=ax.transAxes)
        ax.text(dx + 0.025, y, f'{count}', fontsize=24, color=c,
                fontproperties=f_detail_num, ha='left', va='center', transform=ax.transAxes)
        dx += 0.07
    bar_x = 0.70; bar_w = 0.22; bar_h = 0.022
    ax.add_patch(plt.Rectangle((bar_x, y-bar_h/2), bar_w, bar_h, facecolor='#21262d', edgecolor='none', transform=ax.transAxes, clip_on=False))
    if pct > 0:
        fill_w = bar_w * pct / 100
        ax.add_patch(plt.Rectangle((bar_x, y-bar_h/2), fill_w, bar_h, facecolor=color, edgecolor='none', transform=ax.transAxes, clip_on=False))
    ax.text(bar_x + bar_w + 0.025, y, f'{pct}%', fontsize=18, color=color,
            fontproperties=f_pct, ha='left', va='center', transform=ax.transAxes)

ax.text(0.5, 0.05,
        '달성형(OK/NO)  점수형(G=좋음/N=보통/B=나쁨)',
        fontsize=13, color='#484f58', fontproperties=f_legend, ha='center', transform=ax.transAxes)

path = os.path.expanduser('~/.hermes/survey/stats_v8.png')
os.makedirs(os.path.dirname(path), exist_ok=True)
plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0d1117', edgecolor='none')
plt.close(fig)
print(f"SAVED: {path}")
