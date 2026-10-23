"""모듈 A 가운데 기구 확대 렌더(보고용): 십의 자리 20T·일의 자리 C/L·R1·피니언·플런저 폴 — 09→10 누름(자리올림)과 10→09 노브(빌림).
python scripts/closeup.py  →  figures/closeup/ (mm render)"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE); ROOT = os.path.dirname(os.path.dirname(PROJ))
sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, HERE)
import mm, assembly as A
parts = pickle.load(open(os.path.join(PROJ, 'parts_nominal.pkl'), 'rb'))
SEL = {'core_A_tens': '#9aa3ad', 'core_A_ones': '#7f8a96', 'lockdisc_A': '#c9d1d9', 'r1disc_A': '#6d7782', 'pinion_A': '#ffb300', 'pin_A': '#e8e8e8',
       'plunger_A': '#4fc3f7', 'star_A_tens': '#9aa3ad', 'disc_A_tens_b': '#5c6670', 'disc_A_ones_f': '#5c6670'}
from trimesh.transformations import rotation_matrix
SH = np.array([[1, 0, 0, 48.5], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])           # 모듈 A 중심을 x 0 으로
RZ = rotation_matrix(np.radians(-90), [0, 0, 1])                                        # 축(x)이 정면 뷰 시선 방향이 되게(기어 평면이 보이게)
GL = RZ @ SH
d = os.path.join(PROJ, 'figures', 'closeup'); os.makedirs(os.path.join(d, 'stl'), exist_ok=True)
files = []
for n in SEL:
    m = parts[n].copy(); m.apply_transform(GL); f = os.path.join(d, 'stl', n + '.stl'); m.export(f); files.append(f)
names = list(parts); st = {}
def put(lab, M):
    st[lab] = {n: (GL @ M[n] @ np.linalg.inv(GL)).flatten().tolist() for n in SEL}
for p in (0.0, 0.4, 0.6, 0.8, 1.0):
    put(f'09→10 누름 {int(p * 100)}%', A.state(names, {'A': (0, 9), 'B': (0, 0)}, press={'A': p}))
for a in (9, 18, 27):
    put(f'10→09 노브 뒤로 {a}°', A.state(names, {'A': (1, 0), 'B': (0, 0)}, knob={'A': float(a)}))
r = mm.run('render', files=files, out=d, colors=SEL, states=st, frames=40,
           status='모듈 A 가운데 기구 — 회색 계열: 십의 자리 20T·일의 자리 C/L/R1, 노랑: 전달 피니언, 하늘색: +1 플런저 폴')
print(json.dumps(r, ensure_ascii=False)[:300])
