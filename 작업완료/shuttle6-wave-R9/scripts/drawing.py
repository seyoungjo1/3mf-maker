"""Measured nominal sections and design dimensions, generated inside mm pipeline."""
from pathlib import Path
import pickle,json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties,fontManager
from matplotlib.backends.backend_pdf import PdfPages
PTH=Path(__file__).resolve().parent.parent
from build import P
parts=pickle.load(open(PTH/'parts_nominal.pkl','rb'))
shell=pickle.load(open(PTH/'assembled_shell.pkl','rb'))['shell']
contents=pickle.load(open(PTH/'content_envelopes.pkl','rb'))
f=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');fontManager.addfont(f.get_file())
plt.rcParams.update({'font.family':f.get_name(),'axes.unicode_minus':False,'pdf.fonttype':42})
out=PTH/'drawings';out.mkdir(exist_ok=True)
def section(ax,m,plane,at,color,label):
 n=np.zeros(3);n[plane]=1;o=np.zeros(3);o[plane]=at;keep=[i for i in range(3) if i!=plane]
 s=m.section(plane_origin=o,plane_normal=n)
 if s is not None:
  for i,e in enumerate(s.entities):
   p=s.vertices[e.points];ax.plot(p[:,keep[0]],p[:,keep[1]],color=color,lw=.8,label=label if i==0 else None)
 ax.set_aspect('equal');ax.grid(alpha=.2)
with PdfPages(out/'Shuttle6_C_도면_R9.pdf') as pdf:
 fig,axes=plt.subplots(1,2,figsize=(16.54,11.69));fig.suptitle('R9 · 몸통만 두 조각 접착 / 6개용 / 실제 공칭 메시 단면',fontsize=20)
 section(axes[0],parts['drawer'],0,0,'#b9684e','일체형 받침')
 section(axes[0],contents['contents'],0,0,'#777777','가정 셔틀콕 6개 외피')
 section(axes[0],contents['clearance'],0,0,'#4586a6','1.5mm 여유 외피')
 axes[0].set_title(f"끝 접선45→30° / 마지막 브리지{P['END_FINAL_BRIDGE_D']:.2f}mm / 바깥 채움");axes[0].legend()
 section(axes[1],shell,1,0,'#33383e','접착된 몸통')
 axes[1].axhline(121.5,color='#b9684e',ls='--',label='가로 분할121.5 / 턱 겹침10')
 axes[1].set_title('몸통 길이243 / 전체 닫힘253 / 폭82 / 뚜껑86');axes[1].legend()
 fig.text(.05,.035,'깃털Ø68·코르크Ø28·총길이85·피치28·6개 적층225mm를 가정한 외피입니다. 실물 브랜드 수납 검증 전.',fontsize=11)
 fig.tight_layout(rect=(0,.06,1,.94));pdf.savefig(fig);fig.savefig(out/'01_sections_R9.png',dpi=110);plt.close(fig)
 fig,axes=plt.subplots(1,2,figsize=(16.54,11.69));fig.suptitle('R9 · 접착부 / 스프링과 잠금부 / 출력 안내',fontsize=20)
 section(axes[0],parts['shell_lower'],2,125,'#33383e','접착 턱 외경78.8 / 내경76')
 section(axes[0],parts['shell_upper'],2,3.5,'#b9684e','상단 소켓 내경79.4')
 axes[0].set_title('접착 반경 틈0.30mm / 턱 두께1.4 / 길이10 / 슬라이드 내경76 유지');axes[0].legend()
 section(axes[1],parts['drawer'],1,0,'#b9684e','스프링 길이30.5·두께3·폭8')
 axes[1].set_xlim(30,45);axes[1].set_ylim(0,48);axes[1].set_title('누름1.5mm / 뿌리 아래3.5 / 별도 시험편 먼저');axes[1].legend()
 fig.text(.04,.07,'P1S 0.4 / PLA / 0.2층 / EFC0.15 / 브림10. 몸통 두 조각과 받침은 각각 세워 출력. 접착제는 바깥 턱에만 소량.',fontsize=11)
 fig.text(.04,.035,'저속 전역 설정: 외벽40·내벽60mm/s, 외벽 가속도600·기본1500mm/s². 높이별 감속이나 실제 슬라이싱 시간은 검증하지 않았습니다.',fontsize=10)
 fig.tight_layout(rect=(0,.11,1,.94));pdf.savefig(fig);fig.savefig(out/'02_joint_R9.png',dpi=110);plt.close(fig)
 fig,axes=plt.subplots(1,2,figsize=(16.54,11.69));fig.suptitle('R9 · 끝 곡면 접선30° / 마지막 브리지4mm / 출력 시험편',fontsize=20)
 section(axes[0],parts['drawer'],1,-.02,'#b9684e','실제 메시 단면 y=-0.02')
 roof=P['END_ACTUAL_ROOF_Z'];xx=np.array([1.6,3.2])
 axes[0].plot(xx,roof-np.tan(np.deg2rad(30))*(xx-2),'--',color='#4586a6',label='끝 접선30°(베드 기준)')
 axes[0].annotate('',xy=(2,roof-.06),xytext=(-2,roof-.06),arrowprops={'arrowstyle':'<->','color':'#33383e'})
 axes[0].text(-.6,roof-.22,'4.00mm',fontsize=12)
 axes[0].set_xlim(-3.5,3.5);axes[0].set_ylim(247.5,249.95);axes[0].set_title('입구부터45→30° 연속 곡률 → 폭4mm에서 곡면 종료');axes[0].legend(loc='lower left')
 section(axes[1],parts['tip_coupon'],1,-.02,'#b9684e','실제 받침 끝 z240~249.8 절단')
 axes[1].set_title('05플레이트: 같은 방향으로 세워 출력 / 높이9.8mm');axes[1].legend()
 measured=json.load(open(PTH/'dimensions.json'))['end_geometry']['measured_nominal_mesh_chord_from_bed_deg']
 fig.text(.05,.045,f'30도는 곡면 끝의 접선 경사입니다. 실제 마지막 메시 현 실측은{measured:.2f}도입니다. 입구45도부터 즉시 곡률이 시작되어 끝30도로 이어집니다.',fontsize=12)
 fig.tight_layout(rect=(0,.08,1,.94));pdf.savefig(fig);fig.savefig(out/'03_tip_macro_R9.png',dpi=120)
 fig.canvas.draw();extent=axes[0].get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted()).expanded(1.03,1.08)
 fig.savefig(out/'03_tip_detail_R9.png',dpi=150,bbox_inches=extent);plt.close(fig)

fig,ax=plt.subplots(figsize=(10,5))
section(ax,parts['drawer'],1,-.02,'#b9684e','실제 R9 메시 단면')
z0=P['END_ROUND_START_Z'];roof=P['END_ACTUAL_ROOF_Z']
for angle,r,z,c in [(45.,35.7,z0,'#4586a6'),(30.,2.,roof,'#52784f')]:
 x=np.array([r-3,r+3]);ax.plot(x,z-np.tan(np.deg2rad(angle))*(x-r),'--',color=c,label=f'{angle:.0f}° 접선(베드 기준)')
ax.annotate('4mm 브리지',xy=(0,roof),xytext=(8,roof+2),arrowprops={'arrowstyle':'->'})
ax.set_xlim(-1,39);ax.set_ylim(z0-3,251.8);ax.set_title('입구45°부터 바로 곡률 시작 → 끝30° / 직선 구간 없음');ax.legend(loc='lower left')
ax.set_xlabel('중심에서 거리(mm)');ax.set_ylabel('출력 높이(mm)');fig.tight_layout();fig.savefig(out/'04_full_curve_R9.png',dpi=150);plt.close(fig)
