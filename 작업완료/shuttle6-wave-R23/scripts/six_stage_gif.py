from pathlib import Path
import pickle,numpy as np,trimesh as tm
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
from sequence_renderer import render_sequence
O=Path(__file__).resolve().parent.parent
p=pickle.load(open(O/'parts_nominal.pkl','rb'));up=p['shell_upper'].copy();up.apply_translation([0,0,121.5]);shell=tm.util.concatenate([p['shell_lower'],up])
closed=T([0,0,253.])@R(np.pi,[0,1,0]);pivot=np.array([0,45.5,247.]);G=T([100,255,40])@R(np.pi/2,[1,0,0])
from content_gauges import individual_gauges
gauges=individual_gauges();contents=pickle.load(open(O/'contents.pkl','rb'))['contents'];parts={'shell':shell,'drawer':p['drawer'],'cap':p['cap'],'latch':p['latch'],'stop_left':p['stop_left'],'stop_right':p['stop_right'],}
parts.update({f'콕{i+1}':m for i,m in enumerate(gauges)})
colors={'shell':'#33383e','drawer':'#bd6f53','cap':'#bd6f53','latch':'#ffb300','stop_left':'#33383e','stop_right':'#33383e','contents':'#eeeeee'}
colors.update({f'콕{i+1}':('#fff1cc' if i==0 else '#eeeeee') for i in range(6)})
states={};timeline=[]
def frame(label,distance,angle,duration,hold=False,stage=0,pick=0):
 key=f'{len(states):03d} · '+label
 opened=T(pivot)@R(np.deg2rad(angle),[1,0,0])@T(-pivot)
 slide=T([0,0,distance]);st={'shell':G,'stop_left':G,'stop_right':G,'drawer':G@slide@closed,'cap':G@slide@closed,'latch':G@slide@opened}
 st.update({f'콕{i+1}':G@slide@closed@T([0,pick if i==0 else 0,0]) for i in range(6)})
 states[key]={n:v.ravel().tolist() for n,v in st.items()}
 timeline.append({'state':key,'travel_mm':round(distance,4),'clip_angle_deg':angle,'duration_ms':duration,'hold':hold,'stage':stage,'first_shuttle_lift_mm':pick})
frame('닫힘 · 걸림1/6 · 0mm',0,0,900,True,0)
for angle in range(10,91,10):frame('클립 풀기',0,angle,70)
frame('잠금 해제 · 걸림1/6 · 0mm',0,90,500,True,1)
last=0
for stage,target in enumerate([36,72,108,144,180],2):
 for k in range(1,9):
  u=k/8;smooth=u*u*(3-2*u);frame(f'{stage-1} → {stage}단계 인출',last+(target-last)*smooth,90,60)
 frame(f'걸림{stage}/6 · {target}mm',target,90,650,True,stage)
 last=target
for k in range(1,10):
 u=k/9;smooth=u*u*(3-2*u);frame('6단계 이후 끝까지 인출',180+45*smooth,90,65)
frame('6개 노출 · 225mm · 양옆 이탈 방지턱에서 멈춤',225,90,1700,True,7)
render_sequence(parts,str(O/'preview_six_steps'),colors=colors,states=states,gif_size=(960,720),status='R23 형상 기반 동작 시각화 · 코르크가 뚜껑 쪽 · 앞콘은 원형 · 뒤끝 반원 · 6단계 인출',timeline=timeline)
print('SIX STAGE GIF COMPLETE',flush=True)
