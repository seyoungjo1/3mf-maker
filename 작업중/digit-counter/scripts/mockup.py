#!/usr/bin/env python3
"""정면 시안(실측 mm) — 슬롯형 기계식 7세그먼트 2자리. 모든 요소는 mm 좌표 도형."""
import os, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon, Circle
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE)
W, H = 200.0, 80.0                      # 정면
DH, DW, T = 60.0, 34.0, 8.0             # 숫자 높이·폭·세그먼트 굵기
PITCH, SLOT = 4.0, 2.0                  # 슬롯 피치·슬롯 높이(셔터 행정 = SLOT)
CX = {'tens': -22.0, 'ones': 22.0}      # 숫자 중심 x (정면 중심 0)
SEG = {0: 'abcdef', 1: 'bc', 2: 'abged', 3: 'abgcd', 4: 'fgbc', 5: 'afgcd', 6: 'afgedc', 7: 'abc', 8: 'abcdefg', 9: 'abcdfg'}

def seg_poly(s, cx):
    """세그먼트 윤곽(끝 45° 깎음) — 가로 a g d, 세로 b c e f."""
    h, w, t = DH / 2, DW / 2, T; c = t / 2
    if s in 'agd':
        y = {'a': h - c, 'g': 0.0, 'd': -h + c}[s]; x0, x1 = cx - w + t * 0.6, cx + w - t * 0.6
        return [(x0, y), (x0 + c, y + c), (x1 - c, y + c), (x1, y), (x1 - c, y - c), (x0 + c, y - c)]
    x = cx + (w - c if s in 'bc' else -w + c); y0, y1 = (t * 0.6, h - t * 0.6) if s in 'bf' else (-h + t * 0.6, -t * 0.6)
    return [(x, y0), (x + c, y0 + c), (x + c, y1 - c), (x, y1), (x - c, y1 - c), (x - c, y0 + c)]

def draw(ax, value, title):
    ax.add_patch(FancyBboxPatch((-W / 2, -H / 2), W, H, boxstyle='round,pad=0,rounding_size=6', fc='#26292e', ec='#888', lw=1))
    for k, cx in CX.items():
        d = value // 10 if k == 'tens' else value % 10
        for s in 'abcdefg':
            on = s in SEG[d]; P = seg_poly(s, cx)
            ax.add_patch(Polygon(P, closed=True, fc='#111316', ec='#555', lw=0.4))
            ys = [p[1] for p in P]; xs = [p[0] for p in P]
            y = min(ys) + 0.5
            while y + SLOT <= max(ys) - 0.5:       # 슬롯(가로 틈) — 켜짐이면 색, 꺼짐이면 검정 홈
                ax.add_patch(Rectangle((min(xs) + 1.2, y), max(xs) - min(xs) - 2.4, SLOT, fc='#ffb300' if on else '#08090a', ec='none'))
                y += PITCH
            ax.add_patch(Polygon(P, closed=True, fc='none', ec='#666', lw=0.5))
    ax.add_patch(Rectangle((62, -H / 2 + 6), 30, 7, fc='none', ec='#666', lw=0.6, ls='--'))
    ax.text(77, -H / 2 + 9.5, '윗면: +1 버튼', color='#bbb', ha='center', va='center', fontsize=6)
    ax.text(W / 2 - 2, 0, '오른쪽 옆면:\n리셋 노브', color='#bbb', ha='right', va='center', fontsize=6)
    ax.set_xlim(-W / 2 - 4, W / 2 + 4); ax.set_ylim(-H / 2 - 4, H / 2 + 4); ax.set_aspect('equal'); ax.axis('off'); ax.set_title(title, fontsize=9)

if __name__ == '__main__':
    plt.rcParams['font.family'] = ['WenQuanYi Zen Hei', 'DejaVu Sans']
    fig, axs = plt.subplots(2, 1, figsize=(9, 8.2), facecolor='white')
    draw(axs[0], 47, f'정면 200 × 80 mm — "47" (숫자 {DH:.0f} × {DW:.0f}, 세그먼트 굵기 {T:.0f}, 슬롯 {SLOT:.0f}/피치 {PITCH:.0f}, 숫자 간격 {CX["ones"]-CX["tens"]-DW:.0f})')
    draw(axs[1], 80, '"80" — 셔터가 2 mm 올라가면 슬롯에 색 줄, 내려오면 검정 (세그먼트마다 위/아래 두 상태)')
    os.makedirs(os.path.join(PROJ, 'figures'), exist_ok=True)
    out = os.path.join(PROJ, 'figures', 'mockup_front.png'); fig.tight_layout(); fig.savefig(out, dpi=150); print(out)
