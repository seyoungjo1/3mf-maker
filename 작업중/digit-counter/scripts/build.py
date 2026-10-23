#!/usr/bin/env python3
"""digit-counter 빌드 — `python tools/mm.py make 작업중/digit-counter/pipeline.json` 이 프로젝트 폴더에서 실행한다.
산출: parts_nominal.pkl(조립 좌표·숫자 00 정지 — 조립 검증·렌더용), parts.pkl(출력 방향·첫 층 +0.15 — QC 용),
meta.json(파트별 색·출력 방향·종류), models/plates/*.3mf(플레이트 7장)."""
import os, sys, json, pickle
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE); ROOT = os.path.dirname(os.path.dirname(PROJ))
sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, HERE)
import numpy as np, trimesh
from trimesh.geometry import align_vectors
from efc import pre_expand_first_layer
from generic3mf import write_generic_3mf
import geom as G

PLATES = {   # 플레이트: (파일, [오브젝트 이름 접두/이름], 필라멘트 순서)
    'P1_body': ('models/plates/P1_body.3mf', ['housing', 'lid'], [G.BLACK]),
    'P2_panels': ('models/plates/P2_panels.3mf', ['front', 'mid'], [G.BLACK]),
    'P3_segments_A': ('models/plates/P3_segments_A.3mf', ['sh_A_', 'stem_A_'], [G.BLACK, G.YELLOW]),
    'P3_segments_B': ('models/plates/P3_segments_B.3mf', ['sh_B_', 'stem_B_'], [G.BLACK, G.YELLOW]),
    'P4_mech_A': ('models/plates/P4_mech_A.3mf', ['shaft_A', 'core_A_', 'disc_A_', 'star_A_', 'lockdisc_A', 'r1disc_A', 'pin_A', 'plunger_A', 'spring_A', 'leaf_A_', 'collar_l'], [G.GRAY]),
    'P4_mech_B': ('models/plates/P4_mech_B.3mf', ['shaft_B', 'core_B_', 'disc_B_', 'star_B_', 'lockdisc_B', 'r1disc_B', 'pin_B', 'plunger_B', 'spring_B', 'leaf_B_', 'collar_r'], [G.GRAY]),
    'P5_yellow': ('models/plates/P5_yellow.3mf', ['knob_l', 'knob_r', 'cap_', 'pinion_', 'colon'], [G.YELLOW]),
}

def to_print(m, up):
    """조립 메시 → 출력 방향(up 이 +z, 바닥 z=0, xy 원점 근처)."""
    R = align_vectors(np.asarray(up, float), [0, 0, 1.0]); c = m.copy(); c.apply_transform(R)
    c.apply_translation(-c.bounds[0]); return c, R

def pack(objs, W=256.0, margin=8.0, gap=6.0):
    """선반 배치: 큰 것부터 x 로 늘어놓고 넘치면 다음 줄. objs = [(이름, [메시…])] (같은 오브젝트의 메시는 같이 움직임)."""
    items = sorted(objs, key=lambda o: -max(np.ptp(np.vstack([m.bounds for m in o[1]]), axis=0)[:2]))
    out = []; x = y = margin; row = 0.0
    for n, ms in items:
        b = np.vstack([m.bounds for m in ms]); w, d = np.ptp(b[:, 0]), np.ptp(b[:, 1])
        rot = False
        if w > W - 2 * margin or (x + w > W - margin and x + d <= W - margin and d < w):
            rot = True; w, d = d, w
        if x + w > W - margin: x = margin; y += row + gap; row = 0.0
        moved = []
        for m in ms:
            c = m.copy()
            if rot: c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
            moved.append(c)
        bb = np.vstack([m.bounds for m in moved])
        for c in moved: c.apply_translation([x - bb[0, 0], y - bb[0, 1], 0])
        out.append((n, moved)); x += w + gap; row = max(row, d)
    if y + row > W - margin: raise RuntimeError(f'플레이트 넘침: 높이 {y + row:.0f}')
    return out

if __name__ == '__main__':
    os.chdir(PROJ); os.makedirs('models/plates', exist_ok=True)
    parts = G.all_parts()
    nominal = {n: v[0] for n, v in parts.items()}
    meta = {n: {'color': v[1], 'up': list(v[2]), 'kind': v[3]} for n, v in parts.items()}
    pickle.dump(nominal, open('parts_nominal.pkl', 'wb'))
    # 출력 오브젝트: 셔터는 바탕+줄 두 색 파트를 한 오브젝트로(출력 QC 는 합친 덩어리)
    objs, printed = {}, {}
    for n, (m, col, up, kind) in parts.items():
        if n.startswith('rib_'): continue
        if n.startswith('sh_'):
            rib = parts['rib_' + n[3:]][0]; both = trimesh.util.concatenate([m, rib])
            R = align_vectors(np.asarray(up, float), [0, 0, 1.0]); tmp = both.copy(); tmp.apply_transform(R); off = -tmp.bounds[0]
            pm = []
            for mm_, c_, pn in ((m, col, n), (rib, G.YELLOW, 'rib_' + n[3:])):
                q = mm_.copy(); q.apply_transform(R); q.apply_translation(off); pm.append((q, c_, pn))
            pm[0] = (pre_expand_first_layer(pm[0][0]), pm[0][1], pm[0][2])
            objs[n] = pm; printed[n] = trimesh.boolean.union([pm[0][0], pm[1][0]], engine='manifold')
        else:
            q, R = to_print(m, up); q = pre_expand_first_layer(q); objs[n] = [(q, col, n)]; printed[n] = q
        meta[n]['print_R'] = np.asarray(align_vectors(np.asarray(up, float), [0, 0, 1.0])).tolist()
    pickle.dump(printed, open('parts.pkl', 'wb'))
    json.dump(meta, open('meta.json', 'w'), ensure_ascii=False, indent=0)
    used = set()
    for key, (path, prefixes, mats) in PLATES.items():
        sel = [n for n in objs if any(n == p or (p.endswith('_') and n.startswith(p)) for p in prefixes)]
        used |= set(sel)
        laid = pack([(n, [p[0] for p in objs[n]]) for n in sel])
        out = []
        for n, ms in laid:
            out.append({'name': n, 'parts': [(mm_, objs[n][i][1], objs[n][i][2]) for i, mm_ in enumerate(ms)]})
        write_generic_3mf(path, out, f'digit-counter {key}', material_order=mats)
    missing = set(objs) - used
    assert not missing, f'플레이트에 없는 파트: {missing}'
    ext = {n: [round(v, 1) for v in m.extents] for n, m in printed.items()}
    print('build ok', len(nominal), 'nominal parts,', len(printed), 'print objects; stroke', round(float(G.btn_stroke()), 2))
