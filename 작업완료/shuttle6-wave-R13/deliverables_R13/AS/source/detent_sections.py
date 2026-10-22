"""Actual longitudinal six-row section, with one engaged cam enlarged."""
from pathlib import Path
import sys,pickle
import numpy as np
from trimesh.transformations import rotation_matrix as R,translation_matrix as T
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties,fontManager
PTH=Path(__file__).resolve().parent.parent
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
fontManager.addfont(font.get_file());plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False})
parts=pickle.load(open(PTH/'parts_nominal.pkl','rb'))
shell=pickle.load(open(PTH/'assembled_shell.pkl','rb'))['shell']
shell.apply_transform(T([0,0,253.])@R(np.pi,[0,1,0]))
fig,axes=plt.subplots(1,2,figsize=(9,11),gridspec_kw={'width_ratios':[1,1.3]})
for ax in axes:
 for name,mesh,color in [('외관',shell,'#33383e'),('내관',parts['drawer'],'#bd6f53')]:
  sec=mesh.section(plane_origin=[0,-5,0],plane_normal=[0,1,0])
  for i,e in enumerate(sec.entities):
   v=sec.vertices[e.points];ax.plot(v[:,0],v[:,2],color=color,lw=1.5,label=name if i==0 else None)
 ax.grid(alpha=.2);ax.set_aspect('equal');ax.set_xlabel('X mm');ax.set_ylabel('길이 Z mm')
axes[0].set_xlim(-42,42);axes[0].set_ylim(250,5);axes[0].legend(loc='lower center')
axes[0].set_title('양옆6행 · 36mm 간격\n얇은 절개 혀 없음')
for i,z in enumerate([20,56,92,128,164,200],1):axes[0].text(0,z,str(i),ha='center',va='center',fontsize=12)
axes[1].set_xlim(30,37);axes[1].set_ylim(16,24)
axes[1].set_title('한 곳 확대 · 낮고 넓은 둥근 캠\n홈 표면 여유0.2mm / 모벽2.6mm 유지')
fig.tight_layout();fig.savefig(PTH/'drawings/08_six_detent_longitudinal_R13.png',dpi=150);plt.close(fig)
