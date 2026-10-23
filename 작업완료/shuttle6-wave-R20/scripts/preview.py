from pathlib import Path
import sys,pickle,json,numpy as np,trimesh as tm
ROOT=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'tools'))
from render_preview import render
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
p=pickle.load(open(O/'parts_nominal.pkl','rb'));qc=json.load(open(O/'qc/printed_parts.json'));assert len(qc)==9
c=json.load(open(O/'qc/assembly.json'));assert all(r['body_overlap_mm3']<.01 and r['cap_overlap_mm3']<.01 for r in c['latch_sweep']);assert c['gauge_overlap_mm3']<.01
assert all(r['body_overlap_mm3']<.01 and r['stop_key_overlap_mm3']<.01 for r in c['slide'] if r['travel_mm']<=225)
assert c['slide'][-1]['stop_key_overlap_mm3']>1
up=p['shell_upper'].copy();up.apply_translation([0,0,121.5]);shell=tm.util.concatenate([p['shell_lower'],up]);closed=T([0,0,253.])@R(np.pi,[0,1,0]);pivot=np.array([0,45.5,247.]);opened=T(pivot)@R(np.pi/2,[1,0,0])@T(-pivot)
G=T([100,255,40])@R(np.pi/2,[1,0,0]);contents=pickle.load(open(O/'contents.pkl','rb'))['contents']
parts={'shell':shell,'drawer':p['drawer'],'cap':p['cap'],'latch':p['latch'],'stop_left':p['stop_left'],'stop_right':p['stop_right'],'contents':contents}
base={'shell':G,'stop_left':G,'stop_right':G}
states={'닫힘·뚜껑축 클립':dict(base,drawer=G@closed,cap=G@closed,latch=G),'클립 몸통쪽에서 젖힘':dict(base,drawer=G@closed,cap=G@closed,latch=G@opened),'225mm·양옆 멈춤':dict(base,drawer=G@T([0,0,225])@closed,cap=G@T([0,0,225])@closed,latch=G@T([0,0,225])@opened,contents=G@T([0,0,225])@closed)}
colors={'shell':'#33383e','drawer':'#bd6f53','cap':'#bd6f53','latch':'#ffb300','stop_left':'#4b9eba','stop_right':'#4b9eba','contents':'#eeeeee'}
render(parts,str(O/'preview'),colors=colors,states={k:{n:m.ravel().tolist() for n,m in st.items()} for k,st in states.items()},frames=30,status='완료 — R20 · 코르크 앞·고리 사선 옆면 · 서랍식 좌우 멈춤 · 뒤컵 양옆 고정 어깨 · 뚜껑축→몸통 걸림 · 국부 서포트')
# Both side shoulders shown by the dedicated reproducible cutaway script.
import runpy
runpy.run_path(str(O/'scripts/detail_stops.py'))
H=T([128,250,45])@R(np.pi/2,[1,0,0]);cb=tm.creation.box([110,130,52]);cb.apply_translation([0,0,231])
# Reversed clamp and fixed spacers on cap. Body shortened for clarity only.
sc=tm.boolean.intersection([shell,cb],engine='manifold');cap=p['cap'].copy();cap.apply_transform(closed)
pl={'body':sc,'cap':cap,'latch':p['latch']};st={'잠금·축은 뚜껑':{'body':H,'cap':H,'latch':H},'열림·걸림은 몸통':{'body':H,'cap':H,'latch':H@opened}}
render(pl,str(O/'preview_lock'),colors={'body':'#33383e','cap':'#bd6f53','latch':'#ffb300'},states={k:{n:m.ravel().tolist() for n,m in v.items()} for k,v in st.items()},frames=20,status='완료 — 반대 방향 클립 / 양쪽 지지귀 / 고정 금속 스페이서6×3.2×6.8 / M3 축')
runpy.run_path(str(O/'scripts/keyring_preview.py'))
print('PREVIEWS COMPLETE',flush=True)
