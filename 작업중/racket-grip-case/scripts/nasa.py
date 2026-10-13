"""NASA 우주 직물형 적층섬유 부재 — 앞면(베드 면)은 촘촘한 사각 비늘, 뒷면은 비늘마다 달린 고리가 이웃과 맞물린다(한 번에 출력).
격자: 피치 p 정사각 격자에 A·B 체커보드. 비늘 한 변 2a, 비늘 사이 틈 GAP.
- A: 비늘 = 테두리(폭 F, 가운데 구멍) + 모서리 기둥 4 + 윗 고리(기둥 사이 브리지). 옆면 4개가 창.
- B: 꽉 찬 비늘 + 비늘 위 십자 리브(비늘과 한 몸) → 비늘 끝에서 팔(브리지)이 이웃 A 창을 지나
     A 구멍 안 쐐기 머리판(베드에서 시작) + 머리 기둥에 닿는다. 머리판은 A 테두리 아래쪽에 걸려 빠지지 않는다.
  A 구멍은 이웃 B 4개의 쐐기 머리판이 X 자 틈(0.42)으로 채운다 → 앞면이 거의 꽉 찬 비늘 면.
모든 면 수직 + 양쪽 지지 브리지(팔 2.1, 윗 고리 6.0) → 한쪽 지지 오버행 0."""
import manifold3d as mf

N = dict(a=4.4, GAP=0.4, TH=1.2, F=1.3, S=1.4, RZ0=3.6, RZ1=4.6, AW=1.3, AZ0=1.8, AZ1=2.8, G=0.4, D=0.3, TIP=1.0)
N['p'] = 2 * N['a'] + N['GAP']                               # 9.2

def box(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

def prism(pts, z0, z1):
    pts = [(float(x), float(y)) for x, y in pts]
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    if area < 0: pts = pts[::-1]                                  # 거울 배치(x↔y)로 뒤집힌 윤곽은 반시계로 돌려 놓는다
    return mf.CrossSection([pts]).extrude(z1 - z0).translate([0, 0, z0])

def union(ms): return mf.Manifold.batch_boolean(ms, mf.OpType.Add)

def elem_A(cx, cy, n=N):
    a, F, S, TH, RZ0, RZ1 = n['a'], n['F'], n['S'], n['TH'], n['RZ0'], n['RZ1']
    ring = lambda z0, z1, w: [box(cx - a, cx + a, cy - a, cy - a + w, z0, z1), box(cx - a, cx + a, cy + a - w, cy + a, z0, z1),
                              box(cx - a, cx - a + w, cy - a, cy + a, z0, z1), box(cx + a - w, cx + a, cy - a, cy + a, z0, z1)]
    posts = [box(cx + (a - S if sx > 0 else -a), cx + (a if sx > 0 else -a + S), cy + (a - S if sy > 0 else -a), cy + (a if sy > 0 else -a + S), 0, RZ1)
             for sx in (-1, 1) for sy in (-1, 1)]
    return union(ring(0, TH, F) + ring(RZ0, RZ1, F) + posts)

def head_in_A(ax, ay, side, n=N):
    """A(ax, ay) 구멍 안, side 쪽(B 가 있는 방향 단위벡터, 예 (-1,0) = A 의 -x 쪽 B)에서 들어온 쐐기 머리판 + 머리 기둥 + 팔(A 테두리 위)."""
    a, F, G, D, TIP, TH, AW, AZ0, AZ1 = (n[k] for k in ('a', 'F', 'G', 'D', 'TIP', 'TH', 'AW', 'AZ0', 'AZ1'))
    o = a - F; base = o - G                                   # 3.1, 2.7
    # 기준(side = (-1,0)) 좌표: u = 바깥쪽(−x) 거리, v = 옆
    plate = [(-base, -(base - D)), (-TIP, -(TIP - D)), (-TIP, TIP - D), (-base, base - D)]
    post = [(-base, -AW / 2), (-base + 1.3, -AW / 2), (-base + 1.3, AW / 2), (-base, AW / 2)]
    arm_x0 = -(n['p'] - a) + 0.0                               # B 비늘 끝(A 쪽) = A 중심에서 -(p - a) = -4.8
    arm = [(arm_x0 - 0.05, -AW / 2), (-base + 1.3, -AW / 2), (-base + 1.3, AW / 2), (arm_x0 - 0.05, AW / 2)]
    sx, sy = side
    def T(pts):                                                # 기준 (x, y) → 실제: side 방향으로 회전
        if (sx, sy) == (-1, 0): return [(ax + x, ay + y) for x, y in pts]
        if (sx, sy) == (1, 0): return [(ax - x, ay - y) for x, y in pts]
        if (sx, sy) == (0, -1): return [(ax + y, ay + x) for x, y in pts]
        return [(ax - y, ay - x) for x, y in pts]
    return [prism(T(plate), 0, TH), prism(T(post), 0, AZ1), prism(T(arm), AZ0, AZ1)]

def elem_B(cx, cy, dirs, n=N):
    """dirs: 이웃 A 가 있는 방향 단위벡터 목록."""
    a, TH, AW, AZ1, p = n['a'], n['TH'], n['AW'], n['AZ1'], n['p']
    ms = [box(cx - a, cx + a, cy - a, cy + a, 0, TH)]
    for dx, dy in dirs:
        if dx: xs = sorted([cx, cx + dx * a]); ms.append(box(xs[0], xs[1], cy - AW / 2, cy + AW / 2, TH - 0.05, AZ1))
        else: ys = sorted([cy, cy + dy * a]); ms.append(box(cx - AW / 2, cx + AW / 2, ys[0], ys[1], TH - 0.05, AZ1))
        ms += head_in_A(cx + dx * p, cy + dy * p, (-dx, -dy), n)
    return union(ms)

def sheet(n_x, n_y, n=N, x0=0.0, y0=0.0, keep=None):
    """n_x × n_y 격자 시트. keep(i, j) 가 False 인 칸은 비움. 반환 (A 목록, B 목록) — 칸 (i,j) 중심 (x0 + i p, y0 + j p), i+j 짝수 = A."""
    p = n['p']; cells = {(i, j): ('A' if (i + j) % 2 == 0 else 'B') for i in range(n_x) for j in range(n_y) if keep is None or keep(i, j)}
    As, Bs = [], []
    for (i, j), t in cells.items():
        cx, cy = x0 + i * p, y0 + j * p
        if t == 'A': As.append(elem_A(cx, cy, n))
        else:
            dirs = [(dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if cells.get((i + dx, j + dy)) == 'A']
            Bs.append(elem_B(cx, cy, dirs, n))
    return As, Bs
