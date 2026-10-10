#!/usr/bin/env python3
"""도구 자가검사: 상자+뚜껑(끼움 0.3, 경첩 회전) 가짜 프로젝트를 만들어 pipeline 을 돌리고
(1) 정상 설계 → 경고 0·GIF/PNG/3MF 생성, (2) 일부러 간섭시킨 설계 → ⚠ 검출 을 확인한다. 사용: python tools/selftest.py"""
import os, sys, json, time, pickle, shutil, tempfile, numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from generic3mf import write_generic_3mf; from efc import pre_expand_first_layer; import pipeline
def box(w, d, h, at=(0, 0, 0)):
    b = trimesh.creation.box(extents=[w, d, h]); b.apply_translation([at[0] + w / 2, at[1] + d / 2, at[2] + h / 2]); return b
def fixture(root, gap, axis_x=-1):
    base = trimesh.boolean.difference([box(40, 30, 15), box(34, 24, 13, (3, 3, 3))], engine='manifold')          # 벽 3, 바닥 3
    lid = box(40, 30, 2)                                                                                            # 평판 뚜껑(경첩 스윕용, 본체 위에 얹힘=접촉)
    plug = trimesh.boolean.union([box(40, 30, 2), box(34 - 2 * gap, 24 - 2 * gap, 4, (3 + gap, 3 + gap, 2))], engine='manifold')  # 플러그 뚜껑(끼움 gap/면)
    base = pre_expand_first_layer(base); lid = pre_expand_first_layer(lid); plug = pre_expand_first_layer(plug)
    parts = {'base': base, 'lid': lid, 'plug_lid': plug}; os.makedirs(os.path.join(root, 'models'), exist_ok=True); os.makedirs(os.path.join(root, 'scripts'), exist_ok=True)
    pickle.dump(parts, open(os.path.join(root, 'parts.pkl'), 'wb'))
    A = base.copy(); A.apply_translation([20, 20, 0]); B = lid.copy(); B.apply_translation([80, 20, 0]); C = plug.copy(); C.apply_translation([140, 20, 0])
    write_generic_3mf(os.path.join(root, 'models', 'A.3mf'), [{'name': 'base', 'parts': [(A, '#37474f', 'base')]}, {'name': 'lid', 'parts': [(B, '#ffb300', 'lid')]}, {'name': 'plug_lid', 'parts': [(C, '#ffb300', 'plug_lid')]}], 'selftest')
    open(os.path.join(root, 'scripts', 'asm.py'), 'w').write('''AXIS_X = %d
import numpy as np
from trimesh.transformations import rotation_matrix as R, translation_matrix as T
def define(parts):
    flip = R(np.pi, [1, 0, 0]); closed = T([0, 30, 17]) @ flip        # 뒤집어(판 z -2~0, 플러그 -6~-2) 본체 윗면 15 에 판 밑면이 닿게 → 플러그는 z 11~15 로 공동 안
    piv = [0, 30, 17]                                                  # 뒤 모서리 윗면 경첩축
    return {"states": {"분리": {"base": np.eye(4), "lid": T([0, 0, 30]) @ closed, "plug_lid": T([0, 40, 0]) @ closed},
                       "닫힘(평판)": {"base": np.eye(4), "lid": closed}, "닫힘(플러그)": {"base": np.eye(4), "plug_lid": closed}},
            "pairs": [["base", "lid", {"contact": True}], ["base", "plug_lid", {"contact": True}], ["base", "plug_lid", {"region": [[2, 2, 10.5], [38, 28, 14.9]], "min_gap": 0.25}]],
            "sweeps": [{"name": "경첩", "part": "lid", "pivot": piv, "axis": [AXIS_X, 0, 0], "base": closed, "angles": [0, 30, 60, 90, 120], "against": ["base"], "need": [0, 120]}]}
''' % axis_x)
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
def efc_stl_roundtrip_case():
    """EFC 유니온 결과를 STL 로 쓰고 다시 읽어도 닫힌 1조각인지(인정전 램프 v2 내림마루: 예전 코드는 열린 2조각)."""
    import io
    from efc import pre_expand_first_layer
    fx = trimesh.load(os.path.join(HERE, 'fixtures', 'efc_stl_roundtrip_bar.stl'), force='mesh'); fx.apply_translation([0, 0, -fx.bounds[0, 2]])
    r = pre_expand_first_layer(fx); back = trimesh.load(io.BytesIO(r.export(file_type='stl')), file_type='stl')
    nb = len(back.split(only_watertight=False)); grow = (r.bounds[1, :2] - r.bounds[0, :2]).max() - (fx.bounds[1, :2] - fx.bounds[0, :2]).max()
    print(f'[EFC STL 왕복] 닫힘 {back.is_watertight}, 조각 {nb}, 첫 층 성장 {grow:.2f} mm (기대 True, 1, >0)')
    return back.is_watertight and nb == 1 and grow > 0.1
def slit_case():
    """벽 속 0.1 mm 수평 틈이 있는 상자는 '얇은 틈' 으로 걸리고, 같은 크기 통짜 상자는 안 걸리는지(Toolbox48 v6/v8 뚜껑 줄 재현)."""
    import argparse; from qc_model import qc_part
    qa = argparse.Namespace(layer=0.2, min_wall=1.2, max_tri=200000, max_bridge=7.0, efc=0.15, single_wall=[])
    solid = trimesh.boolean.difference([box(40, 30, 10), box(36, 26, 9, (2, 2, 1))], engine='manifold')          # 벽 2 mm 통
    ring = trimesh.boolean.difference([box(40, 30, 0.1, (0, 0, 7.8)), box(36, 26, 0.1, (2, 2, 7.8))], engine='manifold')
    slit = trimesh.boolean.difference([solid, ring], engine='manifold')
    a, b = qc_part('solid', solid, qa), qc_part('slit', slit, qa)
    fa, fb = [f for f in a['flags'] if '수평 틈' in f], [f for f in b['flags'] if '수평 틈' in f]
    print(f'[벽 속 틈] 통짜 경고 {len(fa)}, 0.1 틈 경고 {len(fb)} {fb} (기대 0, 1)'); return not fa and len(fb) == 1
def wall_step_case():
    """판 쌓기 계단 바닥(0.1 판, 0.057 단차)은 '바깥 벽 단차' 로 걸리고, 같은 곡선의 링 로프트는 안 걸리는지(Toolbox48 v7 바닥 재현)."""
    from qc_model import wall_steps; from loft import loft_rings; from shapely.geometry import box as sb
    sl = []
    for z0 in np.arange(0, 1.5, 0.1):
        d = 0.575 * (1.5 - z0 - 0.05); e = trimesh.creation.extrude_polygon(sb(-20, -15, 20, 15).buffer(-d), 0.1001); e.apply_translation([0, 0, z0]); sl.append(e)
    top = box(40, 30, 6, (-20, -15, 1.5)); stair = trimesh.boolean.union(sl + [top], engine='manifold')
    sm = loft_rings([(z, sb(-20, -15, 20, 15).buffer(-0.575 * max(0, 1.5 - z))) for z in np.arange(0, 1.51, 0.1)] + [(7.5, sb(-20, -15, 20, 15))])
    a, b = wall_steps(stair)['n_heights'], wall_steps(sm)['n_heights']
    print(f'[벽 단차] 판 계단 {a}개 높이, 로프트 {b}개 (기대 ≥3, 0)'); return a >= 3 and b == 0
def mm_api_case():
    """표준 프로그램: 파이썬 mm.run 과 HTTP POST /run 결과가 같은지 + 링 로프트(판 쌓기 대신)가 계단·틈 없이 닫히는지."""
    import threading, urllib.request, http.server, mm
    from loft import loft_rings; from shapely.geometry import Polygon
    st = [(z, Polygon([(-20 + 0.5 * z, -10 + 0.5 * z), (20 - 0.5 * z, -10 + 0.5 * z), (20 - 0.5 * z, 10 - 0.5 * z), (-20 + 0.5 * z, 10 - 0.5 * z)])) for z in np.arange(0, 2.01, 0.1)]
    lf = loft_rings(st); d = tempfile.mkdtemp(); f = os.path.join(d, 'loft.stl'); lf.export(f)
    a = mm.run('slits', files=[f])
    port = 8799; t = threading.Thread(target=mm.serve, kwargs={'port': port}, daemon=True); t.start(); time.sleep(1.0)
    req = urllib.request.Request(f'http://127.0.0.1:{port}/run', data=json.dumps({'cmd': 'mm_slits', 'args': {'files': [f]}}).encode(), headers={'Content-Type': 'application/json'})
    b = json.loads(urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=60).read())
    ok = lf.is_volume and a == b and a['loft']['slit_z'] == []
    print(f'[표준 프로그램] 로프트 닫힘 {lf.is_volume}, 파이썬=HTTP {a == b}, 틈 {a["loft"]["slit_z"]}'); return ok
def scaffold_case():
    """mm new 틀 → mm make(빌드·파이프라인·Bambu 프로젝트·체크리스트)가 처음부터 통과해야 한다. 끝나면 지운다."""
    import mm
    name = f'_selftest_{os.getpid()}'; proj = os.path.join(os.path.dirname(HERE), '작업중', name)
    try:
        mm.run('new', name=name, desc='자가검사'); r = mm.run('make', config=os.path.join(proj, 'pipeline.json'))
        c = r.get('checklist', {}); bam = r.get('bambu', {})
        print(f"[새 도면 틀] make ok {r.get('ok')} · 경고 {r.get('warn')} · Bambu {[v['ok'] for v in bam.values()]} · {c.get('line', r.get('stderr', '')[-300:])}")
        return bool(r.get('ok')) and bool(bam) and all(v['ok'] for v in bam.values())
    finally: shutil.rmtree(proj, ignore_errors=True)
def agent_case():
    """mm_agent 루프를 가짜 클라이언트로 검사(API 키 불필요): 잘못된 입력은 실행하지 않고 오류로 돌려줌 · 체크리스트 미통과면 끝내지 못함(게이트) ·
    make 통과 후에야 끝남 · 거절(refusal) 턴의 도구는 실행하지 않음."""
    import mm_agent
    from types import SimpleNamespace as NS
    name = f'_agent_{os.getpid()}'; proj = os.path.join(os.path.dirname(HERE), '작업중', name)
    tu = lambda i, n, inp: NS(type='tool_use', id=f't{i}', name=n, input=inp)
    txt = lambda t: NS(type='text', text=t)
    script = [NS(stop_reason='tool_use', content=[tu(1, 'mm_new', {'nam': name})]),                     # 잘못된 인자 → INVALID_INPUT
              NS(stop_reason='tool_use', content=[tu(2, 'mm_new', {'name': name})]),
              NS(stop_reason='end_turn', content=[txt('끝났습니다')]),                                    # make 전에 끝내려 함 → 게이트
              NS(stop_reason='tool_use', content=[tu(3, 'mm_make', {'config': f'작업중/{name}/pipeline.json'})]),
              NS(stop_reason='end_turn', content=[txt('완료 보고')])]
    seen = []
    class Stream:
        def __init__(self, msg): self.msg = msg
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def __iter__(self): return iter([])
        def get_final_message(self): return self.msg
    class Msgs:
        def __init__(self, sc): self.sc = list(sc)
        def stream(self, **kw): seen.append(kw); return Stream(self.sc.pop(0))
    try:
        r = mm_agent.run_agent('새 상자 만들어줘', client=NS(beta=NS(messages=Msgs(script))), echo=False)
        u = [m for m in seen[-1]['messages'] if m['role'] == 'user']
        invalid = any(isinstance(c, list) and any(x.get('is_error') and 'INVALID_INPUT' in x['content'] for x in c) for c in (m['content'] for m in u))
        gated = any(isinstance(m['content'], str) and m['content'].startswith('[게이트]') for m in u)
        kw = seen[0]; api_ok = kw['model'] == 'claude-opus-5-5' and kw['fallbacks'] == 'default' and kw['thinking'] == {'type': 'adaptive'} and all(t.get('eager_input_streaming') for t in kw['tools'])
        ok1 = r['ok'] and invalid and gated and r['turns'] == 5 and '[x] QC' in r['final'] and api_ok
        before = os.path.exists(proj); shutil.rmtree(proj, ignore_errors=True)
        r2 = mm_agent.run_agent('x', client=NS(beta=NS(messages=Msgs([NS(stop_reason='refusal', content=[tu(9, 'mm_new', {'name': name})])]))), echo=False)
        ok2 = (not r2['ok']) and not os.path.exists(proj)
        print(f"[API 에이전트] 입력 검증 {invalid} · 게이트 {gated} · 턴 {r['turns']} · 최종 ok {r['ok']} · API 인자 {api_ok} · 거절 턴 도구 미실행 {ok2} (프로젝트 생성됐었음 {before})")
        return ok1 and ok2
    finally: shutil.rmtree(proj, ignore_errors=True)
if __name__ == '__main__':
    tmp = tempfile.mkdtemp(prefix='selftest_'); ok = efc_group_case() and efc_stl_roundtrip_case() and slit_case() and wall_step_case() and mm_api_case()
    cfg = fixture(os.path.join(tmp, 'good'), 0.3); rc = pipeline.run(cfg); rep = json.load(open(os.path.join(tmp, 'good', 'qc', 'report.json')))
    files = [os.path.join(tmp, 'good', 'qc', f) for f in ('REPORT.md', 'assembly/turntable.gif', 'motion/turntable.gif', 'plate_A/view_iso.png')]
    print('\n[정상 설계] 종료코드', rc, '| 경고', rep['warn'], '| 산출물', [os.path.exists(f) for f in files])
    ok &= (rc == 0 and all(os.path.exists(f) for f in files))
    cfg = fixture(os.path.join(tmp, 'bad'), -0.5); rc = pipeline.run(cfg); rep = json.load(open(os.path.join(tmp, 'bad', 'qc', 'report.json')))
    print('\n[간섭 설계] 종료코드', rc, '| 경고', rep['warn']); ok &= (rc == 1 and any('∩' in w for w in rep['warn']))
    cfg = fixture(os.path.join(tmp, 'tight'), 0.1); rc = pipeline.run(cfg); rep = json.load(open(os.path.join(tmp, 'tight', 'qc', 'report.json')))
    print('\n[빡빡한 끼움 0.1] 종료코드', rc, '| 경고', rep['warn']); ok &= (rc == 1 and any('간격' in w for w in rep['warn']))
    # 반대로 도는 경첩(뚜껑이 상자 안으로 회전): 0·90·120° 는 깨끗하고 30·60° 만 간섭 → 예전 판정(최소~최대)은 0~120 통과로 놓쳤다
    cfg = fixture(os.path.join(tmp, 'wrongway'), 0.3, axis_x=1); rc = pipeline.run(cfg); rep = json.load(open(os.path.join(tmp, 'wrongway', 'qc', 'report.json')))
    print('\n[반대 회전 경첩] 종료코드', rc, '| 경고', rep['warn']); ok &= (rc == 1 and any('간섭 각도' in w for w in rep['warn']))
    ok &= scaffold_case(); ok &= agent_case()
    shutil.rmtree(tmp, ignore_errors=True); print('\nSELFTEST', 'PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
