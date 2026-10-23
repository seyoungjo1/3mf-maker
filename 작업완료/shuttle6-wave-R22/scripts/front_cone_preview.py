from pathlib import Path
import pickle,numpy as np,trimesh as tm
from trimesh.transformations import translation_matrix as T
from detail_renderer import render_safe
O=Path(__file__).resolve().parent.parent;p=pickle.load(open(O/'parts_nominal.pkl','rb'))
b=tm.creation.box([100,100,34]);b.apply_translation([0,0,17]);front=tm.boolean.intersection([p['drawer'],b],engine='manifold');front.apply_translation([0,0,-10])
render_safe({'front':front},str(O/'preview_front_cone'),colors={'front':'#bd6f53'},states={'앞콘 전체 원형 · 실제 내관 앞부분':{'front':T([128,128,0]).ravel().tolist()}},frames=24,status='R22 앞쪽 콘은 원형 전체 · 뒤쪽 반원과 외관은 R21 유지 · 실제 메시를 앞쪽34mm에서 잘라 확대')
