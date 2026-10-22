"""Actual mesh sections and cutaway GIF for the flat rail and six detent rows."""
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
 parts=pickle.load(open(PTH/'parts_nominal.pkl','rb'))
 shell=pickle.load(open(PTH/'assembled_shell.pkl','rb'))['shell']
 closed=T([0,0,P['CLOSED_L']])@R(np.pi,[0,1,0])
 tray=parts['drawer'].copy();tray.apply_transform(closed)
 cross={'외관':shell,'내관':tray}
 pickle.dump(cross,open(PTH/'figures/rail_closed.pkl','wb'))
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.font_manager import FontProperties,fontManager
 font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
 fontManager.addfont(font.get_file())
 matplotlib.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False})
 fig,axs=plt.subplots(1,2,figsize=(12,6))
 for ax in axs:
  for name,m in cross.items():
   section=m.section(plane_origin=[0,0,100],plane_normal=[0,0,1])
   for j,e in enumerate(section.entities):
    v=section.vertices[e.points]
    ax.plot(v[:,0],v[:,1],color={'외관':'#33383e','내관':'#bd6f53'}[name],lw=1.5,label=name if j==0 else None)
  ax.grid(alpha=.2);ax.set_aspect('equal');ax.set_xlabel('X mm');ax.set_ylabel('Y mm')
 axs[0].set_title('실제 조립 단면 · 외관 안쪽 아래 한쪽 평면');axs[0].legend()
 axs[1].set_xlim(-15,15);axs[1].set_ylim(-35,-28)
 axs[1].set_title('바닥 레일 확대 · 간격0.30mm / 내관 두께2.60mm')
 axs[1].annotate('0.30mm',xy=(0,-32.75),xytext=(3,-34.1),arrowprops={'arrowstyle':'->'})
 fig.tight_layout();fig.savefig(PTH/'drawings/07_internal_flat_rail_R13.png',dpi=150);plt.close(fig)
 # Remove upper half of shell only, exposing its actual lower flat and recesses.
 cut=tm.boolean.intersection([shell,box(-50,-50,-1,50,0,250)],engine='manifold')
 G=T([100,255,45])@R(np.pi/2,[1,0,0])
 objects={'절개외관':cut,'내관':parts['drawer'],'뚜껑':parts['cap']}
 pickle.dump(objects,open(PTH/'figures/rail_cutaway.pkl','wb'))
 states={'외관 내부 레일·6쌍 홈':{'절개외관':G.ravel().tolist()},
         '내관의 낮은 돌기6쌍':{'내관':(G@closed).ravel().tolist()}}
 for i,d in enumerate([0,36,72,108,144,180]):
  states[f'{i+1}단 위치 · 인출{d}mm']={'절개외관':G.ravel().tolist(),
                                      '내관':(G@T([0,0,d])@closed).ravel().tolist(),
                                      '뚜껑':(G@T([0,0,d])@closed).ravel().tolist()}
 result=mm.run('render',files=[str(PTH/'figures/rail_cutaway.pkl')],out=str(PTH/'preview_rail_R13'),
               states=states,colors={'절개외관':'#33383e','내관':'#bd6f53','뚜껑':'#bd6f53'},frames=40,
               status='R13 절개 표시 · 외관 아래 평면레일 · 양옆6단 · 실물 딸깍 힘·반복수명 미검증')
 json.dump(result,open(PTH/'qc/rail_render_R13.json','w'),ensure_ascii=False,indent=1)
 print(result)

if __name__=='__main__':main()
