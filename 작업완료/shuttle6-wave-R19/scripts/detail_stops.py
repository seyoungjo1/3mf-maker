from pathlib import Path
import sys,pickle,numpy as np,trimesh as tm
ROOT=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT/'tools'))
from render_preview import render
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
p=pickle.load(open(O/'parts_nominal.pkl','rb'));up=p['shell_upper'].copy();up.apply_translation([0,0,121.5]);shell=tm.util.concatenate([p['shell_lower'],up]);closed=T([0,0,253.])@R(np.pi,[0,1,0]);rear=p['drawer'].copy();rear.apply_transform(T([0,0,225])@closed)
window=tm.creation.box([120,60,52]);window.apply_translation([0,-30,231]);body=tm.boolean.intersection([shell,window],engine='manifold');rear=tm.boolean.intersection([rear,window],engine='manifold');G=T([128,250,45])@R(np.pi/2,[1,0,0])
parts={'body_cut':body,'rear_cut':rear,'stop_left':p['stop_left'],'stop_right':p['stop_right']};states={'좌우 멈춤·관찰용 윗면 절개':{n:G for n in parts},'좌우 블록 외측 장착':{'body_cut':G,'rear_cut':G,'stop_left':G@T([-9,0,0]),'stop_right':G@T([9,0,0])}}
render(parts,str(O/'preview_stops'),colors={'body_cut':'#33383e','rear_cut':'#bd6f53','stop_left':'#4b9eba','stop_right':'#4b9eba'},states={k:{n:m.ravel().tolist() for n,m in v.items()} for k,v in states.items()},frames=20,status='완료 — 관찰용 단면 / 뒤컵 좌우 어깨(주황)↔입구 좌우 블록(파랑) / 바닥 멈춤부 없음')
