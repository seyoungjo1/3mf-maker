from pathlib import Path
import pickle,json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties,fontManager
from matplotlib.backends.backend_pdf import PdfPages
PTH=Path(__file__).resolve().parent.parent
from build import P
parts=pickle.load(open(PTH/'parts_nominal.pkl','rb'));shell=pickle.load(open(PTH/'assembled_shell.pkl','rb'))['shell']
f=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');fontManager.addfont(f.get_file())
plt.rcParams.update({'font.family':f.get_name(),'axes.unicode_minus':False,'pdf.fonttype':42})
out=PTH/'drawings';out.mkdir(exist_ok=True)
def section(ax,m,plane,at,color,label):
 n=np.zeros(3);n[plane]=1;o=np.zeros(3);o[plane]=at;keep=[i for i in range(3) if i!=plane]
 s=m.section(plane_origin=o,plane_normal=n)
 if s is not None:
  for i,e in enumerate(s.entities):
   p=s.vertices[e.points];ax.plot(p[:,keep[0]],p[:,keep[1]],color=color,lw=.9,label=label if i==0 else None)
 ax.set_aspect('equal');ax.grid(alpha=.2)
with PdfPages(out/'Shuttle6_C_도면_R12.pdf') as pdf:
 fig,ax=plt.subplots(figsize=(10,7));section(ax,parts['drawer'],2,100,'#b9684e','내관: Ø64 공칭 개방부 / 아래 평면')
 ax.plot([-32,32],[0,0],'--',color='#4586a6');ax.text(-8,2,'Ø64mm',fontsize=14)
 ax.plot([-11.593,11.593],[-32.6,-32.6],color='#52784f',lw=3,label='바닥 평면 폭 약23mm')
 ax.annotate('바닥 두께2.6mm',xy=(0,-31.3),xytext=(4,-23),arrowprops={'arrowstyle':'->'})
 ax.set_xlim(-39,39);ax.set_ylim(-36,8);ax.set_title('R12 내관 단면 · 열린 반원 + 평평한 바닥');ax.legend(loc='upper right')
 fig.tight_layout();pdf.savefig(fig);fig.savefig(out/'01_ID64_flat_bottom_R12.png',dpi=140);plt.close(fig)
 fig,axes=plt.subplots(1,2,figsize=(13,7));section(axes[0],parts['cap'],2,8,'#33383e','반원 전체 포켓');section(axes[0],parts['drawer'],2,8,'#b9684e','속이 찬 반원 끼움부')
 axes[0].set_title('반원 포켓4mm + 안쪽 사각 딸깍 결합');axes[0].legend()
 section(axes[1],parts['drawer'],1,-1.5,'#b9684e','내관 바깥 돌기')
 # Compare the matching shell in the actual canonical closed coordinate frame.
 sh=shell.copy();from trimesh.transformations import translation_matrix as T,rotation_matrix as R
 sh.apply_transform(T([0,0,253])@R(np.pi,[0,1,0]));section(axes[1],sh,1,-1.5,'#33383e','외관 안쪽 홈')
 axes[1].set_xlim(29,40);axes[1].set_ylim(15,25);axes[1].set_title('긴 클립 없음 · 둥근 돌기와 홈으로 딸깍');axes[1].legend(loc='lower left')
 fig.tight_layout();pdf.savefig(fig);fig.savefig(out/'02_cap_and_detent_R12.png',dpi=140)
 fig.canvas.draw();extent=axes[1].get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted()).expanded(1.08,1.08);fig.savefig(out/'03_detent_detail_R12.png',dpi=160,bbox_inches=extent);plt.close(fig)
 fig,axes=plt.subplots(1,2,figsize=(13,7));printed=pickle.load(open(PTH/'parts.pkl','rb'))
 section(axes[0],printed['drawer'],2,1,'#b9684e','실제 눕힘 출력 메시')
 axes[0].set_title('긴 내관은 대각선으로 눕힘 / 큰 뚜껑 별도');axes[0].legend()
 section(axes[1],parts['drawer'],1,-.02,'#b9684e','마지막 콘 곡면');axes[1].set_xlim(-35,35);axes[1].set_ylim(220,251);axes[1].set_title('기존 콘45→30°와 끝4mm 형상 유지')
 fig.tight_layout();pdf.savefig(fig);fig.savefig(out/'04_horizontal_and_tip_R12.png',dpi=130);plt.close(fig)


 fig,axes=plt.subplots(1,2,figsize=(13,7))
 upper=parts['shell_upper'].copy();upper.apply_translation([0,0,P['BODY_SPLIT_Z']])
 for ax in axes:
  section(ax,parts['shell_lower'],2,P['BODY_SPLIT_Z']+7,'#b9684e','하부: 끼움턱 + 돌출 키')
  section(ax,upper,2,P['BODY_SPLIT_Z']+7,'#33383e','상부: 맞춤 소켓 + 키 홈')
 axes[0].set_title('외관 두 조각 실제 결합 단면 / 키45° 한 곳');axes[0].legend(loc='lower left')
 axes[1].set_xlim(21,32);axes[1].set_ylim(21,32);axes[1].set_title('키 폭8mm / 양옆 틈0.10mm')
 axes[1].text(21.3,21.3,'접착턱 길이14mm · 벽2.2mm\n원형부 한쪽 틈0.15mm · 맞닿는 어깨턱',fontsize=10)
 fig.tight_layout();pdf.savefig(fig);fig.savefig(out/'05_keyed_glue_joint_R12.png',dpi=160);plt.close(fig)


 fig,axes=plt.subplots(1,2,figsize=(13,7))
 section(axes[0],parts['cap'],2,4.5,'#33383e','뚜껑:30×30 사각 포켓')
 section(axes[0],parts['drawer'],2,4.5,'#b9684e','내관:29.6 사각 키·탄성 턱')
 axes[0].set_xlim(-21,21);axes[0].set_ylim(-34,4);axes[0].set_title('반원 포켓 안쪽 사각 포켓 한 변30mm');axes[0].legend(loc='upper right',fontsize=9)
 axes[0].annotate('',xy=(-15,1.5),xytext=(15,1.5),arrowprops={'arrowstyle':'<->'});axes[0].text(-5,2.1,'30mm')
 section(axes[1],parts['cap'],1,-6.0,'#33383e','뚜껑 안쪽 걸림 홈')
 section(axes[1],parts['drawer'],1,-6.0,'#b9684e','내관 사각 키의 걸림턱')
 axes[1].set_xlim(10.5,17);axes[1].set_ylim(2.5,8);axes[1].set_title('사각 키 양옆 보호된 딸깍 턱');axes[1].legend(loc='upper right',fontsize=9)
 fig.tight_layout();pdf.savefig(fig);fig.savefig(out/'06_square30_cap_snap_R12.png',dpi=150);plt.close(fig)

fig,ax=plt.subplots(figsize=(7,5))
section(ax,parts['drawer'],1,-1.5,'#b9684e','내관 바깥 둥근 돌기')
sh=shell.copy();sh.apply_transform(T([0,0,253])@R(np.pi,[0,1,0]));section(ax,sh,1,-1.5,'#33383e','외관 안쪽 대응 홈')
ax.set_xlim(32,39.5);ax.set_ylim(17,23);ax.set_title('내관 돌기 ↔ 외관 홈 / 긴 클립·누름버튼 없음');ax.legend(loc='lower left');fig.tight_layout();fig.savefig(out/'03_detent_detail_R12.png',dpi=150);plt.close(fig)
