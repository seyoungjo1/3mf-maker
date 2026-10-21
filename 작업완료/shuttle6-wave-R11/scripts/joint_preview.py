"""Actual glue-joint cutaway, inspected and rendered via the frozen mm API."""
from pathlib import Path
import json,sys,pickle,numpy as np,trimesh
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
p=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(p.parent.parent/'tools'));sys.path.insert(0,str(p/'scripts'))
import mm
from build import P
report=json.load(open(p/'qc/review_R11/report.json'));assert not report['warn']
# Deliberate sectional illustration: full models remain untouched.
files=[]
for name,b in [('shell_lower',[-50,-50,118,50,50,136]),('shell_upper',[-50,-50,0,50,50,20])]:
 out=p/'figures'/f'{name}_joint_cutaway.stl'
 mm.run('crop',file=str(p/'parts_nominal.pkl')+':'+name,box=b,out=str(out))
 files.append(out)
meshes={n:trimesh.load_mesh(f,process=False) for n,f in zip(['하부_강조','상부'],files)}
# Both crop bounds share the same full outer profile. Normalization preservesXYalignment.
pickle.dump(meshes,open(p/'joint_preview.pkl','wb'))
turn=R(-np.pi/2,[0,0,1]);base=T([-39.1,-39.1,0])
states={}
for label,dz in [('분리',30),('맞물림',0)]:
 states[label]={'하부_강조':(turn@base).ravel().tolist(),'상부':(turn@T([0,0,3.5+dz])@base).ravel().tolist()}
res=mm.run('render',files=[str(p/'joint_preview.pkl')],out=str(p/'preview_joint_R11'),colors={'하부_강조':'#bd6f53','상부':'#33383e'},states=states,frames=24,status='실제 형상 절단 확대 — 하부는 설명용 강조색 / 키·홈 폭8mm / 접착턱14mm')
print(json.dumps(res,ensure_ascii=False))
