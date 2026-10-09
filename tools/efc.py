"""코끼리발 보정(EFC) 선반영: 사용자 프로파일(EFC 0.15)이 첫 층 윤곽을 0.15 깎으므로, 모델의 첫 층(0~layer)을 미리 0.15 키워
출력물의 1→2층 단차를 0 으로 만든다(Toolbox42 뚜껑 v6 방식). 출력 방향(바닥 z=0) 메시에만 쓴다."""
import numpy as np, trimesh
from shapely.geometry import Polygon, MultiPolygon
from overhang import layer_poly
def _extrude(poly, h):
    polys = list(poly.geoms) if isinstance(poly, MultiPolygon) else [poly]
    ms = [trimesh.creation.extrude_polygon(p, h) for p in polys if p.area > 1e-6]
    return trimesh.util.concatenate(ms) if ms else None
def pre_expand_first_layer(mesh, efc=0.15, layer=0.2):
    """첫 층 단면을 efc 만큼 바깥으로(구멍은 안으로) 키운 0.2 mm 판을 유니온해 돌려준다. 바닥이 z=0 이어야 한다."""
    assert abs(mesh.bounds[0, 2]) < 1e-6, '바닥을 z=0 으로 옮긴 뒤 호출'
    p = layer_poly(mesh, layer / 2).buffer(efc, join_style='mitre')
    skirt = _extrude(p, layer)
    if skirt is None: return mesh
    out = trimesh.boolean.union([mesh, skirt], engine='manifold')
    return out if out.is_volume else mesh
def pre_expand_first_layer_group(meshes, efc=0.15, layer=0.2):
    """서로 면접촉하는 파트들(같은 오브젝트의 색 파트)을 한 덩어리로 보고 바깥 윤곽만 efc 키운다.
    키운 띠는 그 자리에 닿아 있는 파트에 나눠 붙인다(파트끼리 겹치지 않음). 반환: 같은 순서의 메시 목록."""
    from shapely.ops import unary_union
    polys = [layer_poly(m, layer / 2) for m in meshes]
    U = unary_union(polys); S = U.buffer(efc, join_style='mitre').difference(U)
    out = []; taken = None
    for m, p in zip(meshes, polys):
        mine = S.intersection(p.buffer(efc + 0.01, join_style='mitre'))
        if taken is not None: mine = mine.difference(taken)
        taken = mine if taken is None else taken.union(mine)
        skirt = _extrude(mine.buffer(0), layer) if not mine.is_empty else None
        if skirt is None: out.append(m); continue
        u = trimesh.boolean.union([m, skirt], engine='manifold'); out.append(u if u.is_volume else m)
    return out
