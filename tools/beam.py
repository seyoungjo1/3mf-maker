#!/usr/bin/env python3
"""보 처짐·응력 계산기(직사각 단면). 손잡이·다리·암·선반의 휨 확인용 (SKILL 4절).
  캔틸레버(끝 하중)   δ = P L³ / (3 E I),  σ = P L c / I
  단순지지(가운데)    δ = P L³ / (48 E I), σ = P L c / (4 I)
  양단고정(가운데)    δ = P L³ / (192 E I), σ = P L c / (8 I)
  I = b h³ / 12, c = h/2.  PLA E ≈ 3300 MPa, 인장 강도 ≈ 50 MPa(층 방향 가로지르면 ×0.5) → 허용 응력 ≈ 25 MPa(안전율 2).
사용: python tools/beam.py --mode cantilever|simple|fixed --L 76 --b 12.7 --h 9 --P 20 [--E 3300] [--allow 25]
"""
import argparse
K = {'cantilever': (3.0, 1.0), 'simple': (48.0, 0.25), 'fixed': (192.0, 0.125)}
def calc(mode, L, b, h, P, E=3300.0, allow=25.0):
    kd, km = K[mode]; I = b * h ** 3 / 12.0; c = h / 2.0
    defl = P * L ** 3 / (kd * E * I); M = km * P * L; sigma = M * c / I
    return dict(I_mm4=I, deflection_mm=defl, moment_Nmm=M, stress_MPa=sigma, allow_MPa=allow, ok=sigma <= allow,
                stiffness_N_per_mm=P / defl if defl else float('inf'))
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--mode', choices=list(K), default='cantilever')
    for k in ('L', 'b', 'h', 'P'): ap.add_argument('--' + k, type=float, required=True)
    ap.add_argument('--E', type=float, default=3300); ap.add_argument('--allow', type=float, default=25)
    a = ap.parse_args(); o = calc(a.mode, a.L, a.b, a.h, a.P, a.E, a.allow)
    for k, v in o.items(): print(f'{k:20s} {v:.3f}' if isinstance(v, float) else f'{k:20s} {v}')
