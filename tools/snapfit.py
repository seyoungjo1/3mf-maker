#!/usr/bin/env python3
"""캔틸레버 스냅핏(걸쇠·클립) 계산기 — 사출 설계 표준식(BASF/Bayer snap-fit 매뉴얼, Machine Design 1990 McMaster-Lee).
  변형률  ε = 1.5·t·Y / (L²·Q)
  팁 힘   P = b·t²·E·ε / (6·L·Q)          (= 3EIY/(L³Q), I=b t³/12)
  삽입력  W = P·(μ + tanα) / (1 − μ·tanα)   (α: 리드각 — 분리력은 리턴각으로)
  토크    T = P·r                             (r: 회전축~접촉점 거리, 경첩형 걸쇠)
PLA(FDM): E ≈ 3.0~3.5 GPa, 허용 변형률 — 1회성 4~8 %, 반복 사용 2~4 %, Z방향(층 가로지름) 적층이면 ×0.5.
Q(변형 확대계수, 뿌리가 유연할 때): 1.0(강체 벽) ~ 2.0+(얇은 판 위). 뿌리 조건을 모르면 1.5 로 둔다.
사용: python snapfit.py --L 22 --t 4.5 --b 5 --Y 1.0 [--E 3300] [--Q 1.5] [--mu 0.3] [--lead 30] [--return 60] [--r 22]
"""
import argparse, math
def calc(L, t, b, Y, E=3300.0, Q=1.5, mu=0.3, lead=30.0, ret=90.0, r=None, allow=0.04):
    eps = 1.5 * t * Y / (L * L * Q)
    P = b * t * t * E * eps / (6 * L * Q)                   # N  (E in MPa, mm → N)
    def mating(a):
        ta = math.tan(math.radians(a)); d = 1 - mu * ta
        return float('inf') if d <= 0 else P * (mu + ta) / d
    out = dict(strain=eps, strain_pct=eps * 100, allow_pct=allow * 100, ok=eps <= allow, tip_force_N=P,
               insert_force_N=mating(lead), release_force_N=mating(ret), Ymax_mm=allow * L * L * Q / (1.5 * t))
    if r: out['torque_Nmm'] = P * r
    return out
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--L', type=float, required=True); ap.add_argument('--t', type=float, required=True)
    ap.add_argument('--b', type=float, required=True); ap.add_argument('--Y', type=float, required=True); ap.add_argument('--E', type=float, default=3300)
    ap.add_argument('--Q', type=float, default=1.5); ap.add_argument('--mu', type=float, default=0.3); ap.add_argument('--lead', type=float, default=30)
    ap.add_argument('--return', dest='ret', type=float, default=90); ap.add_argument('--r', type=float); ap.add_argument('--allow', type=float, default=0.04)
    a = ap.parse_args(); o = calc(a.L, a.t, a.b, a.Y, a.E, a.Q, a.mu, a.lead, a.ret, a.r, a.allow)
    for k, v in o.items(): print(f'{k:16s} {v:.3f}' if isinstance(v, float) else f'{k:16s} {v}')
