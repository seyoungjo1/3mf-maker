from pathlib import Path
import pickle,numpy as np,trimesh as tm
from trimesh.transformations import translation_matrix as T
from detail_renderer import render_safe
O=Path(__file__).resolve().parent.parent;p=pickle.load(open(O/'parts_nominal.pkl','rb'))
b=tm.creation.box([100,110,34]);b.apply_translation([0,5,17]);front=tm.boolean.intersection([p['drawer'],b],engine='manifold');G=T([128,128,0])
states={'뚜껑 전체 원형 홈':{'cap':G},'원형 끼움부 분리':{'cap':G,'front':G@T([0,0,35])},'원형 뿌리3.8mm 끼움':{'cap':G,'front':G}}
render_safe({'front':front,'cap':p['cap']},str(O/'preview_front_cone'),colors={'front':'#bd6f53','cap':'#d6a88d'},states={k:{n:m.ravel().tolist() for n,m in v.items()} for k,v in states.items()},frames=24,status='R23 실제 메시 · 뚜껑 원형 홈 / 원형 뿌리3.8mm 삽입 / 반경·끝바닥 여유0.2mm / 앞쪽34mm 확대')
