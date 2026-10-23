from pathlib import Path
import pickle,numpy as np,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties,fontManager
from matplotlib.path import Path as MP
from matplotlib.patches import PathPatch
from shapely.geometry import Polygon
from shapely import make_valid
from shapely.geometry.polygon import orient
O=Path(__file__).resolve().parent.parent
f=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');fontManager.addfont(f.get_file());plt.rcParams.update({'font.family':f.get_name(),'axes.unicode_minus':False})
p=pickle.load(open(O/'parts_nominal.pkl','rb'));old=pickle.load(open(O/'AS/reference_R20_parts.pkl','rb'))
def section(m,z):
 s=m.section(plane_origin=[0,0,z],plane_normal=[0,0,1]);g=None
 for a in s.discrete:
  q=make_valid(Polygon(a[:,:2]));g=q if g is None else g.symmetric_difference(q)
 return g

def paint(ax,g,c):
 for q in ([g] if g.geom_type=='Polygon' else g.geoms):
  if q.geom_type!='Polygon':continue
  q=orient(q,1);paths=[]
  for ring in [q.exterior,*q.interiors]:
   v=np.array(ring.coords);codes=np.full(len(v),MP.LINETO);codes[0]=MP.MOVETO;codes[-1]=MP.CLOSEPOLY;paths.append(MP(v,codes))
  ax.add_patch(PathPatch(MP.make_compound_path(*paths),facecolor=c,edgecolor=c,lw=.6))
fig,axs=plt.subplots(1,3,figsize=(15,5.5))
for ax,limits in zip(axs,[(-42,42,-42,42),(-12,12,-39,-32),(30,40,-11,11)]):
 paint(ax,section(old['shell_lower'],60),'#e7a58b');paint(ax,section(p['shell_lower'],60),'#37474f');ax.set_xlim(*limits[:2]);ax.set_ylim(*limits[2:]);ax.set_aspect('equal');ax.grid(alpha=.2);ax.set_xlabel('X (mm)');ax.set_ylabel('Y (mm)')
axs[0].set_title('실제 외관 단면 · 몸통 Z60mm')
axs[1].set_title('아래쪽 벽: 4.00 → 2.91mm')
axs[2].set_title('옆 레일 벽은 기존 두께 유지')
fig.suptitle('R21 외관 얇게 수정 — 살구색: 이전 외곽 / 진회색: 수정 후\n수납 내면 유지 · 접합·잠금·레일 부위 두께 보존',fontsize=14)
fig.tight_layout();fig.savefig(O/'drawings/housing_thickness_comparison.png',dpi=150,bbox_inches='tight')
