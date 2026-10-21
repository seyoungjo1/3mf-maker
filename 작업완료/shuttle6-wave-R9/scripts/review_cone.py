"""Magnified actual CAD section for reviewing the rounded, filled rear scoop.

Clips the already inspected nominal meshes at z178, retaining actual geometry.
The earlier revision is optional; final model reproduction does not depend on it.
"""
from pathlib import Path
import sys,pickle,json,numpy as np,trimesh as tm
from trimesh.transformations import rotation_matrix as R,translation_matrix as T
P=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(P.parent.parent/'tools'));sys.path.insert(0,str(P/'scripts'))
import mm
from build import box
assert json.load(open(P/'qc/run_R9.json'))['ok']
sources={'수정 R9':pickle.load(open(P/'parts_nominal.pkl','rb'))['drawer']}
old=P.parent/'shuttle6-wave-R8/parts_nominal.pkl'
if old.is_file():sources={'이전 R8':pickle.load(open(old,'rb'))['drawer'],**sources}
parts={};states={}
M=T([128,150,45])@R(np.pi/2,[1,0,0])@R(np.pi,[0,1,0])
for i,(name,mesh) in enumerate(sources.items()):
 n=f'cone_{i}'
 cut=tm.boolean.intersection([mesh,box(-50,-50,178,50,50,251)],engine='manifold')
 cut.apply_translation([0,0,-178]);parts[n]=cut
 states[name]={n:M.ravel().tolist()}
pickle.dump(parts,open(P/'figures/cone_cutaway_R9.pkl','wb'))
print(json.dumps(mm.run('render',files=[str(P/'figures/cone_cutaway_R9.pkl')],out=str(P/'preview_cone_R9'),colors={n:'#bd6f53' for n in parts},states=states,frames=24,status='콘 확대 — 실제 모델 z178 절단 · R9: 끝 접선45→30도·마지막4mm·바깥 채움'),ensure_ascii=False))
