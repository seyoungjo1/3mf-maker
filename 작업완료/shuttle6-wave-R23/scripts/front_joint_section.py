from pathlib import Path
import pickle,numpy as np
import cone_section as sec
from shapely.geometry import Polygon
from shapely import make_valid
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent.parent;p=pickle.load(open(O/'parts_nominal.pkl','rb'))
def cross(m):
 s=m.section(plane_origin=[0,0,8.],plane_normal=[0,0,1]);g=None
 for loop in s.discrete:
  q=make_valid(Polygon(loop[:,:2]));g=q if g is None else g.symmetric_difference(q)
 return g
fig,axs=plt.subplots(1,2,figsize=(12,6.7))
for ax in axs:ax.set_facecolor('#f8f5ef');ax.set_aspect('equal');ax.grid(alpha=.2)
sec.paint(axs[0],cross(p['cap']),'#dfac8e','#77402e');sec.paint(axs[0],cross(p['drawer']),'#bd6f53','#77402e');axs[0].set(xlim=(-44,44),ylim=(-44,53),xlabel='X (mm)',ylabel='Y (mm)',title='실제 결합 단면 Z8mm · 원형 홈과 원형 뿌리')
axs[0].annotate('둘레 여유0.2mm',xy=(0,34.7),xytext=(-25,45),arrowprops={'arrowstyle':'->'},fontsize=10)
sec.paint(axs[1],sec.cap,'#dfac8e','#77402e');sec.paint(axs[1],sec.drawer,'#bd6f53','#77402e');axs[1].set(xlim=(0,32),ylim=(-40,44),xlabel='길이 Z (mm)',ylabel='높이 Y (mm)',title='실제 길이 단면 · 앞콘 원형 뿌리를 뚜껑 속으로')
axs[1].axvline(6,color='#1683a2',ls='--',lw=.7);axs[1].axvline(6.2,color='#1683a2',ls=':',lw=.7)
axs[1].annotate('홈 바닥 Z6\n끼움부 시작 Z6.2',xy=(6.2,25),xytext=(15,35),arrowprops={'arrowstyle':'->'},fontsize=9)
axs[1].annotate('원형 뿌리 약5.05mm 두께',xy=(8.7,0),xytext=(10,-38),arrowprops={'arrowstyle':'->'},fontsize=9)
fig.suptitle('R23 — 뚜껑도 원형으로 파고 앞콘 둘레 전체를 끼움\n삽입3.8mm · 반경/끝바닥 여유0.2mm · 뒤끝 반원 유지',fontsize=14)
fig.tight_layout();fig.savefig(O/'drawings/front_cap_joint_actual_section.png',dpi=150,bbox_inches='tight')
