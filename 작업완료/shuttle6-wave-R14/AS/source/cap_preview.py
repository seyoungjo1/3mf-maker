"""Render actual cap pocket and boat nose through the standard mm API."""
from pathlib import Path
import sys,pickle,json,numpy as np
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p.parent.parent/'tools'));import mm
parts=pickle.load(open(p/'parts_nominal.pkl','rb'))
cut=p/'figures/boat_nose_cutaway.stl'
mm.run('crop',file=str(p/'parts_nominal.pkl')+':drawer',box=[-50,-50,-1,50,50,32],out=str(cut),offset=parts['drawer'].bounds[0].tolist())
front=next(iter(mm.load_any(str(cut)).values()))
pickle.dump({'cap':parts['cap'],'boat_nose':front},open(p/'cap_preview.pkl','wb'))
states={'반원4mm·사각30mm':{'cap':T([-50,0,0]).ravel().tolist(),'boat_nose':(T([50,0,32])@R(np.pi,[0,1,0])).ravel().tolist()},'딸깍 조립':{'cap':np.eye(4).ravel().tolist(),'boat_nose':np.eye(4).ravel().tolist()}}
print(json.dumps(mm.run('render',files=[str(p/'cap_preview.pkl')],out=str(p/'preview_cap_R14'),colors={'cap':'#bd6f53','boat_nose':'#bd6f53'},states=states,frames=24,status='뚜껑 반원 포켓4mm + 안쪽30×30×3mm 사각 포켓 / 내관2.6mm / 보호된 딸깍 키'),ensure_ascii=False))
