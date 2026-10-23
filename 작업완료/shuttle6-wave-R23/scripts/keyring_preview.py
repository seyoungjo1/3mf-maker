from pathlib import Path
import pickle,sys,numpy as np,trimesh as tm
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
O=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(O.parents[1]/'tools'))
from detail_renderer import render_safe as render
p=pickle.load(open(O/'parts_nominal.pkl','rb'));up=p['shell_upper'].copy();up.apply_translation([0,0,121.5])
box=tm.creation.box([120,140,8]);box.apply_translation([0,-5,239]);cut=tm.boolean.intersection([up,box],engine='manifold')
cap=p['cap'].copy();cap.apply_transform(T([0,0,253])@R(np.pi,[0,1,0]))
H=T([128,130,243])@R(np.pi,[0,0,1])@R(np.pi,[1,0,0]);parts={'upper_cut':cut,'cap':cap}
states={'Ø5 고리·출력 바닥면':{'upper_cut':H},'닫힌 뚜껑과 고리':{'upper_cut':H,'cap':H}}
# Closed assembly is lifted for presentation only so the cap is above the bed.
states['닫힌 뚜껑과 고리']={n:T([0,0,14])@v for n,v in states['닫힌 뚜껑과 고리'].items()}
render(parts,str(O/'preview_keyring'),colors={'upper_cut':'#33383e','cap':'#bd6f53'},states={k:{n:m.ravel().tolist() for n,m in v.items()} for k,v in states.items()},frames=20,status='완료 — Ø5mm 관통홀 · 고리 두께4mm · 둘레 살4mm · 위통과 함께 베드 안착 / 관찰용 몸통 절개')
