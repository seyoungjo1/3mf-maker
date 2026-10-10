"""Toolbox48 v7 조립 정의 — tools/pipeline.py 가 define(parts) 를 호출한다.
결합부(v5 실측, 변경 없음): 본체 뒤 너클 ⌀3.4 (y 192.39+14.2, z 26.5) ↔ 뚜껑 귀 쌍(출력 좌표 y 68.42, z 10); 손잡이 귀 구멍 (y 65.45, z 18.25) ↔ 다리 끝 구멍 (y -162.57, z 4.5).
걸쇠는 실제 장착 위치를 사진에서 확정하지 못해 조립 상태에 넣지 않는다(형상·결합부 v5 그대로)."""
import os, sys, json, numpy as np, trimesh
from trimesh.transformations import rotation_matrix as R, translation_matrix as T
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..')); sys.path.insert(0, os.path.join(ROOT, 'tools'))
from load3mf import load_parts
PR = json.load(open(os.path.join(HERE, '..', 'docs', 'v8_params.json')))
BAY_CX = [75.6, 128.0, 180.4]; PITCH = 7.0; N = 8; FLOOR_Z = 2.6
ROW_START = [PR['front_row'][0] + 1.0, PR['rear_row'][0] + 1.0]      # 칸 앞면 + 여유 1.0 (칸 깊이 58 = 8×7 + 1 + 1)
def define(parts):
    C = PR['C_closed']; knuckle = np.array(PR['knuckle'], float); flip = R(np.pi, [1, 0, 0]); dx = (79.9 + 176.1) / 2 - (387.1 + 483.3) / 2
    closed = T([dx, C, 36.5]) @ flip
    def lid_open(ang): return T(knuckle) @ R(np.radians(ang), [-1, 0, 0]) @ T(-knuckle) @ closed   # 축 -x: +각도 = 뚜껑이 위로 열림(+x 축이면 본체 속으로 내려감 — v7 검증에서 확인)
    ear = np.array([0, 65.45, 18.25]); leg_hole = np.array([0, -162.57, 4.5]); hx = (63.6 + 136.4) / 2; ex = (91.6 + 164.4) / 2
    def handle_M(th): return T(ear) @ R(np.radians(th), [1, 0, 0]) @ T([ex - hx, 0, 0]) @ T(-leg_hole)
    hm = {}
    for th in (-90, 90):
        m = parts['handle'].copy(); m.apply_transform(handle_M(th)); hm[th] = float(m.bounds[1, 2])
    th_up = max(hm, key=hm.get); th_down = min(hm, key=hm.get)
    # 명판 48장: 샘플 밑판을 긴 변 아래로 세워(x축 +90°) U자 홈에, 앞뒤 피치 7.0 으로 8장씩
    plate = load_parts(os.path.join(ROOT, 'sample', 'nameplate_50x30x7_EtoA.3mf'))['2_민 우_밑판'].copy(); plate.apply_translation(-plate.bounds[0])
    inst = []
    for cx in BAY_CX:
        for s in ROW_START:
            for i in range(N):
                m = plate.copy(); m.apply_transform(R(np.pi / 2, [1, 0, 0])); m.apply_translation([cx - 25, s + PITCH * (i + 1), FLOOR_Z]); inst.append(m)
    plates48 = trimesh.util.concatenate(inst)
    I = np.eye(4); lip_region = [[40, 70, 27.0], [216, 210, 28.8]]   # 립 옆면 구간만(스커트 바닥 0.1·립 윗면 0.2·윗모서리 챔퍼(z>28.9)의 틈은 끼움이 아님)
    lifted = T([0, 0, 50]) @ closed
    states = {'분리': {'base': I, 'lid': lifted, 'logo': lifted, 'handle': T([0, -30, 0]) @ handle_M(0)},
              '조립-닫힘': {'base': I, 'lid': closed, 'logo': closed, 'handle': handle_M(th_up)},
              '조립-열림 90°': {'base': I, 'lid': lid_open(90), 'logo': lid_open(90), 'handle': handle_M(th_down)},
              '명판 48장 (열림 90°)': {'base': I, 'lid': lid_open(90), 'logo': lid_open(90), 'handle': handle_M(th_down), 'nameplates': I},
              '명판 48장 (닫힘)': {'base': I, 'lid': closed, 'logo': closed, 'handle': handle_M(th_up), 'nameplates': I}}
    pairs = [['base', 'lid', {'contact': True}], ['base', 'lid', {'region': lip_region, 'min_gap': 0.28}], ['base', 'handle', {'contact': True}],
             ['base', 'nameplates', {'contact': True}], ['base', 'nameplates', {'region': [[40, 75, 3.5], [216, 210, 12.0]], 'min_gap': 0.5}],
             ['lid', 'nameplates', {'min_gap': 0.5}]]
    sweeps = [{'name': '경첩', 'part': 'lid', 'pivot': knuckle.tolist(), 'axis': [-1, 0, 0], 'base': closed, 'angles': list(range(0, 121, 15)), 'against': ['base'], 'need': [15, 120], 'also': {'handle': handle_M(th_down)}, 'follow': ['logo']},
              {'name': '손잡이', 'part': 'handle', 'pivot': ear.tolist(), 'axis': [1, 0, 0], 'base': handle_M(0), 'angles': list(range(-90, 91, 15)), 'against': ['base'], 'need': [-90, 90], 'also': {'lid': closed, 'logo': closed}}]
    notes = [f'손잡이 올림 각도 {th_up}°(가로대 z {hm[th_up]:.1f}), 내림 {th_down}°(z {hm[th_down]:.1f}). 손잡이 다리 끝 ↔ 귀 슬롯 간격 0.06 은 v5 그대로(사용자: 문제 없음).',
             '걸쇠: 형상·결합부 v5 그대로. 실제 장착 위치를 확정하지 못해 조립 상태·GIF 에는 넣지 않음(플레이트 A 렌더에만).',
             f'명판: 칸 중심 x {BAY_CX}, 앞뒤 시작 y {ROW_START}, 피치 {PITCH}, 칸당 {N}장 = {3 * 2 * N}장.']
    return {'states': states, 'pairs': pairs, 'sweeps': sweeps, 'extra': {'nameplates': plates48}, 'notes': notes}
