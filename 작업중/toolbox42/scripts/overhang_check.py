import numpy as np, trimesh
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
LAYER=0.2; MAXSTEP=0.115
def layer_poly(mesh,z):
    sec=mesh.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
    if sec is None: return Polygon()
    p2,T=sec.to_2D(normal=[0,0,1])
    polys=list(p2.polygons_full)
    if not polys: return Polygon()
    # map back to world XY: to_2D used transform T (4x4); world = T^-1 applied to (x,y,0)
    import numpy as np
    from shapely.affinity import affine_transform
    Ti=T
    a,b,c,d,xoff,yoff=Ti[0,0],Ti[0,1],Ti[1,0],Ti[1,1],Ti[0,3],Ti[1,3]
    region=unary_union([affine_transform(q,[a,b,c,d,xoff,yoff]) for q in polys])
    return region.buffer(0)
def check(mesh,name,report_top=6):
    zmax=mesh.bounds[1,2]; prev=None; bad=[]; total=0
    k=0; z=LAYER/2+0.0137
    while z<zmax:
        cur=layer_poly(mesh,z)
        if prev is not None and not cur.is_empty:
            unsup=cur.difference(prev.buffer(MAXSTEP))
            a=unsup.area
            if a>0.5: bad.append((round(z,2),a,unsup.bounds)); total+=a
        prev=cur; z+=LAYER; k+=1
    bad.sort(key=lambda t:-t[1])
    print(f'== {name}: layers={k}, unsupported-by-rule area total={total:.0f} mm² in {len(bad)} layers')
    for z,a,b in bad[:report_top]: print(f'   z={z:5.2f} area={a:7.1f}  x[{b[0]:.1f},{b[2]:.1f}] y[{b[1]:.1f},{b[3]:.1f}]')
    return total
if __name__=='__main__':
    import sys; sys.path.insert(0,'/home/claude'); from load3mf import load_parts
    p=load_parts('/tmp/claude-0/-home-claude/896aa1c8-8e29-58d9-8e4f-9137638ec972/scratchpad/3mf/in.3mf')
    for n in ['base','lid','logo','handle','latch']: check(p[n],n)
