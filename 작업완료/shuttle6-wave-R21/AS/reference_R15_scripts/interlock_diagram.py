"""Unwrapped actual male/female edge profile, displayed separated for clarity."""
from pathlib import Path
import sys,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties,fontManager
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'scripts'))
from build import P
from rail_geometry import seam_from_s,joint_row
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');fontManager.addfont(font.get_file());plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False})
x=np.linspace(0,P['PATTERN_PITCH']*2.1,2500);cy,_,r=joint_row();y=seam_from_s(x)-cy
fig,axs=plt.subplots(2,1,figsize=(10,6),sharex=True)
for ax,offset in zip(axs,[6,.1]):
 ax.fill_between(x,-5,y-.05,color='#bd6f53',label='아래통: 돌출된 물결 숫형')
 ax.fill_between(x,y+.05+offset,r+offset+7,color='#33383e',label='위통 아래: 대응 물결 암홈')
 ax.plot(x,y-.05,color='#854b38',lw=2);ax.plot(x,y+.05+offset,color='#111111',lw=2)
 ax.set_aspect('equal');ax.axis('off')
axs[0].set_title('몸통 둘레를 펼친 실제 결합 윤곽 / 두 파트 분리',fontsize=14);axs[0].legend(loc='upper center',fontsize=10,ncol=2)
axs[1].set_title('맞물린 상태 — 물결 돌기가 위통의 음각에 들어감',fontsize=14)
fig.tight_layout();fig.savefig(p/'drawings/00_actual_male_female_wave_R15.png',dpi=140)
