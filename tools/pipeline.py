#!/usr/bin/env python3
"""스킬 절차(QC → 조립 검증 → 보여주기 → 3MF strict → 보고)를 설정 파일 하나로 끝까지 돌리는 파이프라인 + 게이트.
사용: python tools/pipeline.py <config.json>      (⚠ 가 하나라도 남으면 종료 코드 1 — 그 결과물은 보내지 않는다)

config.json (경로는 config 파일 위치 기준):
{
 "name": "Toolbox48 v7",
 "out": "qc/v7",
 "parts_pkl": "v7parts.pkl",                      # {이름: trimesh} 출력 방향 메시(바닥 z=0, EFC 선반영 완료) — QC 용
 "assembly_parts_pkl": "v7parts_nominal.pkl",     # (선택) EFC 선반영 전 공칭 형상 — 조립 검사·렌더 용
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
def log(*a): print('[pipeline]', *a, file=sys.stderr, flush=True)
def _flush(out, L): open(os.path.join(out, 'REPORT.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n\n(진행 중…)\n')
def tf(m, M): m = m.copy(); m.apply_transform(np.asarray(M, float)); return m
def _bodies(m):
    if len(m.faces) < 20000: return [m]
    bs = m.split(only_watertight=False); return bs if 1 < len(bs) <= 400 else [m]
def inter(a, b):
    """교집합 부피. 조각이 많은 파트(명판 48장 같은 내용물)는 조각별로 나눠 더한다(한 메시로 하면 manifold 가 매우 느림). 바운딩 박스가 안 겹치는 조각은 건너뜀."""
    tot = 0.0
    for x in _bodies(a):
        for y in _bodies(b):
            if (x.bounds[1] < y.bounds[0]).any() or (y.bounds[1] < x.bounds[0]).any(): continue
            try: r = trimesh.boolean.intersection([x, y], engine='manifold'); tot += float(abs(r.volume)) if r.is_volume else 0.0
            except Exception: return -1.0
    return tot
def gaps(a, b, n=8000, region=None):
    """b 표면 샘플에서 a 까지의 거리 분포(최소 / 1 % / 5 %). region=[[x0,y0,z0],[x1,y1,z1]] 이면 그 상자 안의 샘플만(끼움부처럼 특정 면만 볼 때)."""
    pts = b.sample(n)
    if region is not None:
        lo, hi = np.asarray(region[0], float), np.asarray(region[1], float); pts = pts[((pts >= lo) & (pts <= hi)).all(1)]
        if len(pts) < 50: return float('nan'), float('nan'), float('nan')
    # 부호 없는 최근접 거리(간섭 여부는 manifold 교집합 부피로 따로 판정 — signed_distance 의 contains 레이 캐스팅은 메모리 폭주).
    # 먼 점은 closest_point 후보 삼각형이 폭증하므로(2천만 배열) 정점 KD-트리 거리로 먼저 거르고 5 mm 이내 점만 정확히 잰다.
    pq = trimesh.proximity.ProximityQuery(a); dv, _ = pq.vertex(pts); d = np.asarray(dv, float).copy(); near = d < 5.0
    if near.any():
        _, dn, _ = trimesh.proximity.closest_point(a, pts[near]); d[near] = dn
    d = np.sort(d); n = len(d)
    return float(d[0]), float(d[int(0.01 * n)]), float(d[int(0.05 * n)])
def check_assembly(asm, allparts, mg, L, warn, render_only=False):
    """조립 검증(상태별 교집합·간격·영역 간격, 각도 스윕). pipeline.run 과 mm.py assemble 이 같은 코드를 쓴다."""
    L += ['## 3. 조립 검증 — 상태별 교집합·간격 (표면 샘플 거리: 최소 / 1 % / 5 %)', '', '| 상태 | A | B | 교집합 mm³ | 최소 / 1 % / 5 % mm | 판정 |', '|---|---|---|---|---|---|']
    for st, mats in ([] if render_only else asm['states'].items()):
        log('state', st); placed = {n: tf(allparts[n], M) for n, M in mats.items()}
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
    for sw in ([] if render_only else asm.get('sweeps', [])):
        L += [f"### 스윕 — {sw['name']} ({sw['part']})", '', '| 각도 | ' + ' | '.join(f'∩{o} mm³' for o in sw['against']) + ' | 최소 간격 mm |', '|---|' + '---|' * (len(sw['against']) + 1)]
        fixed = {o: tf(allparts[o], sw.get('fixed', {}).get(o, np.eye(4))) for o in sw['against']}; ok = []
        for ang in sw['angles']:
            log('sweep', sw['name'], ang); M = T(sw['pivot']) @ R(np.radians(ang), sw['axis']) @ T(-np.array(sw['pivot'])) @ np.asarray(sw['base'], float); mv = tf(allparts[sw['part']], M)
            ivs = [inter(fixed[o], mv) for o in sw['against']]; g = min(gaps(fixed[o], mv, 3000)[0] for o in sw['against'])
            if min(ivs) < 0: warn.append(f"스윕 {sw['name']} {ang}°: 교집합 계산 실패(불리언) — 판정 불가")
            if 0 <= max(ivs) <= 0.01 and min(ivs) >= 0: ok.append(ang)
            L.append(f'| {ang} | ' + ' | '.join(f'{v:.2f}' for v in ivs) + f' | {g:.2f} |')
        # 간섭 0 범위는 '연속' 구간으로만 말한다(예전: 간섭 0 각도의 최소~최대 → 0·90·120 만 깨끗하고 30·60 이 간섭이어도 0~120 으로 통과하던 구멍)
        angs = list(sw['angles']); runs, cur = [], []
        for x in angs:
            if x in ok: cur.append(x)
            elif cur: runs.append(cur); cur = []
        if cur: runs.append(cur)
        rng = ', '.join(f'{r[0]}~{r[-1]}°' for r in runs) if runs else '없음'; badang = [x for x in angs if x not in ok]
        L += ['', f"간섭 0 범위: **{rng}** (요구: {sw.get('need', '')})" + (f' · 간섭 각도 {badang}' if badang else ''), '']
        if sw.get('need'):
            lo, hi = sw['need']; inside = [x for x in angs if lo <= x <= hi]; bad_in = [x for x in inside if x not in ok]
            if not inside or min(inside) > lo or max(inside) < hi: warn.append(f"스윕 {sw['name']}: 각도 목록 {angs} 이 요구 {sw['need']} 를 덮지 못함")
            elif bad_in: warn.append(f"스윕 {sw['name']}: 요구 {sw['need']} 안 간섭 각도 {bad_in} (간섭 0 범위 {rng})")


def run(cfg_path, render_only=False):
    cfg = json.load(open(cfg_path, encoding='utf-8')); base = os.path.dirname(os.path.abspath(cfg_path)); P = lambda p: os.path.join(base, p)
    out = P(cfg['out']); os.makedirs(out, exist_ok=True); warn = []; info = []; L = [f"# {cfg['name']} — 파이프라인 보고", '']
    # 단계별 기록(report.json 'stages') — mm checklist 가 이것으로 체크리스트를 자동으로 채운다
    stages = {'qc': {}, 'plates': [], 'assembly': None, 'renders': {}, 'efc': {'qc_efc': cfg.get('qc', {}).get('efc', 0.15), 'nominal_pkl': cfg.get('assembly_parts_pkl')},
              'support_zones': cfg.get('support_zones', [])}
    qa = argparse.Namespace(layer=0.2, min_wall=cfg.get('qc', {}).get('min_wall', 1.2), max_tri=200000, max_bridge=cfg.get('qc', {}).get('max_bridge', 7.0),
                            efc=cfg.get('qc', {}).get('efc', 0.15), single_wall=cfg.get('qc', {}).get('single_wall', []))
    zones = {z['part']: z for z in cfg.get('support_zones', [])}
    if render_only: L.append('(렌더 전용 실행 — 검사 결과는 이전 REPORT.md 참조)')
    # 근거 있는 허용: [{"part","flag"(얇은 살|브리지|조각|안착|가늘고),"max","desc"}] — 측정값이 max 이하면 ℹ 로 낮춘다(이유 필수)
    KEY = {'얇은 살': 'thin_area_mm2', '브리지': 'bridge_max_span', '조각': 'bodies', '오버행': 'overhang_mm2'}
    accepted = cfg.get('accepted', [])
    def accept(n, f, r):
        for a in accepted:
            if a['part'] == n and a['flag'] in f and r.get(KEY.get(a['flag'], ''), 0) <= a.get('max', 1e9): return a
        return None
    # ---------- 1. QC: 출력 방향 파트 ----------
    parts = pickle.load(open(P(cfg['parts_pkl']), 'rb')); L += ['## 1. QC — 출력 방향 파트 (EFC %.2f 반영, 출력물 기준)' % qa.efc, '',
        '| 파트 | 삼각형 | 닫힘 | 조각 | 크기 (mm) | PLA g(통짜) | 바닥 접지 / 첫 층 mm² | 얇은 살 mm² | 오버행(한쪽) mm² | 브리지 mm² (최대 폭) | 판정 |', '|---|---|---|---|---|---|---|---|---|---|---|']
    qc = {}
    for n, m in parts.items():
        if render_only: break
        log('QC', n, len(m.faces), 'faces'); r = qc_part(n, m, qa); qc[n] = r; flags = []
        for f in r['flags']:
            if f.startswith('오버행') and n in zones:
                z = zones[n]; (info if r['overhang_mm2'] <= z['max_mm2'] else warn).append(f"{n}: 오버행 {r['overhang_mm2']} mm² → 서포트({z['desc']}, 허용 {z['max_mm2']})"); flags.append(f"ℹ 서포트: {z['desc']}" if r['overhang_mm2'] <= z['max_mm2'] else '⚠ ' + f)
            elif f.startswith('조각') and n in cfg.get('multi_body_ok', []): flags.append('ℹ 의도된 다중 조각')
            elif accept(n, f, r): a = accept(n, f, r); info.append(f"{n}: {f} → 허용({a['desc']})"); flags.append(f"ℹ {a['flag']} 허용: {a['desc']}")
            else: warn.append(f'{n}: {f}'); flags.append('⚠ ' + f)
        stages['qc'][n] = {'flags': flags, 'overhang_mm2': r['overhang_mm2'], 'is_volume': r['is_volume'], 'bodies': r['bodies']}
        L.append(f"| {n} | {r['faces']:,} | {'O' if r['is_volume'] else 'X'} | {r['bodies']} | {'×'.join(map(str, r['size_mm']))} | {r['weight_g_solid']} | {r['bed_contact_mm2']} / {r['first_layer_mm2']} | {r['thin_area_mm2']} | {r['overhang_mm2']} | {r['bridge_mm2']} ({r['bridge_max_span']}) | {'; '.join(flags) if flags else '✓'} |")
    L += ['', '오버행 상위 위치: ' + ' / '.join(f"{n}: " + '; '.join(f'z={z} {a} mm² {b}' for z, a, b in r['overhang_top']) for n, r in qc.items() if r['overhang_top']),
          '', '브리지 상위 위치(z, mm², 폭): ' + ' / '.join(f"{n}: " + '; '.join(f'z={z} {a} mm² 폭 {w}' for z, a, w in r['bridge_top']) for n, r in qc.items() if r.get('bridge_top')),
          '', '얇은 살 위치: ' + ' / '.join(f"{n}: {r['thin_area_mm2']} mm² z={r['thin_at_z']} {r['thin_bounds']}" for n, r in qc.items() if r['thin_area_mm2'] > 2), '']
    # ---------- 2. 플레이트 3MF: 충돌·베드·strict ----------
    L += ['## 2. 플레이트 3MF — 충돌·베드·lib3mf strict', '', '| 플레이트 | 파트 | 범위 x / y (mm) | 충돌 | strict 경고 | 판정 |', '|---|---|---|---|---|---|']
    tmp = tempfile.mkdtemp(prefix='p3mf_')
    for pl in ([] if render_only else cfg['plates']):
        log('plate', pl); pp = load_files([P(pl)]); allb = np.array([m.bounds for m in pp.values()]); lo, hi = allb[:, 0].min(0), allb[:, 1].max(0)
        col = collisions(pp); bad = [c for c in col if c['intersection_mm3'] > 0.01]; fl = []
        if lo[0] < 0 or lo[1] < 0 or hi[0] > 256 or hi[1] > 256 or lo[2] < -0.01: fl.append('베드 밖')
        tri = sum(len(m.faces) for m in pp.values())
        if tri > 500000: fl.append(f'파일 삼각형 {tri:,} > 500,000')
        if bad: fl.append('충돌 ' + ', '.join(f"{c['a']}∩{c['b']}={c['intersection_mm3']}" for c in bad))
        ascii_copy = os.path.join(tmp, f'plate{len(os.listdir(tmp))}.3mf'); shutil.copy(P(pl), ascii_copy); nw, ws, _ = strict_check(ascii_copy)
        if nw: fl.append(f'strict 경고 {nw}: ' + '; '.join(ws[:3]))
        for f in fl: warn.append(f'{os.path.basename(pl)}: {f}')
        stages['plates'].append({'file': pl, 'strict_warnings': nw, 'collisions': len(bad), 'in_bed': '베드 밖' not in fl, 'triangles': tri})
        L.append(f"| {os.path.basename(pl)} | {', '.join(pp)} | {lo[0]:.0f}~{hi[0]:.0f} / {lo[1]:.0f}~{hi[1]:.0f} | {len(bad)} | {nw} | {'⚠ ' + '; '.join(fl) if fl else '✓'} |")
    shutil.rmtree(tmp, ignore_errors=True); L.append(''); _flush(out, L)
    # ---------- 3. 조립 검증 ----------
    asm = None
    if cfg.get('assembly'):
        spec = importlib.util.spec_from_file_location('asm', P(cfg['assembly'])); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        # 조립 검사는 EFC 선반영 전(공칭) 형상으로 — 첫 층 +0.15 스커트는 출력물에서 슬라이서가 깎아 없어지는 것이라 끼움 판정에 넣으면 안 된다
        nominal = pickle.load(open(P(cfg['assembly_parts_pkl']), 'rb')) if cfg.get('assembly_parts_pkl') else parts
        asm = mod.define(nominal); allparts = dict(nominal); allparts.update(asm.get('extra', {})); mg = cfg.get('min_gap', 0.3)
        for st, mats in asm['states'].items():
            for n in mats: assert n in allparts, f'상태 {st} 에 없는 파트 {n}'
        for sw in asm.get('sweeps', []):
            for n in [sw['part']] + list(sw['against']): assert n in allparts, f"스윕 {sw['name']} 에 없는 파트 {n}"
        nw0 = len(warn); check_assembly(asm, allparts, mg, L, warn, render_only)
        stages['assembly'] = {'states': list(asm['states']), 'pairs': len(asm.get('pairs', [])), 'sweeps': [sw['name'] for sw in asm.get('sweeps', [])], 'warnings': len(warn) - nw0}
        for n in asm.get('notes', []): L.append('- ' + n)
        L.append(''); _flush(out, L)
    # ---------- 4. 보여주기 ----------
    colors = cfg.get('colors', {}); L += ['## 4. 렌더 (three.js, 5뷰 + 회전 GIF + 작동 GIF)', '']
    def status_of(pp, extra=''):
        allb = np.array([m.bounds for m in pp.values()]); lo, hi = allb[:, 0].min(0), allb[:, 1].max(0)
        return f'완료 — 모델 크기 {hi[0]-lo[0]:.1f} × {hi[1]-lo[1]:.1f} × {hi[2]-lo[2]:.1f} mm · 파트 {len(pp)}개: ' + ', '.join(pp) + (' · ' + extra if extra else '')
    for pl in cfg['plates']:
        log('render plate', pl); pp = load_files([P(pl)]); d = os.path.join(out, 'plate_' + os.path.splitext(os.path.basename(pl))[0]); render3(pp, d, colors, None, cfg.get('frames', 36), status=status_of(pp)); stages['renders'][os.path.relpath(d, base)] = 'plate'; L.append(f'- 플레이트 `{os.path.basename(pl)}`: `{os.path.relpath(d, base)}/view_*.png`, `turntable.gif`')
    if asm:
        allparts = dict(nominal); allparts.update(asm.get('extra', {}))
        static = {k: v for k, v in asm['states'].items()}; shown = set(n for st in static.values() for n in st)
        sub = {n: m for n, m in allparts.items() if n in shown}
        log('render assembly'); d = os.path.join(out, 'assembly'); render3(sub, d, colors, {k: {n: np.asarray(M).ravel().tolist() for n, M in v.items()} for k, v in static.items()}, cfg.get('frames', 36), status=status_of({n: tf(sub[n], M) for n, M in list(static.values())[1].items()} if len(static) > 1 else sub, cfg['name']))
        stages['renders'][os.path.relpath(d, base)] = 'assembly'
        L.append(f'- 조립 상태(분리/닫힘/열림…): `{os.path.relpath(d, base)}/view_*_<상태>.png`, `turntable.gif`')
        motion = {}
        for sw in asm.get('sweeps', []):
            for ang in sw['angles']:
                M = T(sw['pivot']) @ R(np.radians(ang), sw['axis']) @ T(-np.array(sw['pivot'])) @ np.asarray(sw['base'], float)
                st = {o: np.asarray(sw.get('fixed', {}).get(o, np.eye(4))).ravel().tolist() for o in sw['against']}; st.update({n: np.asarray(M).ravel().tolist() for n in [sw['part']]})
                for n, M2 in sw.get('also', {}).items(): st[n] = np.asarray(M2).ravel().tolist()
                for n in sw.get('follow', []): st[n] = np.asarray(M).ravel().tolist()        # 움직이는 파트와 같이 움직이는 파트(뚜껑의 로고)
                motion[f"{sw['name']} {ang}°"] = st
        if motion:
            names = set(n for st in motion.values() for n in st); sub = {n: m for n, m in allparts.items() if n in names}
            log('render motion', len(motion), 'frames'); d2 = os.path.join(out, 'motion'); render3(sub, d2, colors, motion, len(motion), status=cfg['name'] + ' · 작동(스윕)'); stages['renders'][os.path.relpath(d2, base)] = 'motion'; L.append(f'- 작동 GIF(스윕 각도별 프레임): `{os.path.relpath(d2, base)}/turntable.gif`')
    L.append('')
    # ---------- 5. 판정 ----------
    L += ['## 5. 판정', '']
    for i in info: L.append('- ℹ ' + i)
    for w in warn: L.append('- ⚠ ' + w)
    L.append('' if warn else '- ✓ 경고 없음 — 보낼 수 있음'); L.append('')
    if render_only: print('\n'.join(L)); print('\n렌더만 다시 함 — REPORT.md 유지'); return 0
    open(os.path.join(out, 'REPORT.md'), 'w', encoding='utf-8').write('\n'.join(L)); json.dump({'warn': warn, 'info': info, 'qc': qc, 'stages': stages}, open(os.path.join(out, 'report.json'), 'w'), ensure_ascii=False, indent=1, default=str)
    print('\n'.join(L)); print('\nREPORT:', os.path.join(out, 'REPORT.md')); return 1 if warn else 0
if __name__ == '__main__': sys.exit(run(sys.argv[1], render_only='--render-only' in sys.argv))
