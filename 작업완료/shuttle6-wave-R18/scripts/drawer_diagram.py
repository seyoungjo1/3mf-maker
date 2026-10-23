from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon
from matplotlib.font_manager import FontProperties,fontManager
O=Path(__file__).resolve().parent.parent;f=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');fontManager.addfont(f.get_file());plt.rcParams.update({'font.family':f.get_name(),'axes.unicode_minus':False})
fig,axs=plt.subplots(2,1,figsize=(13,6.7));fig.patch.set_facecolor('#f6f3ed')
for ax,travel in zip(axs,[0,225]):
 ax.set_facecolor('#f6f3ed');ax.add_patch(Rectangle((0,-39.1),243,78.2,fc='#33383e',alpha=.16,ec='#33383e',lw=2))
 # Nominal coordinates: rear end3.2+travel; front end249.8+travel.
 ax.add_patch(Rectangle((3.2+travel,-34.6),246.6,69.2,fc='#bd6f53',alpha=.34,ec='#a05b44',lw=1.5))
 ax.add_patch(Rectangle((3.2+travel,-34.6),14.8,69.2,fc='#bd6f53',alpha=.55))
 ax.add_patch(Rectangle((243+travel,-41.1),10,82.2,fc='#bd6f53',ec='#a05b44',lw=1.5))
 for sign in [-1,1]:
  ya,yb=sorted([sign*34.8,sign*39.1]);ax.add_patch(Rectangle((236,ya),4,yb-ya,fc='#4b9eba',ec='#186079',lw=1.2))
  ya,yb=sorted([sign*32.5,sign*36.8]);ax.add_patch(Rectangle((4.2+travel,ya),6.8,yb-ya,fc='#db6037',ec='#8f321d',lw=1.2))
 ax.annotate('',xy=(218.4+travel,8),xytext=(247+travel,8),arrowprops={'arrowstyle':'-|>','color':'#c69300','lw':5})
 ax.text(247+travel,17,'축: 뚜껑',ha='center',fontsize=10)
 ax.text(218.4+travel,-15,'클립 걸림: 몸통 방향',ha='center',fontsize=9)
 ax.set_title('닫힘' if travel==0 else '서랍처럼225mm 인출 — 뒤컵 양옆의 고정 어깨가 입구 양옆 블록에 걸림',fontsize=13,loc='left')
 if travel:
  ax.annotate('외관 입구',xy=(243,39),xytext=(285,65),arrowprops={'arrowstyle':'->'},fontsize=11)
  ax.annotate('양쪽 멈춤블록(파랑)\n양쪽 고정 어깨(주황)',xy=(237,35.7),xytext=(130,67),arrowprops={'arrowstyle':'->'},fontsize=11)
  ax.annotate('뒤컵: 뚜껑 반대 끝',xy=(235,0),xytext=(115,-75),arrowprops={'arrowstyle':'->'},fontsize=11)
  ax.annotate('',xy=(450,-62),xytext=(330,-62),arrowprops={'arrowstyle':'->','lw':2});ax.text(390,-80,'당기는 방향',ha='center',fontsize=11)
 ax.set_aspect('equal');ax.set_xlim(-5,495);ax.set_ylim(-90,90);ax.axis('off')
fig.suptitle('좌우 걸림 구조 · 바닥에는 이탈 방지턱 없음',fontsize=17);fig.tight_layout()
(O/'drawings').mkdir(exist_ok=True);fig.savefig(O/'drawings/drawer_side_stops.png',dpi=140,bbox_inches='tight')
