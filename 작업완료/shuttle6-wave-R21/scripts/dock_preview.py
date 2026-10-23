from pathlib import Path
import pickle,trimesh as tm,numpy as np
from trimesh.transformations import translation_matrix as T, rotation_matrix as R
from detail_renderer import render_safe
O=Path(__file__).resolve().parent.parent;p=pickle.load(open(O/'parts_nominal.pkl','rb'))
def crop(m,z0,z1):
 b=tm.creation.box([110,110,z1-z0]);b.apply_translation([0,0,(z0+z1)/2]);return tm.boolean.intersection([m,b],engine='manifold')
body=crop(p['shell_lower'],0,12);rear=crop(p['drawer'],238,250);rear.apply_transform(T([0,0,253])@R(np.pi,[0,1,0]));G=T([128,128,0])
states={'외관 안쪽 반원 홈':{'body':G},'반원 뒤끝 분리':{'body':G,'rear':G@T([0,0,22])},'4.1mm 삽입·여유0.2mm':{'body':G,'rear':G}}
render_safe({'body':body,'rear':rear},str(O/'preview_dock'),colors={'body':'#37474f','rear':'#bd6f53'},states={k:{n:m.ravel().tolist() for n,m in st.items()} for k,st in states.items()},frames=24,status='R21 실제 메시 확대 · 앞쪽을 잘라 내부 표시 · 안쪽 반원 받침 / 입구0.35·자리0.2mm / 이탈방지는 별도 양옆 레일')
