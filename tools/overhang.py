"""0.2 mm 층당 수평 돌출 ≤ 0.115 mm 규칙 검사 (toolbox42/scripts/overhang_check.py 와 동일 알고리즘)."""
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.affinity import affine_transform
def layer_poly(mesh, z):
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None: return Polygon()
    p2, T = sec.to_2D(normal=[0, 0, 1]); polys = list(p2.polygons_full)
    if not polys: return Polygon()
    a, b, c, d, xo, yo = T[0, 0], T[0, 1], T[1, 0], T[1, 1], T[0, 3], T[1, 3]
    return unary_union([affine_transform(q, [a, b, c, d, xo, yo]) for q in polys]).buffer(0)
def check(mesh, layer=0.2, maxstep=0.115, min_area=0.5):
    """returns (total_area, [(z, area, bounds), ...] sorted by area desc)"""
    zmax = mesh.bounds[1, 2]; prev = None; bad = []; total = 0.0; z = layer / 2 + 0.0137
    while z < zmax:
        cur = layer_poly(mesh, z)
        if prev is not None and not cur.is_empty:
            unsup = cur.difference(prev.buffer(maxstep)); a = unsup.area
            if a > min_area: bad.append((round(z, 2), round(a, 1), tuple(round(v, 1) for v in unsup.bounds))); total += a
        prev = cur; z += layer
    bad.sort(key=lambda t: -t[1]); return total, bad
