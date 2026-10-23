#!/usr/bin/env python3
"""정면 시안 2안(실측 mm) — A: 2자리 축소(여백 10 균일), B: 4자리 00:00(200×80, 여백 10 균일). 슬롯은 geom.slots 그대로."""
import os, sys, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(PROJ, '..', '..', 'tools'))
import geom as G
DIG = G.DIGITS; M = 10.0; H = 80.0
def digit(ax, cx, d):
    for s in G.SEGS:
        on = s in DIG[d]
        for b in G.slots(s, cx):
            x0, z0, x1, z1 = b.bounds
            ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, fc='#ffb300' if on else '#08090a', ec='none'))
def body(ax, W, title):
    ax.add_patch(FancyBboxPatch((-W / 2, 0), W, H, boxstyle='round,pad=0,rounding_size=4', fc='#26292e', ec='#999', lw=1))
    ax.set_title(title, fontsize=9)
def dims(ax, W, ext):
    x0, x1 = ext
    for (a, b, y, t) in [(-W / 2, x0, -5, f'{x0 + W / 2:.1f}'), (x1, W / 2, -5, f'{W / 2 - x1:.1f}')]:
        ax.annotate('', (a, y), (b, y), arrowprops=dict(arrowstyle='<->', lw=0.6, color='#666')); ax.text((a + b) / 2, y - 3.5, t, ha='center', fontsize=6, color='#444')
    ax.annotate('', (x1 + 2, 0), (x1 + 2, 10), arrowprops=dict(arrowstyle='<->', lw=0.6, color='#aaa')); ax.text(x1 + 3, 4, '10', fontsize=6, color='#ccc')
    ax.annotate('', (x1 + 2, 70), (x1 + 2, 80), arrowprops=dict(arrowstyle='<->', lw=0.6, color='#aaa')); ax.text(x1 + 3, 74, '10', fontsize=6, color='#ccc')
    ax.text(0, -14, f'{W:.0f} × {H:.0f} mm', ha='center', fontsize=8)
def finish(ax, W):
    ax.set_xlim(-W / 2 - 6, W / 2 + 14); ax.set_ylim(-18, H + 6); ax.set_aspect('equal'); ax.axis('off')
if __name__ == '__main__':
    plt.rcParams['font.family'] = ['WenQuanYi Zen Hei', 'DejaVu Sans']
    fig, axs = plt.subplots(2, 1, figsize=(10, 8.6), gridspec_kw={'height_ratios': [1, 1]})
    WA = 83.0 + 2 * M; ax = axs[0]; body(ax, WA, 'A안 — 2자리 축소: 숫자 60 × 34(그대로), 여백 위·아래·좌·우 10 → 103 × 80 · "47"')
    digit(ax, -24.5, 4); digit(ax, 24.5, 7); dims(ax, WA, (-41.5, 41.5)); finish(ax, 200.0)
    WB = 200.0; cA, cB = -48.5, 48.5; ax = axs[1]
    body(ax, WB, 'B안 — 4자리 00 : 00 (점수판: 왼쪽·오른쪽 각각 +1 버튼, 리셋 노브 하나) → 200 × 80, 여백 10 · "12 : 07"')
    for c, (t, o) in ((cA, (1, 2)), (cB, (0, 7))): digit(ax, c - 24.5, t); digit(ax, c + 24.5, o)
    for zc in (40 - 11, 40 + 11 - 7.5):
        for k in (0, 1): ax.add_patch(Rectangle((-2.5, zc + k * 5.5), 5, 2, fc='#ffb300', ec='none'))
    dims(ax, WB, (cA - 41.5, cB + 41.5)); finish(ax, WB)
    out = os.path.join(PROJ, 'figures', 'mockup_v2_options.png'); fig.tight_layout(); fig.savefig(out, dpi=150); print(out)
