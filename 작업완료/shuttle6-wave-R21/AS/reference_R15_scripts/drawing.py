"""R15 actual-mesh sections: circular inside, external cradle and rail detents."""
from pathlib import Path
import pickle,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties,fontManager
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
from build import P
PTH=Path(__file__).resolve().parent.parent
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');fontManager.addfont(font.get_file())
plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False,'pdf.fonttype':42})
parts=pickle.load(open(PTH/'parts_nominal.pkl','rb'));shell=pickle.load(open(PTH/'assembled_shell.pkl','rb'))['shell']
body=shell.copy();body.apply_transform(T([0,0,253.])@R(np.pi,[0,1,0]))
out=PTH/'drawings';out.mkdir(exist_ok=True)
def sec(ax,m,axis,at,color,label):
 n=np.zeros(3);n[axis]=1;o=np.zeros(3);o[axis]=at;keep=[i for i in range(3) if i!=axis]
 s=m.section(plane_origin=o,plane_normal=n)
 if s is not None:
  for j,e in enumerate(s.entities):
   v=s.vertices[e.points];ax.plot(v[:,keep[0]],v[:,keep[1]],color=color,lw=1.4,label=label if j==0 else None)
 ax.set_aspect('equal');ax.grid(alpha=.2)
with PdfPages(out/'Shuttle6_C_도면_R15.pdf') as pdf:
 fig,axs=plt.subplots(1,2,figsize=(12,7))
 for ax in axs:
  sec(ax,body,2,100,'#33383e','외관: 맞춤 레일 홈')
  sec(ax,parts['drawer'],2,100,'#bd6f53','내관: 원형 그대로 + 좁은 바닥 굽')
 axs[0].set_xlim(-43,43);axs[0].set_ylim(-43,43);axs[0].legend(loc='upper right');axs[0].set_title('안쪽 Ø64 원형 / 외부에만 재료 추가')
 axs[1].set_xlim(-16,16);axs[1].set_ylim(-40,-22);axs[1].set_title('외부 받침·대응 홈 / 수직 바닥 총 두께2.8mm')
 fig.tight_layout();pdf.savefig(fig);fig.savefig(out/'02_actual_round_inside_cradle_R15.png',dpi=150);plt.close(fig)
 fig,axs=plt.subplots(1,2,figsize=(10,10))
 for ax in axs:
  sec(ax,body,1,P['CAM_FACE_Y'],'#33383e','외관 레일 속 홈')
  sec(ax,parts['drawer'],1,P['CAM_FACE_Y'],'#bd6f53','받침 쪽 낮은 돌기')
 axs[0].set_xlim(-30,30);axs[0].set_ylim(245,5);axs[0].legend(loc='lower center');axs[0].set_title('레일 안쪽에 양옆6단 · 피치36mm')
 for i,z in enumerate([20,56,92,128,164,200],1):axs[0].text(0,z,str(i),ha='center')
 axs[1].set_xlim(7,10);axs[1].set_ylim(16,24);axs[1].set_title('한 곳 확대 · 안착 여유0.2mm')
 fig.tight_layout();pdf.savefig(fig);fig.savefig(out/'03_six_detents_inside_rail_R15.png',dpi=150);plt.close(fig)
 fig,ax=plt.subplots(figsize=(8,7));up=parts['shell_upper'].copy();up.apply_translation([0,0,P['BODY_SPLIT_Z']])
 sec(ax,parts['shell_lower'],2,P['BODY_SPLIT_Z']+7,'#bd6f53','아래 몸통: 바닥 통과부가 열린 접착턱')
 sec(ax,up,2,P['BODY_SPLIT_Z']+7,'#33383e','위 몸통: 레일과 대응 접착 소켓')
 ax.set_title('받침이 접합부도 통과 / 접착 겹침22mm·정렬 키 유지');ax.legend(loc='upper right')
 fig.tight_layout();pdf.savefig(fig);fig.savefig(out/'04_cradle_passes_joint_R15.png',dpi=150);plt.close(fig)
 fig,ax=plt.subplots(figsize=(8,7));sec(ax,parts['cap'],2,4.5,'#33383e','30mm 사각 포켓');sec(ax,parts['drawer'],2,4.5,'#bd6f53','29.6mm 사각 키')
 ax.set_title('별도 뚜껑의 사각 스냅은 유지 / 반원 포켓은 새 받침 단면에 맞춤');ax.legend()
 fig.tight_layout();pdf.savefig(fig);fig.savefig(out/'05_separate_cap_R15.png',dpi=150);plt.close(fig)

 fig,axs=plt.subplots(1,2,figsize=(12,7))
 sec(axs[0],parts['rear_head'],2,235,'#bd6f53','뒤끝:360도 원형 가이드')
 sec(axs[0],body,2,235,'#33383e','기존 외관 안쪽')
 axs[0].set_title('외경69.2mm·원형 가이드 길이27.8mm');axs[0].legend()
 sec(axs[1],parts['rear_head'],0,0,'#bd6f53','따로 출력하는 뒤컵')
 sec(axs[1],parts['drawer'],0,0,'#33383e','내관 뒤끝')
 axs[1].set_ylim(205,252);axs[1].set_title('겹침10mm·접착간극 편측0.2mm');axs[1].legend()
 fig.tight_layout();pdf.savefig(fig);fig.savefig(out/'06_round_rear_guide_R15.png',dpi=150);plt.close(fig)
