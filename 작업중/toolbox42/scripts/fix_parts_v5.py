"""걸쇠: 눕혀 출력 + 바깥면(z=0.55)을 링 밑면(z=0)까지 채워 바닥 전면 접지.  손잡이: 곧은 다리 구간을 다리 끝 폭(5.4)으로 두껍게."""
import pickle, numpy as np, trimesh, sys
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from trimesh.creation import extrude_polygon
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from overhang_check import check, layer_poly
from load3mf import load_parts
# 사용: python fix_parts_v5.py models/Toolbox42_P1S_v4.3mf models/00_original_chatgpt_Toolbox42_P1S_Compact_M3.3mf v5parts.pkl
P=load_parts(sys.argv[1]); O=load_parts(sys.argv[2])
latch=O['latch'].copy(); handle=P['handle'].copy()
# ---- 걸쇠 ----
foot=layer_poly(latch,1.0)                       # z=1.0 윤곽(링·암·판·쐐기 끝 포함)
fill=extrude_polygon(foot.buffer(0),1.0); fill.apply_translation([0,0,-0.0])   # z 0..1.0
latch2=latch.union(fill,engine='manifold'); latch2.apply_translation([0,0,-latch2.bounds[0,2]])
print('latch: volume',round(latch.volume,1),'->',round(latch2.volume,1),'is_volume',latch2.is_volume,'bounds',latch2.bounds.round(2).tolist())
m=latch2; sel=(m.face_normals[:,2]<-0.99)&(m.triangles_center[:,2]<0.05); print('latch bed contact area', m.area_faces[sel].sum().round(1),'mm2 (footprint', round(foot.area,1),')')
# 결합 치수 보존 확인: 링 구멍(지름 3.4, 중심 y -192.11 z 2.8), 암 간격, 쐐기면(z=5.05 윗면) 변화 없음
def hole(mesh,x):
    s=mesh.section(plane_origin=[x,0,0],plane_normal=[1,0,0]); p2,T=s.to_2D(normal=[1,0,0])
    for q in p2.polygons_full:
        for i in q.interiors:
            c=np.array(i.coords); c3=(np.c_[c,np.zeros(len(c)),np.ones(len(c))]@T.T)[:,:3]; return (c3[:,1].max()-c3[:,1].min()).round(3),(c3[:,2].max()-c3[:,2].min()).round(3),((c3[:,1].max()+c3[:,1].min())/2).round(3),((c3[:,2].max()+c3[:,2].min())/2).round(3)
print('latch hole before',hole(latch,171),'after',hole(latch2,171),'| right',hole(latch2,209))
top_before=latch.slice_plane([0,0,2.0],[0,0,1]); top_after=latch2.slice_plane([0,0,2.0],[0,0,1])
print('latch upper half (z>2) volume before/after', round(top_before.volume,2), round(top_after.volume,2))
# ---- 손잡이 ----
hb=handle.bounds; y_bar=-187.58; y_end=-172.0
legs=[(60.93,66.33),(133.68,139.08)]
adds=[extrude_polygon(box(x0,y_bar-1.0,x1,y_end),9.0) for x0,x1 in legs]
handle2=handle.union(trimesh.util.concatenate(adds),engine='manifold')
print('handle: volume',round(handle.volume,1),'->',round(handle2.volume,1),'is_volume',handle2.is_volume,'bounds',handle2.bounds.round(2).tolist())
# 다리 끝(y>-172) 형상 보존 확인: y=-165 단면 동일
def sec_area(mesh,y):
    s=mesh.section(plane_origin=[0,y,0],plane_normal=[0,1,0]); p2,_=s.to_2D(normal=[0,1,0]); return round(sum(q.area for q in p2.polygons_full),3)
for y in [-163,-168,-171,-175,-180]: print(f'  handle section area y={y}: before {sec_area(handle,y)} after {sec_area(handle2,y)}')
m=handle2; sel=(m.face_normals[:,2]<-0.99)&(m.triangles_center[:,2]<0.05); print('handle bed contact area', m.area_faces[sel].sum().round(1))
print('--- overhang rule check ---')
check(latch2,'latch v5 (flat)'); check(handle2,'handle v5'); check(P['lid'],'lid (v4 flat, unchanged)'); check(P['base'],'base (unchanged)')
pickle.dump({'base':P['base'],'lid':P['lid'],'logo':P['logo'],'handle':handle2,'latch':latch2},open(sys.argv[3],'wb')); print('saved v5parts.pkl')
