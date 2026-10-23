#!/usr/bin/env python3
"""gukse-clicker 빌드 — `python tools/mm.py make 작업중/gukse-clicker/pipeline.json` 이 이 스크립트를 프로젝트 폴더에서 실행한다.
스킬 순서: 1 설계 규칙 → 2 모델링(이 파일) → 3 QC → 4 조립 검증 → 5 렌더 → 6 3MF → 7 보고 (3~7 은 파이프라인이 한다).
산출: parts_nominal.pkl(공칭 — 조립 검증용), parts.pkl(첫 층 +0.15 선반영 — 출력 QC 용), models/gukse-clicker_A.3mf(플레이트)
틀은 '상자 + 경첩 뚜껑' 예시다. make_parts() 와 P 를 새 도면으로 바꾸고 README 치수표를 같이 고친다."""
import os, sys, pickle
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE); ROOT = os.path.dirname(os.path.dirname(PROJ))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import trimesh
from efc import pre_expand_first_layer
from generic3mf import write_generic_3mf

P = {"W": 40.0, "D": 30.0, "H": 15.0, "WALL": 3.0, "FLOOR": 3.0, "LID_T": 2.0}     # 설계 치수표 (README.md 와 같게)
COLORS = {'base': '#37474f', 'lid': '#ffb300'}

def box(w, d, h, at=(0, 0, 0)):
    b = trimesh.creation.box(extents=[w, d, h]); b.apply_translation([at[0] + w / 2, at[1] + d / 2, at[2] + h / 2]); return b

def make_parts():
    """출력 방향(평평한 큰 면이 z=0) 공칭 파트 {이름: trimesh}. 새 도면은 여기만 바꾼다."""
    W, D, H, T, F = P['W'], P['D'], P['H'], P['WALL'], P['FLOOR']
    base = trimesh.boolean.difference([box(W, D, H), box(W - 2 * T, D - 2 * T, H, (T, T, F))], engine='manifold')
    lid = box(W, D, P['LID_T'])
    return {'base': base, 'lid': lid}

def plate(parts, gap=10.0):
    """플레이트 배치: x 방향으로 gap 간격, 베드(256×256) 안 원점 10 mm 부터."""
    objs, x = [], 10.0
    for n, m in parts.items():
        c = m.copy(); c.apply_translation([x - c.bounds[0][0], 10.0 - c.bounds[0][1], -c.bounds[0][2]]); x = c.bounds[1][0] + gap
        objs.append({'name': n, 'parts': [(c, COLORS.get(n, '#37474f'), n)]})
    return objs

if __name__ == '__main__':
    os.chdir(PROJ); os.makedirs('models', exist_ok=True)
    nominal = make_parts(); pickle.dump(nominal, open('parts_nominal.pkl', 'wb'))
    printed = {n: pre_expand_first_layer(m) for n, m in nominal.items()}; pickle.dump(printed, open('parts.pkl', 'wb'))
    write_generic_3mf('models/gukse-clicker_A.3mf', plate(printed), 'gukse-clicker')
    print('build ok', {n: [round(v, 2) for v in m.extents] for n, m in nominal.items()})
