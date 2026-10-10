#!/usr/bin/env python3
"""원판(디스크) 자석 흡착력·자석 걸이 고정력 계산기 (SKILL 4절 — 힘 계산).
모델: 축 방향으로 균일하게 자화된 원판(자기 표면 전하 ±σ, σ = Br/μ0)을 두꺼운 철판(투자율 ∞) 앞 간격 g 에 둔다
→ 철판 = 거울상 자석(간격 2g, 같은 방향) → 두 원판의 네 면 쌍 사이 쿨롱형 힘을 동축 링-링 식(타원 적분)으로 적분.
  링-링 축 방향 힘:  F = μ0 q1 q2 z / (4π) · (1/2π)∫dφ/(A − B cosφ)^{3/2},  ∫ = 4E(k)/((A−B)√(A+B)),  A = a²+b²+z², B = 2ab, k² = 2B/(A+B)
한계: 이상적인 두꺼운 철판(포화·도장·거칠기 없음) 기준 = 상한. 실제 표면(도장 철판, 니켈 도금, 얇은 판)은 이보다 작다 —
'derate'(기본 0.5)로 낮춘 값을 설계값으로 쓴다. 마주 보는 상대가 자석이면 같은 크기의 자석끼리 끌림 ≈ 같은 식(간격 2g → 실제 면 간격).
걸이 판정: 미끄러짐(전단) = μ·N·F ≥ 하중, 떼어짐(앞으로 젖힘) = 아래 모서리 피벗 기준 모멘트(하중 × 앞 돌출 ≤ F 합 × 자석 높이).
사용: python tools/magnet.py --d 20 --t 1 --br 1.17 --gaps 0 0.1 0.5 1.0 --n 3 --load_g 150 --lever 30 --arm 45
"""
import argparse, math, numpy as np
from scipy.special import ellipe
MU0 = 4e-7 * math.pi
GRADES = {'N35': 1.17, 'N42': 1.29, 'N52': 1.43}       # 잔류 자속 밀도 Br [T] 대표값(제조사 표 최소~대표)

def _gl(n, a, b):
    x, w = np.polynomial.legendre.leggauss(n); return 0.5 * (b - a) * x + 0.5 * (b + a), 0.5 * (b - a) * w

def disk_pair_force(R, z, n=600):
    """반지름 R(m) 같은 두 동축 원판(단위 면전하 σ=1), 축 거리 z(m) 사이 축 방향 힘 / σ² (N·m²/A²·...) — z>0 에서 반발이 +."""
    r, w = _gl(n, 0.0, R); a = r[:, None]; b = r[None, :]
    A = a * a + b * b + z * z; B = 2 * a * b; k2 = np.clip(2 * B / (A + B), 0, 1 - 1e-15)
    I = 4 * ellipe(k2) / ((A - B) * np.sqrt(A + B))                         # ∫0^2π dφ /(A − B cosφ)^{3/2}
    qa = 2 * math.pi * a * w[:, None]; qb = 2 * math.pi * b * w[None, :]   # 링 전하 / σ
    return float(MU0 / (4 * math.pi) * np.sum(qa * qb * z * I / (2 * math.pi)))

def pull_force(d, t, br, gap):
    """원판 자석(지름 d, 두께 t mm, Br T)이 두꺼운 철판에서 간격 gap mm 일 때 흡착력 N (이상 상한)."""
    R = d / 2e3; T = t / 1e3; g = max(gap, 0.02) / 1e3; s = br / MU0                       # σ = M = Br/μ0 [A/m]
    n = int(min(2400, max(300, 6 * R / g)))                                                 # 가까울수록 촘촘히(피크 폭 ≈ 2g)
    # 자석(+면 앞 g, −면 g+T) 과 거울상(+면 −g, −면 −g−T; 철판이 같은 방향 자화를 만든다) 네 면 쌍. 끌림을 + 로 돌려준다.
    f = (disk_pair_force(R, 2 * g, n) - disk_pair_force(R, 2 * g + T, n) - disk_pair_force(R, 2 * g + T, n) + disk_pair_force(R, 2 * g + 2 * T, n))
    return f * s * s

def dipole_force(d, t, br, gap):
    """먼 거리 점검용: 쌍극자 m = M·V 와 거울상(중심 거리 2(g+t/2))의 끌림 3μ0 m² / (2π r⁴)."""
    m = br / MU0 * math.pi * (d / 2e3) ** 2 * (t / 1e3); r = 2 * (gap + t / 2) / 1e3
    return 3 * MU0 * m * m / (2 * math.pi * r ** 4)

def hanger(d=20.0, t=1.0, br=1.17, gaps=(0.0, 0.1, 0.5, 1.0), n=3, load_g=150.0, lever=30.0, arm=45.0, mu=0.3, derate=0.5):
    """자석 n 개 걸이의 고정력 판정. lever = 하중 무게중심의 벽에서 앞 돌출(mm), arm = 아래 피벗 모서리 → 자석 중심 높이(mm)."""
    W = load_g * 9.81e-3; rows = []
    for g in gaps:
        F = pull_force(d, t, br, g); Fd = F * derate; N = n * Fd
        rows.append({'gap_mm': g, 'pull_ideal_N': round(F, 2), 'pull_design_N': round(Fd, 2), 'total_design_N': round(N, 2),
                     'slip_capacity_N': round(mu * N, 2), 'slip_safety': round(mu * N / W, 1) if W else None,
                     'peel_safety': round(N * arm / (W * lever), 1) if W and lever else None})
    return {'magnet': f'Ø{d}×{t} Br {br} T', 'n': n, 'load_N': round(W, 3), 'mu': mu, 'derate': derate, 'lever_mm': lever, 'arm_mm': arm, 'rows': rows,
            'note': '이상적 두꺼운 철판 상한 × derate = 설계값. 미끄러짐 = μ·N·F ≥ 하중, 떼어짐 = F합×arm ≥ 하중×lever. 실물은 간단한 매달기 시험으로 확인'}

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--d', type=float, default=20); ap.add_argument('--t', type=float, default=1)
    ap.add_argument('--br', type=float, default=1.17); ap.add_argument('--gaps', type=float, nargs='+', default=[0, 0.1, 0.5, 1.0])
    ap.add_argument('--n', type=int, default=3); ap.add_argument('--load_g', type=float, default=150); ap.add_argument('--lever', type=float, default=30)
    ap.add_argument('--arm', type=float, default=45); ap.add_argument('--mu', type=float, default=0.3); ap.add_argument('--derate', type=float, default=0.5)
    a = ap.parse_args(); r = hanger(a.d, a.t, a.br, a.gaps, a.n, a.load_g, a.lever, a.arm, a.mu, a.derate)
    print(r['magnet'], f"× {r['n']}  하중 {r['load_N']} N")
    for x in r['rows']: print(x)
