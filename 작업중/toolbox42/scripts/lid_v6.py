"""뚜껑 v6: 윗면 모서리 = 바닥에서 LAND mm 수직(전체 윤곽) + 그 위부터 본체 바닥과 같은 곡선(v5 곡선을 LAND 만큼 올림).
v6 = (v5 − [바깥 띠 안에서 올린 곡선 밖에 남는 입술]) ∪ [바닥 수직 띠]. 로고 포켓·경첩 귀·걸쇠 탭(기둥 포함)은 건드리지 않는다."""
import pickle, sys, numpy as np, trimesh
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from trimesh.creation import triangulate_polygon, extrude_polygon
import os; sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..','tools')); from overhang import layer_poly, check
# 사용: python lid_v6.py <v5parts.pkl> [LAND=0.8]  → lid_v6.pkl
LAND=float(sys.argv[2]) if len(sys.argv)>2 else 0.8
P=pickle.load(open(sys.argv[1],'rb')); lid=P['lid']; logo=P['logo']
ZTOP=7.8; M=900; dz=0.2
def polys(p): return list(p.geoms) if p.geom_type=='MultiPolygon' else [p]
def outer_ring(poly):
    ext=max(polys(poly),key=lambda q:q.area).exterior
    L=ext.length; xc=(poly.bounds[0]+poly.bounds[2])/2; st=ext.project(Point(xc,poly.bounds[1]))
    t=(st+np.linspace(0,L,M,endpoint=False))%L; pts=np.array([ext.interpolate(v).coords[0] for v in t])
    return pts if ext.is_ccw else pts[::-1]
full_ext=Polygon(outer_ring(layer_poly(lid,ZTOP)))            # 전체 윤곽(수직 벽 구간, 귀·탭 제외)
zs=np.round(np.arange(0,ZTOP+dz/2,dz),3); rings=[]
for z in zs:
    zsrc=z-LAND
    rings.append(outer_ring(full_ext) if zsrc<0.05 else outer_ring(layer_poly(lid,min(zsrc,ZTOP))))
V=np.vstack([np.column_stack([r,np.full(M,z)]) for z,r in zip(zs,rings)]); F=[]
for k in range(len(zs)-1):
    a=k*M; b=(k+1)*M; i=np.arange(M); j=(i+1)%M; F.append(np.column_stack([a+i,a+j,b+j])); F.append(np.column_stack([a+i,b+j,b+i]))
F=np.vstack(F).tolist()
for k,sign in [(0,-1),(len(zs)-1,1)]:
    vv,ff=triangulate_polygon(Polygon(rings[k]),engine='earcut'); bi=len(V); V=np.vstack([V,np.column_stack([vv,np.full(len(vv),zs[k])])]); F.extend(((ff[:,::-1] if sign<0 else ff)+bi).tolist())
loft=trimesh.Trimesh(V,np.array(F),process=True); loft.merge_vertices(); trimesh.repair.fix_normals(loft); print('loft is_volume',loft.is_volume)
# 잘라낼 띠: 바깥 4 mm 띠, 걸쇠 탭 구역(x 415~455, y>183)은 제외
band=full_ext.buffer(0.6).difference(full_ext.buffer(-4.0)).difference(box(415,183,456,200))
cut_region=extrude_polygon(band,ZTOP+0.2); cut_region.apply_translation([0,0,-0.1])
lip=cut_region.difference(loft,engine='manifold')                      # 띠 안에서 올린 곡선 밖 = 제거할 입술
lid6=lid.difference(lip,engine='manifold')
# 바닥 수직 띠: 전체 윤곽 − 로고 포켓(모든 글자) , z 0..LAND
p05=layer_poly(lid,0.5); pockets=unary_union([Polygon(i) for g in polys(p05) for i in g.interiors]).buffer(0.3)
slab_poly=full_ext.difference(pockets); slab=trimesh.util.concatenate([extrude_polygon(g,LAND+0.02) for g in polys(slab_poly) if g.area>0.5]); slab.apply_translation([0,0,-0.01])
lid6=lid6.union(slab,engine='manifold'); lid6.apply_translation([0,0,-lid6.bounds[0,2]])
print('lid6 is_volume',lid6.is_volume,'vol',round(lid.volume),'->',round(lid6.volume),'faces',len(lid6.faces),'lid∩logo',round(lid6.intersection(logo,engine='manifold').volume,3),'bounds',lid6.bounds.round(2).tolist())
# 보존 확인: 경첩 귀(y<72, z>8), 탭 구역(y>184), 로고 포켓 부피
def region_vol(m,b): 
    bx=trimesh.creation.box(extents=[b[1][0]-b[0][0],b[1][1]-b[0][1],b[1][2]-b[0][2]]); bx.apply_translation([(b[0][i]+b[1][i])/2 for i in range(3)]); r=m.intersection(bx,engine='manifold'); return round(r.volume,2) if r.is_volume else 0
for nm,bb in [('경첩 귀 구역',[[340,60,8],[530,72,19]]),('걸쇠 탭 구역',[[415,183,3],[456,200,19]])]:
    print(f'  {nm}: v5 {region_vol(lid,bb)} / v6 {region_vol(lid6,bb)} mm³')
zz=np.arange(0.1137,8.0,0.2)
def prof(m): xs=np.array([layer_poly(m,z).bounds[0] for z in zz]); return xs-xs[zz>7.5].min()
pb=prof(P['base']); p5=prof(lid); p6=prof(lid6)
print(' z    본체    v5    v6')
for z,a,b,c in zip(zz,pb,p5,p6):
    if z<2.2 or abs(z-round(z))<0.11: print(f'{z:5.2f} {a:6.2f} {b:6.2f} {c:6.2f}')
print('첫층 면적 v5 %.0f → v6 %.0f ; 층당 바깥 돌출 최대 v6 %.3f'%(layer_poly(lid,0.1137).area,layer_poly(lid6,0.1137).area,-np.diff(p6).min()))
tot,bad=check(lid6); print('v6 overhang total %.0f'%tot, bad[:5])
pickle.dump(lid6,open('lid_v6.pkl','wb')); np.save('prof_v6.npy',np.c_[zz,pb,p5,p6]); print('saved')
