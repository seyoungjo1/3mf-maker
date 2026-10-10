"""코끼리발 보정(EFC) 선반영: 사용자 프로파일(EFC 0.15)이 첫 층 윤곽을 0.15 깎으므로, 모델의 첫 층(0~layer)을 미리 0.15 키워
출력물의 1→2층 단차를 0 으로 만든다(Toolbox42 뚜껑 v6 방식). 출력 방향(바닥 z=0) 메시에만 쓴다."""
import numpy as np, trimesh
from shapely.geometry import Polygon, MultiPolygon
from overhang import layer_poly
def _extrude(poly, h):
    polys = list(poly.geoms) if isinstance(poly, MultiPolygon) else [poly]
    ms = [trimesh.creation.extrude_polygon(p, h) for p in polys if p.area > 1e-6]
    return trimesh.util.concatenate(ms) if ms else None
def _drop_slivers(m, ref_volume):
    """불리언이 남긴 부피 0 껍질 조각(같은 면 유니온)을 버린다. 의미 있는 조각(≥1 mm³)은 그대로 둔다."""
    bs = m.split(only_watertight=False)
    if len(bs) <= 1: return m
    keep = [b for b in bs if abs(b.volume) >= 1.0]
    out = trimesh.util.concatenate(keep) if len(keep) > 1 else keep[0]
    return out if out.is_volume and abs(abs(out.volume) - ref_volume) < 0.5 else m
OVERLAP = 0.05   # 띠를 파트 안쪽으로 겹치는 폭 — 띠 안쪽 경계가 수직 벽과 같은 면이면 manifold 유니온이 부피 0 조각을 남긴다
def pre_expand_first_layer(mesh, efc=0.15, layer=0.2):
    """첫 층 단면을 efc 만큼 바깥으로(구멍은 안으로) 키운 0.2 mm 판을 유니온해 돌려준다. 바닥이 z=0 이어야 한다."""
    assert abs(mesh.bounds[0, 2]) < 1e-6, '바닥을 z=0 으로 옮긴 뒤 호출'
    p0 = layer_poly(mesh, layer / 2); p = p0.buffer(efc, join_style='mitre').difference(p0.buffer(-OVERLAP))
    skirt = _extrude(p, layer)
    if skirt is None: return mesh
    out = trimesh.boolean.union([mesh, skirt], engine='manifold')
    if not out.is_volume: return mesh
    return _drop_slivers(out, abs(out.volume))
def pre_expand_first_layer_group(meshes, efc=0.15, layer=0.2):
    """서로 면접촉하는 파트들(같은 오브젝트의 색 파트)을 한 덩어리로 보고 바깥 윤곽만 efc 키운다.
    키운 띠는 그 자리에 닿아 있는 파트에 나눠 붙인다(파트끼리 겹치지 않음). 반환: 같은 순서의 메시 목록."""
    from shapely.ops import unary_union
    polys = [layer_poly(m, layer / 2) for m in meshes]
    U = unary_union(polys)
    # 바깥 윤곽만: 구멍(인레이 포켓과 인레이 사이 틈 등)은 채운 외피 기준으로 띠를 만든다 — 구멍 안까지 키우면 부피 0 찌꺼기 조각이 생긴다(Toolbox48 v8 뚜껑 24조각)
    env = unary_union([Polygon(g.exterior) for g in (U.geoms if isinstance(U, MultiPolygon) else [U]) if g.area > 1e-6])
    S = env.buffer(efc, join_style='mitre').difference(env); inner = env.difference(env.buffer(-OVERLAP))
    out = []; taken = None
    for m, p in zip(meshes, polys):
        mine = S.intersection(p.buffer(efc + 0.01, join_style='mitre'))
        if taken is not None: mine = mine.difference(taken)
        taken = mine if taken is None else taken.union(mine)
        mine = mine.union(inner.intersection(p))          # 자기 파트 안쪽으로만 0.05 겹침(이웃 파트 침범 없음)
        mine = unary_union([g for g in (mine.geoms if hasattr(mine, 'geoms') else [mine]) if getattr(g, 'area', 0) > 0.01]) if not mine.is_empty else mine
        skirt = _extrude(mine.buffer(0), layer) if not mine.is_empty else None
        if skirt is None: out.append(m); continue
        u = trimesh.boolean.union([m, skirt], engine='manifold'); out.append(_drop_slivers(u, abs(u.volume)) if u.is_volume else m)
    return out
