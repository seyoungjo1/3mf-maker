"""v2 공통 기하 함수: 상자·원기둥·링·2D 프로파일 압출·경로 상자·배열."""
import numpy as np, trimesh
from trimesh.creation import box, cylinder, extrude_polygon
from trimesh.transformations import rotation_matrix as R, translation_matrix as T
from shapely.geometry import Polygon, box as sbox
from shapely.ops import unary_union
def U(ms):
    ms=[m for m in ms if m is not None and len(m.faces)]
    return ms[0] if len(ms)==1 else trimesh.boolean.union(ms, engine='manifold')
def D(a,b): return a.difference(b, engine='manifold')
def I(a,b): return a.intersection(b, engine='manifold')
def B(sx,sy,sz,cx=0,cy=0,z0=0):
    b=box(extents=[sx,sy,sz]); b.apply_translation([cx,cy,z0+sz/2]); return b
def CYL(d,h,cx=0,cy=0,z0=0,sec=48):
    c=cylinder(radius=d/2,height=h,sections=sec); c.apply_translation([cx,cy,z0+h/2]); return c
def RING(w,d,h,z0,wall,cx=0,cy=0): return D(B(w,d,h,cx,cy,z0), B(w-2*wall,d-2*wall,h+2,cx,cy,z0-1))
def EXT(poly, h, z0=0):
    """shapely 폴리곤(또는 멀티) 을 z0 에서 h 만큼 압출"""
    polys=list(poly.geoms) if hasattr(poly,'geoms') else [poly]
    ms=[extrude_polygon(p,h) for p in polys if p.area>1e-6]
    m=trimesh.util.concatenate(ms) if len(ms)>1 else ms[0]; m.apply_translation([0,0,z0]); return m
def HULL(pts): return trimesh.convex.convex_hull(np.array(pts,float))
def segbox(p0,p1,w,h,up=(0,0,1)):
    """점 p0→p1 을 잇는 각재(폭 w, 높이 h): 단면이 경로에 수직. 길이 방향 양 끝 평면."""
    p0,p1=np.array(p0,float),np.array(p1,float); d=p1-p0; L=np.linalg.norm(d); d/=L
    u=np.cross(d,np.array(up,float)); u/=np.linalg.norm(u); v=np.cross(u,d)
    pts=[p0+sx*u*w/2+sz*v*h/2 for sx in(-1,1) for sz in(-1,1)]+[p1+sx*u*w/2+sz*v*h/2 for sx in(-1,1) for sz in(-1,1)]
    return HULL(pts)
def centers(lo,hi,pitch,margin=0.0):
    """lo..hi 안에 pitch 간격으로 균등 배치한 중심들(양 끝 여백 자동)"""
    n=max(1,int((hi-lo-2*margin)//pitch)); span=(n-1)*pitch; s=(lo+hi)/2-span/2
    return [s+i*pitch for i in range(n)]
def flip_x(m):
    q=m.copy(); q.apply_transform(R(np.pi,[1,0,0])); return q
def drop(m):
    q=m.copy(); q.apply_translation([0,0,-q.bounds[0,2]]); return q
