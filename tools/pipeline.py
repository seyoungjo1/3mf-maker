#!/usr/bin/env python3
"""스킬 절차(QC → 조립 검증 → 보여주기 → 3MF strict → 보고)를 설정 파일 하나로 끝까지 돌리는 파이프라인 + 게이트.
사용: python tools/pipeline.py <config.json>      (⚠ 가 하나라도 남으면 종료 코드 1 — 그 결과물은 보내지 않는다)

config.json (경로는 config 파일 위치 기준):
{
 "name": "Toolbox48 v7",
 "out": "qc/v7",
 "parts_pkl": "v7parts.pkl",                      # {이름: trimesh} 출력 방향 메시(바닥 z=0, EFC 선반영 완료)
 "plates": ["models/A.3mf", "models/B.3mf"],      # 플레이트별 일반 3MF (베드 좌표)
 "assembly": "scripts/assembly_v7.py",            # define(parts) -> {"states":{상태:{파트:4x4}}, "sweeps":[...], "extra":{이름:mesh}, "pairs":[[a,b],...], "notes":[...]}
 "colors": {"base": "#37474f", "logo": "#ffb300"},
 "qc": {"efc": 0.15, "max_bridge": 7, "min_wall": 1.2, "single_wall": []},
 "support_zones": [{"part": "base", "desc": "손잡이 귀 밑면(z 13.5)", "max_mm2": 300}],   # 설계상 돌출 — 서포트로 처리할 곳(측정값이 max_mm2 이하면 ℹ, 넘으면 ⚠)
 "min_gap": 0.3,                                  # 조립 상태에서 요구하는 최소 간격(접촉 쌍은 pairs 에 "contact": true)
 "frames": 36
}
sweep: {"name":"경첩","part":"lid","pivot":[x,y,z],"axis":[1,0,0],"base":4x4,"angles":[0,15,...],"against":["base"],"fixed":{"base":4x4}}
"""
import os, sys, json, pickle, shutil, tempfile, importlib.util, argparse, numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from qc_model import qc_part, collisions, load as load_files
from render_preview import render as render3
from check3mf import check as strict_check
from trimesh.transformations import rotation_matrix as R, translation_matrix as T
def tf(m, M): m = m.copy(); m.apply_transform(np.asarray(M, float)); return m
def inter(a, b):
    try: r = trimesh.boolean.intersection([a, b], engine='manifold'); return float(abs(r.volume)) if r.is_volume else 0.0
    except Exception: return -1.0
def gaps(a, b, n=8000, region=None):
    """b 표면 샘플에서 a 까지의 거리 분포(최소 / 1 % / 5 %). region=[[x0,y0,z0],[x1,y1,z1]] 이면 그 상자 안의 샘플만(끼움부처럼 특정 면만 볼 때)."""
    pts = b.sample(n)
    if region is not None:
        lo, hi = np.asarray(region[0], float), np.asarray(region[1], float); pts = pts[((pts >= lo) & (pts <= hi)).all(1)]
        if len(pts) < 50: return float('nan'), float('nan'), float('nan')
    d = np.sort(-trimesh.proximity.ProximityQuery(a).signed_distance(pts)); n = len(d)
    return float(d[0]), float(d[int(0.01 * n)]), float(d[int(0.05 * n)])
def run(cfg_path):
    cfg = json.load(open(cfg_path, encoding='utf-8')); base = os.path.dirname(os.path.abspath(cfg_path)); P = lambda p: os.path.join(base, p)
    out = P(cfg['out']); os.makedirs(out, exist_ok=True); warn = []; info = []; L = [f"# {cfg['name']} — 파이프라인 보고", '']
    qa = argparse.Namespace(layer=0.2, min_wall=cfg.get('qc', {}).get('min_wall', 1.2), max_tri=200000, max_bridge=cfg.get('qc', {}).get('max_bridge', 7.0),
                            efc=cfg.get('qc', {}).get('efc', 0.15), single_wall=cfg.get('qc', {}).get('single_wall', []))
    zones = {z['part']: z for z in cfg.get('support_zones', [])}
    # ---------- 1. QC: 출력 방향 파트 ----------
    parts = pickle.load(open(P(cfg['parts_pkl']), 'rb')); L += ['## 1. QC — 출력 방향 파트 (EFC %.2f 반영, 출력물 기준)' % qa.efc, '',
        '| 파트 | 삼각형 | 닫힘 | 조각 | 크기 (mm) | PLA g(통짜) | 바닥 접지 / 첫 층 mm² | 얇은 살 mm² | 오버행(한쪽) mm² | 브리지 mm² (최대 폭) | 판정 |', '|---|---|---|---|---|---|---|---|---|---|---|']
    qc = {}
    for n, m in parts.items():
        r = qc_part(n, m, qa); qc[n] = r; flags = []
        for f in r['flags']:
            if f.startswith('오버행') and n in zones:
                z = zones[n]; (info if r['overhang_mm2'] <= z['max_mm2'] else warn).append(f"{n}: 오버행 {r['overhang_mm2']} mm² → 서포트({z['desc']}, 허용 {z['max_mm2']})"); flags.append(f"ℹ 서포트: {z['desc']}" if r['overhang_mm2'] <= z['max_mm2'] else '⚠ ' + f)
            elif f.startswith('조각') and n in cfg.get('multi_body_ok', []): flags.append('ℹ 의도된 다중 조각')
            else: warn.append(f'{n}: {f}'); flags.append('⚠ ' + f)
        L.append(f"| {n} | {r['faces']:,} | {'O' if r['is_volume'] else 'X'} | {r['bodies']} | {'×'.join(map(str, r['size_mm']))} | {r['weight_g_solid']} | {r['bed_contact_mm2']} / {r['first_layer_mm2']} | {r['thin_area_mm2']} | {r['overhang_mm2']} | {r['bridge_mm2']} ({r['bridge_max_span']}) | {'; '.join(flags) if flags else '✓'} |")
    L += ['', '오버행 상위 위치: ' + ' / '.join(f"{n}: " + '; '.join(f'z={z} {a} mm² {b}' for z, a, b in r['overhang_top']) for n, r in qc.items() if r['overhang_top']), '']
    # ---------- 2. 플레이트 3MF: 충돌·베드·strict ----------
    L += ['## 2. 플레이트 3MF — 충돌·베드·lib3mf strict', '', '| 플레이트 | 파트 | 범위 x / y (mm) | 충돌 | strict 경고 | 판정 |', '|---|---|---|---|---|---|']
    tmp = tempfile.mkdtemp(prefix='p3mf_')
    for pl in cfg['plates']:
        pp = load_files([P(pl)]); allb = np.array([m.bounds for m in pp.values()]); lo, hi = allb[:, 0].min(0), allb[:, 1].max(0)
        col = collisions(pp); bad = [c for c in col if c['intersection_mm3'] > 0.01]; fl = []
        if lo[0] < 0 or lo[1] < 0 or hi[0] > 256 or hi[1] > 256 or lo[2] < -0.01: fl.append('베드 밖')
        tri = sum(len(m.faces) for m in pp.values())
        if tri > 500000: fl.append(f'파일 삼각형 {tri:,} > 500,000')
        if bad: fl.append('충돌 ' + ', '.join(f"{c['a']}∩{c['b']}={c['intersection_mm3']}" for c in bad))
        ascii_copy = os.path.join(tmp, f'plate{len(os.listdir(tmp))}.3mf'); shutil.copy(P(pl), ascii_copy); nw, ws, _ = strict_check(ascii_copy)
        if nw: fl.append(f'strict 경고 {nw}: ' + '; '.join(ws[:3]))
        for f in fl: warn.append(f'{os.path.basename(pl)}: {f}')
        L.append(f"| {os.path.basename(pl)} | {', '.join(pp)} | {lo[0]:.0f}~{hi[0]:.0f} / {lo[1]:.0f}~{hi[1]:.0f} | {len(bad)} | {nw} | {'⚠ ' + '; '.join(fl) if fl else '✓'} |")
    shutil.rmtree(tmp, ignore_errors=True); L.append('')
    # ---------- 3. 조립 검증 ----------
    asm = None
    if cfg.get('assembly'):
        spec = importlib.util.spec_from_file_location('asm', P(cfg['assembly'])); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        asm = mod.define(parts); allparts = dict(parts); allparts.update(asm.get('extra', {})); mg = cfg.get('min_gap', 0.3)
        for st, mats in asm['states'].items():
            for n in mats: assert n in allparts, f'상태 {st} 에 없는 파트 {n}'
        for sw in asm.get('sweeps', []):
            for n in [sw['part']] + list(sw['against']): assert n in allparts, f"스윕 {sw['name']} 에 없는 파트 {n}"
        L += ['## 3. 조립 검증 — 상태별 교집합·간격 (표면 샘플 거리: 최소 / 1 % / 5 %)', '', '| 상태 | A | B | 교집합 mm³ | 최소 / 1 % / 5 % mm | 판정 |', '|---|---|---|---|---|---|']
        for st, mats in asm['states'].items():
            placed = {n: tf(allparts[n], M) for n, M in mats.items()}
            for a, b, *opt in asm.get('pairs', []):
                if a not in placed or b not in placed: continue
                o = opt[0] if opt else {}; iv = inter(placed[a], placed[b]); g0, g1, g5 = gaps(placed[a], placed[b], region=o.get('region')); contact = bool(o.get('contact'))
                need = o.get('min_gap', mg)
                if o.get('region'): L.append(f"| {st} | {a} | {b} (영역 {o['region']}) | {iv:.2f} | {g0:.2f} / {g1:.2f} / {g5:.2f} | {'⚠ 간섭' if iv > 0.01 else ('⚠ 간격 %.2f < %s' % (g1, need) if g1 < need else '✓')} |")
                if o.get('region'):
                    if iv > 0.01: warn.append(f'{st} {a}∩{b} = {iv:.2f} mm³')
                    elif g1 < need: warn.append(f'{st} {a}↔{b} 영역 간격 1 % {g1:.2f} < {need}')
                    continue
                if iv > 0.01: v = '⚠ 간섭'; warn.append(f'{st} {a}∩{b} = {iv:.2f} mm³')
                elif contact: v = '접촉(의도)' if g0 > -0.02 else '⚠'
                elif g1 < need: v = f'⚠ 간격 {g1:.2f} < {need}'; warn.append(f'{st} {a}↔{b} 간격 1 % {g1:.2f} < {need}')
                else: v = '✓'
                L.append(f'| {st} | {a} | {b} | {iv:.2f} | {g0:.2f} / {g1:.2f} / {g5:.2f} | {v} |')
        L.append('')
        for sw in asm.get('sweeps', []):
            L += [f"### 스윕 — {sw['name']} ({sw['part']})", '', '| 각도 | ' + ' | '.join(f'∩{o} mm³' for o in sw['against']) + ' | 최소 간격 mm |', '|---|' + '---|' * (len(sw['against']) + 1)]
            fixed = {o: tf(allparts[o], sw.get('fixed', {}).get(o, np.eye(4))) for o in sw['against']}; ok = []
            for ang in sw['angles']:
                M = T(sw['pivot']) @ R(np.radians(ang), sw['axis']) @ T(-np.array(sw['pivot'])) @ np.asarray(sw['base'], float); mv = tf(allparts[sw['part']], M)
                ivs = [inter(fixed[o], mv) for o in sw['against']]; g = min(gaps(fixed[o], mv, 3000)[0] for o in sw['against'])
                if max(ivs) <= 0.01: ok.append(ang)
                L.append(f'| {ang} | ' + ' | '.join(f'{v:.2f}' for v in ivs) + f' | {g:.2f} |')
            rng = f"{min(ok)}~{max(ok)}°" if ok else '없음'; L += ['', f"간섭 0 범위: **{rng}** (요구: {sw.get('need', '')})", '']
            if sw.get('need') and (not ok or min(ok) > sw['need'][0] or max(ok) < sw['need'][1]): warn.append(f"스윕 {sw['name']}: 간섭 0 범위 {rng} 가 요구 {sw['need']} 를 못 채움")
        for n in asm.get('notes', []): L.append('- ' + n)
        L.append('')
    # ---------- 4. 보여주기 ----------
    colors = cfg.get('colors', {}); L += ['## 4. 렌더 (three.js, 5뷰 + 회전 GIF + 작동 GIF)', '']
    for pl in cfg['plates']:
        pp = load_files([P(pl)]); d = os.path.join(out, 'plate_' + os.path.splitext(os.path.basename(pl))[0]); render3(pp, d, colors, None, cfg.get('frames', 36)); L.append(f'- 플레이트 `{os.path.basename(pl)}`: `{os.path.relpath(d, base)}/view_*.png`, `turntable.gif`')
    if asm:
        allparts = dict(parts); allparts.update(asm.get('extra', {}))
        static = {k: v for k, v in asm['states'].items()}; shown = set(n for st in static.values() for n in st)
        sub = {n: m for n, m in allparts.items() if n in shown}
        d = os.path.join(out, 'assembly'); render3(sub, d, colors, {k: {n: np.asarray(M).ravel().tolist() for n, M in v.items()} for k, v in static.items()}, cfg.get('frames', 36))
        L.append(f'- 조립 상태(분리/닫힘/열림…): `{os.path.relpath(d, base)}/view_*_<상태>.png`, `turntable.gif`')
        motion = {}
        for sw in asm.get('sweeps', []):
            for ang in sw['angles']:
                M = T(sw['pivot']) @ R(np.radians(ang), sw['axis']) @ T(-np.array(sw['pivot'])) @ np.asarray(sw['base'], float)
                st = {o: np.asarray(sw.get('fixed', {}).get(o, np.eye(4))).ravel().tolist() for o in sw['against']}; st.update({n: np.asarray(M).ravel().tolist() for n in [sw['part']]})
                for n, M2 in sw.get('also', {}).items(): st[n] = np.asarray(M2).ravel().tolist()
                motion[f"{sw['name']} {ang}°"] = st
        if motion:
            names = set(n for st in motion.values() for n in st); sub = {n: m for n, m in allparts.items() if n in names}
            d2 = os.path.join(out, 'motion'); render3(sub, d2, colors, motion, len(motion)); L.append(f'- 작동 GIF(스윕 각도별 프레임): `{os.path.relpath(d2, base)}/turntable.gif`')
    L.append('')
    # ---------- 5. 판정 ----------
    L += ['## 5. 판정', '']
    for i in info: L.append('- ℹ ' + i)
    for w in warn: L.append('- ⚠ ' + w)
    L.append('' if warn else '- ✓ 경고 없음 — 보낼 수 있음'); L.append('')
    open(os.path.join(out, 'REPORT.md'), 'w', encoding='utf-8').write('\n'.join(L)); json.dump({'warn': warn, 'info': info, 'qc': qc}, open(os.path.join(out, 'report.json'), 'w'), ensure_ascii=False, indent=1, default=str)
    print('\n'.join(L)); print('\nREPORT:', os.path.join(out, 'REPORT.md')); return 1 if warn else 0
if __name__ == '__main__': sys.exit(run(sys.argv[1]))
