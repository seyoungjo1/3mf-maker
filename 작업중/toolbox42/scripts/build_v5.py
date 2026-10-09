#!/usr/bin/env python3
"""v5 출력 파일 생성. 입력: 작업용 pkl(v5parts) → models/ 에 일반 3MF 2장 + Bambu 프로젝트 3MF + STL."""
import sys, os, json, pickle, numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from generic3mf import write_generic_3mf
from bbl_project import write_bbl_project
MODELS = os.path.join(HERE, '..', 'models')
C1, C2 = '#30949D', '#F2AF38'     # 필라멘트 1(본체색) / 2(로고색) — 원본 프로젝트 색 유지
P = pickle.load(open(sys.argv[1], 'rb'))
def place(m, x0, y0):
    m = m.copy(); b = m.bounds; m.apply_translation([x0 - b[0, 0], y0 - b[0, 1], -b[0, 2]]); return m
# 플레이트 A: 본체 + 손잡이 + 걸쇠 (256×256 안에 여유 두고 배치)
base = place(P['base'], 20, 100); handle = place(P['handle'], 20, 40); latch = place(P['latch'], 120, 45)
# 플레이트 B: 뚜껑(뒤집어 출력) + 로고 — 둘은 한 오브젝트의 두 파트(상대 위치 유지)
lid, logo = P['lid'].copy(), P['logo'].copy(); b = lid.bounds; d = [40 - b[0, 0], 60 - b[0, 1], -b[0, 2]]
lid.apply_translation(d); logo.apply_translation(d)
A = [{'name': 'base', 'parts': [(base, C1, 'base')]}, {'name': 'handle', 'parts': [(handle, C1, 'handle')]}, {'name': 'latch', 'parts': [(latch, C1, 'latch')]}]
B = [{'name': 'lid+logo', 'parts': [(lid, C1, 'lid'), (logo, C2, 'logo')]}]
write_generic_3mf(os.path.join(MODELS, 'Toolbox42_v5_A_base_handle_latch.3mf'), A, 'Toolbox42 v5 A')
write_generic_3mf(os.path.join(MODELS, 'Toolbox42_v5_B_lid_logo.3mf'), B, 'Toolbox42 v5 B')
# Bambu 프로젝트(3 플레이트): project_settings 는 sample/test+lunch+box(1).3mf(사용자 Bambu Studio 02.08.02.61 내보내기)에서 유도
ps = json.load(open(os.path.join(MODELS, '..', 'docs', 'project_settings_v5.json'), encoding='utf-8'))
plates = [{'name': '01 Base + Handle + Latch', 'objects': [{'name': n, 'extruder': 1, 'parts': [(m, n, 1)]} for n, m in [('base', base), ('handle', handle), ('latch', latch)]]},
          {'name': '02 Lid + Logo', 'objects': [{'name': 'lid+logo', 'extruder': 1, 'parts': [(lid, 'lid', 1), (logo, 'logo', 2)]}]}]
write_bbl_project(os.path.join(MODELS, 'Toolbox42_P1S_v5_project.3mf'), plates, ps, app_version=ps['version'], title='Toolbox42 v5', filament_colours=[C1, C2])
for n, m in [('latch', P['latch']), ('handle', P['handle'])]:
    mm = m.copy(); mm.apply_translation(-mm.bounds[0]); mm.export(os.path.join(MODELS, f'Toolbox42_{n}_v5.stl'))
print('done')
