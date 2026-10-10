#!/usr/bin/env python3
"""도구 자가검사: 상자+뚜껑(끼움 0.3, 경첩 회전) 가짜 프로젝트를 만들어 pipeline 을 돌리고
(1) 정상 설계 → 경고 0·GIF/PNG/3MF 생성, (2) 일부러 간섭시킨 설계 → ⚠ 검출 을 확인한다. 사용: python tools/selftest.py"""
import os, sys, json, pickle, shutil, tempfile, numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from generic3mf import write_generic_3mf; from efc import pre_expand_first_layer; import pipeline
def box(w, d, h, at=(0, 0, 0)):
    b = trimesh.creation.box(extents=[w, d, h]); b.apply_translation([at[0] + w / 2, at[1] + d / 2, at[2] + h / 2]); return b
def fixture(root, gap):
    base = trimesh.boolean.difference([box(40, 30, 15), box(34, 24, 13, (3, 3, 3))], engine='manifold')          # 벽 3, 바닥 3
    lid = box(40, 30, 2)                                                                                            # 평판 뚜껑(경첩 스윕용, 본체 위에 얹힘=접촉)
    plug = trimesh.boolean.union([box(40, 30, 2), box(34 - 2 * gap, 24 - 2 * gap, 4, (3 + gap, 3 + gap, 2))], engine='manifold')  # 플러그 뚜껑(끼움 gap/면)
    base = pre_expand_first_layer(base); lid = pre_expand_first_layer(lid); plug = pre_expand_first_layer(plug)
    parts = {'base': base, 'lid': lid, 'plug_lid': plug}; os.makedirs(os.path.join(root, 'models'), exist_ok=True); os.makedirs(os.path.join(root, 'scripts'), exist_ok=True)
    pickle.dump(parts, open(os.path.join(root, 'parts.pkl'), 'wb'))
    A = base.copy(); A.apply_translation([20, 20, 0]); B = lid.copy(); B.apply_translation([80, 20, 0]); C = plug.copy(); C.apply_translation([140, 20, 0])
    write_generic_3mf(os.path.join(root, 'models', 'A.3mf'), [{'name': 'base', 'parts': [(A, '#37474f', 'base')]}, {'name': 'lid', 'parts': [(B, '#ffb300', 'lid')]}, {'name': 'plug_lid', 'parts': [(C, '#ffb300', 'plug_lid')]}], 'selftest')
    open(os.path.join(root, 'scripts', 'asm.py'), 'w').write('''import numpy as np
from trimesh.transformations import rotation_matrix as R, translation_matrix as T
def define(parts):
    flip = R(np.pi, [1, 0, 0]); closed = T([0, 30, 17]) @ flip        # 뒤집어(판 z -2~0, 플러그 -6~-2) 본체 윗면 15 에 판 밑면이 닿게 → 플러그는 z 11~15 로 공동 안
    piv = [0, 30, 17]                                                  # 뒤 모서리 윗면 경첩축
    return {"states": {"분리": {"base": np.eye(4), "lid": T([0, 0, 30]) @ closed, "plug_lid": T([0, 40, 0]) @ closed},
                       "닫힘(평판)": {"base": np.eye(4), "lid": closed}, "닫힘(플러그)": {"base": np.eye(4), "plug_lid": closed}},
            "pairs": [["base", "lid", {"contact": True}], ["base", "plug_lid", {"contact": True}], ["base", "plug_lid", {"region": [[2, 2, 10.5], [38, 28, 14.9]], "min_gap": 0.25}]],
            "sweeps": [{"name": "경첩", "part": "lid", "pivot": piv, "axis": [1, 0, 0], "base": closed, "angles": [0, 30, 60, 90, 120], "against": ["base"], "need": [0, 120]}]}
''')
    json.dump({'name': 'selftest', 'out': 'qc', 'parts_pkl': 'parts.pkl', 'plates': ['models/A.3mf'], 'assembly': 'scripts/asm.py', 'colors': {'base': '#37474f', 'lid': '#ffb300'}, 'min_gap': 0.25, 'frames': 8},
              open(os.path.join(root, 'cfg.json'), 'w'))
    return os.path.join(root, 'cfg.json')
def efc_group_case():
    """뚜껑+인레이(포켓과 0.3 틈) 그룹 EFC 뒤에도 뚜껑이 1조각이고 띠는 바깥에만 생기는지(Toolbox48 v8 24조각 버그 재현)."""
    from efc import pre_expand_first_layer_group
    lid = trimesh.boolean.difference([box(40, 30, 3), box(10.6, 6.6, 0.6, (9.7, 11.7, 0)), box(10.6, 6.6, 0.6, (24.7, 11.7, 0))], engine='manifold')
    inl = [box(10, 6, 0.6, (10, 12, 0)), box(10, 6, 0.6, (25, 12, 0))]; inlay = trimesh.util.concatenate(inl)
    l2, i2 = pre_expand_first_layer_group([lid, inlay])
    nb = len(l2.split(only_watertight=False)); grow = (l2.bounds[1, 0] - l2.bounds[0, 0]) - 40
    print(f'[EFC 그룹] 뚜껑 조각 {nb}, 바깥 성장 {grow:.2f} mm (기대 1, 0.30), 인레이 부피 변화 {abs(i2.volume) - abs(inlay.volume):.3f}')
    ok1 = nb == 1 and abs(grow - 0.30) < 0.02 and abs(abs(i2.volume) - abs(inlay.volume)) < 0.01   # 구멍 안 띠 = 인레이 부피 증가
    # 수직 첫 층의 둥근 모서리: 띠 안쪽 경계가 벽과 같은 면 → 부피 0 조각. 실제 Toolbox48 v8 뚜껑 모서리를 잘라 고정 시험편으로 씀(예전 코드 2조각)
    from efc import pre_expand_first_layer
    fx = trimesh.load(os.path.join(HERE, 'fixtures', 'efc_vertical_rounded_edge.stl'), force='mesh'); fx.merge_vertices()
    g2, = pre_expand_first_layer_group([fx]); r2 = pre_expand_first_layer(fx)
    nb2, nb3 = len(r2.split(only_watertight=False)), len(g2.split(only_watertight=False))
    print(f'[EFC 실제 모서리] 단일 조각 {nb2}, 그룹 조각 {nb3} (기대 1, 1; 예전 코드 그룹 2)')
    return ok1 and nb2 == 1 and nb3 == 1
if __name__ == '__main__':
    tmp = tempfile.mkdtemp(prefix='selftest_'); ok = efc_group_case()
    cfg = fixture(os.path.join(tmp, 'good'), 0.3); rc = pipeline.run(cfg); rep = json.load(open(os.path.join(tmp, 'good', 'qc', 'report.json')))
    files = [os.path.join(tmp, 'good', 'qc', f) for f in ('REPORT.md', 'assembly/turntable.gif', 'motion/turntable.gif', 'plate_A/view_iso.png')]
    print('\n[정상 설계] 종료코드', rc, '| 경고', rep['warn'], '| 산출물', [os.path.exists(f) for f in files])
    ok &= (rc == 0 and all(os.path.exists(f) for f in files))
    cfg = fixture(os.path.join(tmp, 'bad'), -0.5); rc = pipeline.run(cfg); rep = json.load(open(os.path.join(tmp, 'bad', 'qc', 'report.json')))
    print('\n[간섭 설계] 종료코드', rc, '| 경고', rep['warn']); ok &= (rc == 1 and any('∩' in w for w in rep['warn']))
    cfg = fixture(os.path.join(tmp, 'tight'), 0.1); rc = pipeline.run(cfg); rep = json.load(open(os.path.join(tmp, 'tight', 'qc', 'report.json')))
    print('\n[빡빡한 끼움 0.1] 종료코드', rc, '| 경고', rep['warn']); ok &= (rc == 1 and any('간격' in w for w in rep['warn']))
    shutil.rmtree(tmp, ignore_errors=True); print('\nSELFTEST', 'PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
