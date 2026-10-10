"""모서리 곡선을 '한 도형'으로 입히기 (Toolbox48 v10, 사용자: "그냥 하나의 도형").
뒤집어 출력하는 판(뚜껑) 또는 바닥(본체)의 바깥 모서리를, 둥근 사각형 외곽을 profile 만큼 안으로 줄인 링을 촘촘히(dz) 이은 로프트 하나로 정한다.
  apply_edge(mesh, rect, zp, ip, fill=2.0, dz=0.05)
    rect : 주 외곽(shapely Polygon, 둥근 사각형) — 귀·탭 같은 돌출은 제외한 몸통 외곽
    zp, ip : 곡선 inset(z) 표(z 오름차순, 끝은 0) — 예: 하판 바닥 곡선 measure_profile()
    fill : 외곽 안쪽 fill mm 띠를 먼저 채운 뒤 곡선으로 깎는다 → 원래 면이 군데군데 남아 생기는 이음매(줄) 없음
  결과 = ((mesh ∪ 띠) ∩ 로프트몸통) ∪ (mesh ∩ 외곽 밖)   — 외곽 밖(귀·탭 받침)은 원형 그대로.
판을 쌓거나 일부만 잘라 이어 붙이지 않는다(접힘선·벽 속 틈의 원인)."""
import numpy as np, trimesh
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union
from trimesh.creation import extrude_polygon
from overhang import layer_poly
from loft import loft_rings
from meshops import drop_slivers
def _big(p): return max(p.geoms, key=lambda q: q.area) if isinstance(p, MultiPolygon) else p
def measure_profile(mesh, axis_x_side=True, z_max=8.0, dz=0.05):
    """mesh 바닥 모서리의 inset(z): 각 높이 단면의 x 최소값이 수직 벽(z_max 부근)보다 얼마나 안쪽인지."""
    zs = np.arange(dz, z_max, dz); xs = np.array([layer_poly(mesh, z).bounds[0] for z in zs]); ins = xs - xs[-1]
    ins = np.minimum.accumulate(np.maximum(ins, 0)); ins[ins < 0.002] = 0.0
    return np.r_[0.0, zs], np.r_[ins[0], ins]
def lump_zones(mesh, rect, fill=2.0, H=None, step=0.25):
    """외곽 밖으로 튀어나온 돌출부(귀 받침·탭 기둥)마다, 그 폭 그대로 벽 안쪽 fill+0.5 mm 까지 늘린 직사각 구역.
    이 구역은 원형을 남긴다 — 곡선만 깎고 돌출부만 남기면 둘 사이에 V자 홈이 생긴다(Toolbox48 v10 1차, 걸쇠 탭 x=435 y 197~199 z 0~5)."""
    H = H or float(mesh.bounds[1, 2])
    proj = unary_union([layer_poly(mesh, z) for z in np.arange(0.05, H, step)]).buffer(0)
    lumps = proj.difference(rect.buffer(0.3)); rx0, ry0, rx1, ry1 = rect.bounds; d = fill + 0.5; zones = []
    for g in (lumps.geoms if hasattr(lumps, 'geoms') else [lumps]):
        if g.is_empty or g.area < 0.5: continue
        x0, y0, x1, y1 = g.bounds; side = np.argmin([abs(y1 - ry0) if y1 <= ry0 + 0.5 else 1e9, abs(y0 - ry1) if y0 >= ry1 - 0.5 else 1e9,
                                                     abs(x1 - rx0) if x1 <= rx0 + 0.5 else 1e9, abs(x0 - rx1) if x0 >= rx1 - 0.5 else 1e9])
        if side == 0: zones.append(box(x0, y0, x1, ry0 + d))          # 앞(−y) 벽
        elif side == 1: zones.append(box(x0, ry1 - d, x1, y1))        # 뒤(+y) 벽
        elif side == 2: zones.append(box(x0, y0, rx0 + d, y1))
        else: zones.append(box(rx1 - d, y0, x1, y1))
    return unary_union(zones).buffer(0) if zones else None, lumps
def apply_edge(mesh, rect, zp, ip, fill=2.0, dz=0.05, H=None, M=1600):
    H = H or float(mesh.bounds[1, 2]) + 1.0
    z_end = float(zp[np.argmax(ip <= 0)]) if (ip <= 0).any() else float(zp[-1])
    rr = lambda d: rect.buffer(d, join_style='round', quad_segs=48)
    stack = [(float(z), rr(-float(np.interp(z, zp, ip)))) for z in np.arange(0.0, z_end + dz / 2, dz)]
    stack += [(z_end + 0.3, rr(0.05)), (H, rr(0.05))]
    body = loft_rings(stack, M=M)
    band = extrude_polygon(rect.difference(rect.buffer(-fill)), z_end + 0.2)
    b = mesh.bounds; big = box(b[0, 0] - 5, b[0, 1] - 5, b[1, 0] + 5, b[1, 1] + 5)
    zones, lumps = lump_zones(mesh, rect, fill, b[1, 2])
    keep_xy = big.difference(rr(0.04)).union(zones.buffer(0.01)) if zones is not None else big.difference(rr(0.04))   # 0.01 겹침 — 같은 면 유니온 회피
    out_prism = trimesh.util.concatenate([extrude_polygon(q, H + 1) for q in (keep_xy.geoms if hasattr(keep_xy, 'geoms') else [keep_xy])]); out_prism.apply_translation([0, 0, -0.5])
    core = trimesh.boolean.intersection([trimesh.boolean.union([mesh, band], engine='manifold'), body], engine='manifold')
    if zones is not None:
        zp_ = trimesh.util.concatenate([extrude_polygon(q, H + 1) for q in (zones.geoms if hasattr(zones, 'geoms') else [zones])]); zp_.apply_translation([0, 0, -0.5])
        core = trimesh.boolean.difference([core, zp_], engine='manifold')
    keep = trimesh.boolean.intersection([mesh, out_prism], engine='manifold')
    res = trimesh.boolean.union([core, keep], engine='manifold') if len(keep.faces) else core
    res, n, v = drop_slivers(res)
    nz = len(zones.geoms) if zones is not None and hasattr(zones, 'geoms') else (1 if zones is not None else 0)
    return res, {'z_end': z_end, 'rings': len(stack), 'slivers_removed': n, 'sliver_mm3': v, 'lump_zones': nz,
                 'zones': [[round(c, 1) for c in q.bounds] for q in (zones.geoms if zones is not None and hasattr(zones, 'geoms') else ([zones] if zones is not None else []))]}
def fit_rounded_rect(mesh, z, x_probe=None):
    """z 높이 단면에서 몸통 둥근 사각형(x·y 범위, 모서리 반경)을 잰다. 귀·탭이 없는 x(x_probe)에서 y 범위를 잰다."""
    p = _big(layer_poly(mesh, z)); x0, _, x1, _ = p.bounds; xp = x_probe if x_probe is not None else (x0 + x1) / 2
    seg = p.intersection(box(xp - 0.01, -1e4, xp + 0.01, 1e4)); y0, y1 = seg.bounds[1], seg.bounds[3]
    # 모서리 반경: x0 쪽 아래 모서리 근처에서 단면이 직선 벽(x0)에서 벗어나기 시작하는 y
    for r in np.arange(0.5, 40, 0.25):
        s = p.intersection(box(-1e4, y0 + r - 0.01, 1e4, y0 + r + 0.01))
        if not s.is_empty and s.bounds[0] - x0 < 0.01: break
    R = float(r)
    A = box(x0 + R, y0 + R, x1 - R, y1 - R).buffer(R, quad_segs=48)
    # 실제 외곽: 원본 벽 다각형 그대로(모서리가 각진 다각형이면 해석 원호와 최대 ~0.1 mm 차이 → 원본 벽과 곡선이 만나는 높이에 턱/줄, v10 1차 z 7.08 네 모서리).
    # 귀·탭 혹(외곽 밖 0.3 넘게 튀어나온 부분)만 해석 외곽으로 잘라낸다 — 혹은 직선 벽 위에 있으므로 원본 벽 = 해석 외곽인 곳.
    lumps = p.difference(A.buffer(0.3))
    true = p.intersection(A.buffer(0.3))
    if not lumps.is_empty: true = true.difference(lumps.buffer(1.0).difference(A))
    true = _big(true.buffer(0))
    return Polygon(true.exterior), {'x': [x0, x1], 'y': [y0, y1], 'R': R, 'lumps': len(getattr(lumps, 'geoms', [lumps])) if not lumps.is_empty else 0}
