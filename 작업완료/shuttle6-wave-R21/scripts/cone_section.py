from pathlib import Path
import pickle,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties,fontManager
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
from shapely import make_valid
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
O=Path(__file__).resolve().parent.parent
f=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');fontManager.addfont(f.get_file());plt.rcParams.update({'font.family':f.get_name(),'axes.unicode_minus':False})
p=pickle.load(open(O/'parts_nominal.pkl','rb'));g=pickle.load(open(O/'contents.pkl','rb'))['contents']
def material(mesh,axial=False):
 s=mesh.section(plane_origin=([0,0,5.] if axial else [.2,0,0]),plane_normal=([0,0,1] if axial else [1,0,0]));result=None
 for loop in s.discrete:
  poly=make_valid(Polygon(loop[:,[0,1]] if axial else loop[:,[2,1]]));result=poly if result is None else result.symmetric_difference(poly)
 return result
def paint(ax,geom,color,edge):
 for poly in ([geom] if geom.geom_type=='Polygon' else geom.geoms):
  if poly.geom_type!='Polygon':continue
  poly=orient(poly,1);paths=[]
  for ring in [poly.exterior,*poly.interiors]:
   v=np.array(ring.coords);codes=np.full(len(v),MPath.LINETO);codes[0]=MPath.MOVETO;codes[-1]=MPath.CLOSEPOLY;paths.append(MPath(v,codes))
  ax.add_patch(PathPatch(MPath.make_compound_path(*paths),facecolor=color,edgecolor=edge,lw=1.1))
drawer=material(p['drawer']);cap=material(p['cap']);gauge=material(g)
fig=plt.figure(figsize=(14,12));grid=fig.add_gridspec(3,2,height_ratios=[1.1,1.2,1.2]);axs=[fig.add_subplot(grid[0,:]),fig.add_subplot(grid[1,0]),fig.add_subplot(grid[1,1])]
for ax in axs:
 ax.set_facecolor('#f8f5ef');paint(ax,drawer,'#bd6f53','#77402e');paint(ax,cap,'#dfac8e','#77402e');paint(ax,gauge,'#fffdf5','#777777');ax.set_aspect('equal');ax.grid(alpha=.18);ax.set_xlabel('내관 길이 방향 Z (mm)');ax.set_ylabel('높이 Y (mm)')
axs[0].set(xlim=(-2,253),ylim=(-42,45),title='R21 실제 메시 단면 — 왼쪽: 뚜껑·코르크 / 오른쪽: 깃털·뒤컵')
axs[0].annotate('기존 갓을 앞쪽으로 이동',xy=(20,-22),xytext=(46,-40),arrowprops={'arrowstyle':'->'},color='#8c3e23')
axs[0].annotate('뒤쪽은 열린 반원 · 콘 없음',xy=(238,-31),xytext=(145,-40),arrowprops={'arrowstyle':'->'},color='#135c77')
axs[1].set(xlim=(0,60),ylim=(-39,25),title='앞쪽 확대: 기존 갓 단면 그대로 이동')
axs[1].annotate('기존 갓 형상 · 윗면은 열림',xy=(16,-12),xytext=(4,19),arrowprops={'arrowstyle':'->'},fontsize=10)
axs[1].axvline(10,color='#8c3e23',ls=':',alpha=.5);axs[1].axvline(24.8,color='#8c3e23',ls=':',alpha=.5)
axs[2].set(xlim=(210,270),ylim=(-40,45),title='뒤쪽 확대: 열린 반원 마감 · 두께5.8mm')
axs[2].axvline(238,color='#1683a2',ls='--');axs[2].axvline(244,color='#1683a2',ls='--')
axs[2].annotate('',xy=(238,39),xytext=(244,39),arrowprops={'arrowstyle':'<->','color':'#135c77'})
axs[2].text(241,41,'6mm',ha='center',color='#135c77',fontsize=11)
axs[2].annotate('깃털 끝',xy=(238,27),xytext=(212,31),arrowprops={'arrowstyle':'->'},fontsize=10)
axs[2].annotate('반원 벽 Z244',xy=(244,-8),xytext=(247,19),arrowprops={'arrowstyle':'->'},fontsize=10)
rear=p['drawer'].copy();rear.apply_transform(T([0,0,253])@R(np.pi,[0,1,0]))
seat=material(p['shell_lower'],True);end=material(rear,True)
for index,title in [(0,'외관 맨 안쪽 반원 홈에 들어간 실제 단면 (몸통Z5mm)'),(1,'접합부 확대 · 실제 여유0.2mm (가로·세로 축척 다름)')]:
 ax=fig.add_subplot(grid[2,index]);ax.set_facecolor('#f8f5ef');paint(ax,seat,'#37474f','#263238');paint(ax,end,'#bd6f53','#77402e');ax.grid(alpha=.2)
 if index==0:ax.set_aspect('equal');ax.set_xlim(-43,43);ax.set_ylim(-43,43)
 else:
  ax.set_xlim(-12,12);ax.set_ylim(-.6,.7);ax.annotate('',xy=(0,0),xytext=(0,.2),arrowprops={'arrowstyle':'<->','color':'#1683a2'});ax.text(1,.09,'0.2mm',color='#1683a2',fontsize=11)
 ax.set_title(title,fontsize=11);ax.set_xlabel('X (mm)');ax.set_ylabel('Y (mm)')
fig.suptitle('R21 실제 메시 단면 — 앞쪽 갓 / 두꺼운 반원 뒤끝 / 외관 반원 받침 홈',fontsize=14)
fig.tight_layout();(O/'drawings').mkdir(exist_ok=True);fig.savefig(O/'drawings/cone_actual_section.png',dpi=150,bbox_inches='tight')
