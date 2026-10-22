"""Actual additive-cradle meshes: underside, chamber, channel and six positions."""
from pathlib import Path
import sys,pickle,json
import numpy as np
import trimesh as tm
from trimesh.transformations import rotation_matrix as R,translation_matrix as T
PTH=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(PTH/'scripts'));sys.path.insert(0,str(PTH.parent.parent/'tools'))
from build import P,box
import mm

def main():
 parts=pickle.load(open(PTH/'parts_nominal.pkl','rb'));shell=pickle.load(open(PTH/'assembled_shell.pkl','rb'))['shell']
 closed=T([0,0,P['CLOSED_L']])@R(np.pi,[0,1,0])
 cut=tm.boolean.intersection([shell,box(-50,-50,-1,50,0,250)],engine='manifold')
 G=T([100,255,45])@R(np.pi/2,[1,0,0])
 under=T([100,10,45])@R(-np.pi/2,[1,0,0])
 objects={'절개외관':cut,'내관':parts['drawer'],'뚜껑':parts['cap']}
 pickle.dump(objects,open(PTH/'figures/rail_cutaway.pkl','wb'))
 states={'외관 레일 안의6단 홈':{'절개외관':G.ravel().tolist()},
         '내관 원형 공간 그대로':{'내관':(G@closed).ravel().tolist()},
         '내관 바깥 받침·레일 돌기':{'내관':(under@closed).ravel().tolist()}}
 for i,d in enumerate([0,36,72,108,144,180]):
  states[f'{i+1}단 위치 · 인출{d}mm']={'절개외관':G.ravel().tolist(),'내관':(G@T([0,0,d])@closed).ravel().tolist(),'뚜껑':(G@T([0,0,d])@closed).ravel().tolist()}
 r=mm.run('render',files=[str(PTH/'figures/rail_cutaway.pkl')],out=str(PTH/'preview_rail_R14'),states=states,
          colors={'절개외관':'#33383e','내관':'#bd6f53','뚜껑':'#bd6f53'},frames=45,
          status='R14 · 내부 원형64 유지 · 바깥 덧붙임 받침 · 레일 속6단 · 실물 힘·수명 미검증')
 json.dump(r,open(PTH/'qc/rail_render_R14.json','w'),ensure_ascii=False,indent=1)
 print('Rendered external cradle and circular chamber')

if __name__=='__main__':main()
