"""Actual meshes: shallow foot, round rear bearing, and wavy body seam."""
from pathlib import Path
import sys,pickle,json
import numpy as np,trimesh as tm
from trimesh.transformations import rotation_matrix as R,translation_matrix as T
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'scripts'));sys.path.insert(0,str(p.parent.parent/'tools'))
from build import P,box
import mm
parts=pickle.load(open(p/'parts_nominal.pkl','rb'));up=parts['shell_upper'].copy();up.apply_translation([0,0,P['BODY_SPLIT_Z']])
cut=lambda m,z0,z1:tm.boolean.intersection([m,box(-50,-50,z0,50,50,z1)],engine='manifold')
meshes={'아래몸통':cut(parts['shell_lower'],101,148),'위몸통':cut(up,101,150),'내관끝':cut(parts['drawer'],201,223),'원형뒤컵':parts['rear_head'],'내관':parts['drawer']}
pickle.dump({n:m.copy(include_cache=False) for n,m in meshes.items()},open(p/'figures/details.pkl','wb'))
G=T([100,255,40])@R(np.pi/2,[1,0,0]);U=T([100,10,40])@R(-np.pi/2,[1,0,0])
states={'물결 숫돌기·암홈 조립':{'아래몸통':G,'위몸통':G},'물결 숫돌기·암홈 분리':{'아래몸통':G,'위몸통':G@T([0,0,10])},'뒤끝 원형 가이드 조립':{'내관끝':G,'원형뒤컵':G},'뒤컵 끼움부 분리':{'내관끝':G,'원형뒤컵':G@T([0,0,14])},'좁은 접시 굽·강화 돌기':{'내관':U}}
r=mm.run('render',files=[str(p/'figures/details.pkl')],out=str(p/'preview_details_R15'),states={k:{n:M.ravel().tolist() for n,M in v.items()} for k,v in states.items()},colors={'아래몸통':'#bd6f53','위몸통':'#33383e','내관끝':'#bd6f53','원형뒤컵':'#bd6f53','내관':'#bd6f53'},frames=30,status='R15 · 기존 둥근 외관 · 좁은 바닥 굽 · 원형 뒤가이드 · 물결 맞물림(결합설명색) · 실물 힘·수명 미검증')
json.dump(r,open(p/'qc/detail_render_R15.json','w'),ensure_ascii=False,indent=1)
