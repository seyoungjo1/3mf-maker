#!/usr/bin/env python3
"""3D 출력 모델 품질검사 + 렌더링 — 보내기 전 항상 돌린다 (SKILL 3절).
사용: python tools/qc_model.py <file.3mf | a.stl b.stl ...> --out <dir> [--layer 0.2] [--min-wall 1.2] [--max-tri 200000] [--max-bridge 7] [--efc 0.15] [--single-wall 이름,…] [--no-render]
결과: <dir>/report.md, report.json, render_iso/top/side/bottom.png, assembly.png
검사: 닫힘(watertight/is_volume/조각 수), 삼각형 예산, 크기·부피·PLA 무게, 바닥 접지 면적·비율, 얇은 살(<min-wall), 작은 부품,
      오버행 규칙(0.2 층당 0.115)을 한쪽 지지(캔틸레버)와 양쪽 지지(브리지, 폭 ≤ --max-bridge 7 허용)로 나눠 보고, 파트 간 충돌(교집합 부피)·최소 간격.
"""
import os, sys, json, argparse, numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from load3mf import load_parts
from overhang import classify as overhang_classify, layer_poly
PLA_DENSITY = 1.24e-3   # g/mm³

def load(paths):
    parts = {}
    for p in paths:
        if p.lower().endswith('.3mf'):
            for n, m in load_parts(p).items(): parts[n] = m
        else:
            m = trimesh.load(p, force='mesh'); parts[os.path.splitext(os.path.basename(p))[0]] = m
    return parts

def thin_regions(mesh, min_wall, zs):
    """층 단면을 반지름 min_wall/2 로 열기(opening)해 사라지는 영역 = 그보다 얇은 살."""
    r = min_wall / 2; worst = (0.0, None, None)
    for z in zs:
        p = layer_poly(mesh, z)
        if p.is_empty: continue
        thin = p.difference(p.buffer(-r).buffer(r + 0.01, join_style='mitre'))      # mitre: 직각 모서리 쐐기 오탐 방지
        thin = unary_union([g for g in getattr(thin, 'geoms', [thin]) if g.area > 0.2]) if not thin.is_empty else thin; a = thin.area
        if a > worst[0]: worst = (a, round(z, 2), tuple(round(v, 1) for v in thin.bounds))
    return worst

from shapely.ops import unary_union
def internal_gaps(mesh, n=1500, max_gap=0.4, seed=0):
    """벽 속 얇은 틈(슬릿) 검사: x·y·z 방향 레이를 쏴서, 파트를 빠져나왔다가 max_gap 안에 다시 들어가는 구간을 센다.
    슬라이서는 틈의 위아래(또는 양옆)를 각각 윗면/아랫면·벽으로 처리해 출력물 옆면에 줄이 생긴다(Toolbox48 v6/v8 뚜껑 z 7.81~7.91 0.1 mm 틈).
    반환: [(축, 틈 길이, 틈 시작 좌표 xyz), ...]"""
    rng = np.random.default_rng(seed); b = mesh.bounds; out = []
    for ax in range(3):
        o = np.column_stack([rng.uniform(b[0, i] + 0.05, b[1, i] - 0.05, n) for i in range(3)]); o[:, ax] = b[0, ax] - 1.0
        d = np.zeros((n, 3)); d[:, ax] = 1.0
        loc, ri, _ = mesh.ray.intersects_location(o, d, multiple_hits=True)
        if not len(loc): continue
        order = np.lexsort((loc[:, ax], ri)); loc, ri = loc[order], ri[order]
        for r in np.unique(ri):
            t = loc[ri == r, ax]; t = t[np.r_[True, np.diff(t) > 1e-4]]          # 같은 점 중복 교점 제거
            for k in range(1, len(t) - 1, 2):                                    # 0 들어감, 1 나감, 2 들어감 … → 나감~들어감 = 바깥 구간
                g = t[k + 1] - t[k]
                if 0.01 < g < max_gap: p = o[r].copy(); p[ax] = t[k]; out.append((ax, round(float(g), 3), tuple(np.round(p, 2))))
    return out
def wall_steps(mesh, z_range=None, n_dir=48, step=0.02, max_step=0.3, dz=0.02, min_dirs=3):
    """바깥 벽 단차(출력물 가로줄) 검사: 파트 중심에서 n_dir 방향으로 바깥 벽 거리를 z dz 간격으로 재서,
    이웃 높이 사이 벽이 step~max_step mm 갑자기 튀는 곳(이웃 높이의 변화보다 2.5배 이상)을 높이별로 센다.
    0.3 mm 넘는 건 귀·받침 같은 형상 경계로 본다. 원인 예: 판 쌓기 계단(v7 바닥 0.1 판), 원본 벽과 새 곡면의 어긋남(각진 모서리 vs 원호)."""
    import collections
    b = mesh.bounds; c = (b[0] + b[1]) / 2; R = float(np.linalg.norm(b[1, :2] - b[0, :2]))
    z0, z1 = z_range if z_range else (b[0, 2] + dz, b[1, 2] - dz); zs = np.arange(z0, z1, dz)
    jumps = collections.Counter(); worst = collections.defaultdict(float); where = collections.defaultdict(list)
    for a in np.linspace(0, 2 * np.pi, n_dir, endpoint=False):
        d = np.array([-np.cos(a), -np.sin(a), 0.0]); o = np.column_stack([np.full(len(zs), c[0] + R * np.cos(a)), np.full(len(zs), c[1] + R * np.sin(a)), zs])
        loc, ri, _ = mesh.ray.intersects_location(o, np.tile(d, (len(zs), 1)), multiple_hits=False)
        if len(ri) == 0: continue                                    # 이 방향은 빈 곳(떨어진 두 조각 사이)
        r = np.full(len(zs), np.nan); hit = np.full((len(zs), 2), np.nan); r[ri] = np.linalg.norm(loc[:, :2] - c[:2], axis=1); hit[ri] = loc[:, :2]
        dr = np.abs(np.diff(r)); prev = np.r_[np.nan, dr[:-1]]; nxt = np.r_[dr[1:], np.nan]
        for i in np.where((dr > step) & (dr < max_step))[0]:
            if not (dr[i] > 2.5 * np.nanmax([prev[i], nxt[i], 1e-9])): continue
            zk = round(float(zs[i]), 2); jumps[zk] += 1; worst[zk] = max(worst[zk], float(dr[i])); where[zk].append([round(float(np.degrees(a))), round(float(hit[i, 0]), 1), round(float(hit[i, 1]), 1)])
    rows = sorted(((z, n, round(worst[z], 3), where[z][:6]) for z, n in jumps.items() if n >= min_dirs), key=lambda t: -t[1])
    return {'steps': rows[:20], 'n_heights': len(rows)}
def qc_part(name, m, args):
    r = {'name': name, 'faces': int(len(m.faces)), 'vertices': int(len(m.vertices))}
    r['watertight'] = bool(m.is_watertight); r['is_volume'] = bool(m.is_volume)
    sh = m.split(only_watertight=False)
    # 안쪽을 향한 닫힌 껍질(부피 < 0) = 속이 빈 공간(묻는 자석·너트 자리) — 따로 떨어진 조각이 아니다
    r['voids'] = int(sum(1 for s in sh if s.is_watertight and s.volume < 0)); r['bodies'] = int(len(sh)) - r['voids']
    b = m.bounds; r['size_mm'] = [round(float(v), 2) for v in (b[1] - b[0])]; r['min_z'] = round(float(b[0, 2]), 3)
    vol = float(abs(m.volume)) if m.is_volume else float('nan'); r['volume_cm3'] = round(vol / 1000, 2); r['weight_g_solid'] = round(vol * PLA_DENSITY, 1)
    sel = (m.face_normals[:, 2] < -0.99) & (m.triangles_center[:, 2] < b[0, 2] + 0.05)
    r['bed_contact_mm2'] = round(float(m.area_faces[sel].sum()), 1)
    foot = layer_poly(m, b[0, 2] + args.layer / 2 + 0.0137); r['first_layer_mm2'] = round(foot.area, 1)
    hull = m.convex_hull; hb = hull.bounds; r['footprint_hull_mm2'] = round(float(layer_poly(hull, b[0, 2] + 0.05).area), 1) if hull.is_volume else None
    h = r['size_mm'][2]; w = min(r['size_mm'][0], r['size_mm'][1]); r['aspect_h_over_w'] = round(h / w, 2) if w else None
    zs = np.linspace(b[0, 2] + 0.3, b[1, 2] - 0.3, 12) if h > 1 else [b[0, 2] + h / 2]
    ta, tz, tb = thin_regions(m, args.min_wall, zs); r['thin_area_mm2'] = round(ta, 1); r['thin_at_z'] = tz; r['thin_bounds'] = tb
    gaps = [g for g in internal_gaps(m) if g[0] == 2]          # 수평 틈(z 방향)만 — x·y 방향 좁은 틈은 경첩 여유 같은 설계 틈이 많다
    import collections; cl = collections.Counter(round(g[2][2], 1) for g in gaps)
    slit_z = sorted(z for z, c in cl.items() if c >= 10)          # 같은 높이에 10개 이상 = 벽을 가로지르는 틈(곡면 스침 잡음은 1~10개)
    r['internal_gaps'] = len(gaps); r['slit_z'] = slit_z
    oc = overhang_classify(m, args.layer, 0.115, args.max_bridge, efc=args.efc); tot = oc['overhang_mm2']
    r['overhang_mm2'] = round(tot, 1); r['overhang_top'] = oc['overhang_top'][:4]
    r['bridge_mm2'] = round(oc['bridge_mm2'], 1); r['bridge_max_span'] = round(oc['bridge_max_span'], 1); r['bridge_top'] = oc['bridge_top'][:4]
    flags = []
    if not r['watertight'] or not r['is_volume']: flags.append('열린 메시(watertight 아님) — 출력 금지')
    if r['bodies'] > 1: flags.append(f'조각 {r["bodies"]}개로 분리됨')
    if r['voids']: r['note'] = (r.get('note', '') + ' ' if r.get('note') else '') + f'속 빈 공간 {r["voids"]}개(묻는 부품 자리 — 출력 중 일시정지 높이 확인)'
    ws = wall_steps(m, z_range=(b[0, 2] + 0.25, b[1, 2] - 0.02)); r['wall_steps'] = ws['steps'][:6]     # 첫 층(EFC +0.15 선반영 턱, 슬라이서가 깎음)은 제외
    if ws['n_heights']:
        flags.append(f"바깥 벽 단차 0.02~0.3 mm {ws['n_heights']}개 높이 (z, 방향 수, 최대 mm): {[t[:3] for t in ws['steps'][:4]]} — 출력물에 가로줄")
    if slit_z:
        flags.append(f'벽 속 수평 틈(<0.4 mm) z={slit_z} (레이 {sum(cl[z] for z in slit_z)}개) — 출력물 옆면에 줄이 생김')
    if r['faces'] > args.max_tri: flags.append(f'삼각형 {r["faces"]:,} > 예산 {args.max_tri:,} — 단순화 필요')
    if max(r['size_mm']) < 5 or (vol == vol and vol < 50): flags.append('너무 작은 부품(최대 치수 <5 mm 또는 부피 <50 mm³)')
    if r['bed_contact_mm2'] < 0.3 * r['first_layer_mm2']: flags.append(f'안착 불량: 바닥 접지 {r["bed_contact_mm2"]} mm² < 첫 층 {r["first_layer_mm2"]} mm² 의 30 %')
    if r['bed_contact_mm2'] < 100: flags.append(f'바닥 접지 {r["bed_contact_mm2"]} mm² < 100 mm² — 브림 필수')
    if r['aspect_h_over_w'] and r['aspect_h_over_w'] > 3: flags.append(f'가늘고 높음(높이/폭 {r["aspect_h_over_w"]}) — 넘어질 위험, 브림')
    if ta > 2.0:
        if name in args.single_wall: r['note'] = f'단일 벽(발광 갓) {ta:.0f} mm² — 의도된 0.8 mm 두 줄 벽'
        else: flags.append(f'{args.min_wall} mm 보다 얇은 살 {ta:.1f} mm² (z={tz}, x/y {tb})')
    if tot > 50: flags.append(f'오버행(한쪽 지지) 규칙 위반 {tot:.0f} mm² (서포트 또는 재설계)')
    if r['bridge_max_span'] > args.max_bridge: flags.append(f'브리지 폭 {r["bridge_max_span"]} mm > {args.max_bridge} mm')
    r['flags'] = flags; return r

def collisions(parts):
    names = list(parts); out = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = parts[names[i]], parts[names[j]]
            if not (a.is_volume and b.is_volume): continue
            ba, bb = a.bounds, b.bounds
            if (ba[1] < bb[0] - 2).any() or (bb[1] < ba[0] - 2).any(): continue
            try: inter = a.intersection(b, engine='manifold'); iv = float(abs(inter.volume)) if inter.is_volume else 0.0
            except Exception: iv = -1.0
            pts = b.sample(4000); d = trimesh.proximity.ProximityQuery(a).signed_distance(pts); mind = float(-d.max()) if len(d) else None
            out.append({'a': names[i], 'b': names[j], 'intersection_mm3': round(iv, 3), 'min_gap_mm': round(mind, 3) if mind is not None else None})
    return out

def render(parts, outdir, colors=None):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    try: import fast_simplification as fs
    except ImportError: fs = None
    palette = ['#4e8fb3', '#f2af38', '#7dbb6a', '#c76f6f', '#9b7fc9', '#8a8a8a']
    tris = []
    for k, (n, m) in enumerate(parts.items()):
        V, F = np.asarray(m.vertices, float), np.asarray(m.faces, np.int64)
        if fs and len(F) > 40000:
            V, F = fs.simplify(V, F, target_count=40000)
        col = (colors or {}).get(n, palette[k % len(palette)]); tris.append((V, F, col, n))
    allv = np.vstack([V for V, _, _, _ in tris]); lo, hi = allv.min(0), allv.max(0); c = (lo + hi) / 2; span = (hi - lo).max() / 2 + 2
    light = np.array([0.3, -0.5, 0.8]); light /= np.linalg.norm(light)
    views = {'iso': (28, -55), 'top': (90, -90), 'side': (0, -90), 'bottom': (-90, -90)}
    for vn, (el, az) in views.items():
        fig = plt.figure(figsize=(9, 7)); ax = fig.add_subplot(111, projection='3d')
        for V, F, col, n in tris:
            T = V[F]; nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12)
            sh = 0.45 + 0.55 * np.clip(nrm @ light, 0, 1)
            rgb = np.array(matplotlib.colors.to_rgb(col)); fc = np.clip(rgb[None, :] * sh[:, None], 0, 1)
            pc = Poly3DCollection(T, facecolors=fc, edgecolors='none'); ax.add_collection3d(pc)
        if vn in ('iso', 'top'):   # 베드 256×256 격자
            for g in range(0, 257, 32): ax.plot([g, g], [0, 256], [0, 0], color='#bbb', lw=.4); ax.plot([0, 256], [g, g], [0, 0], color='#bbb', lw=.4)
        ax.set_xlim(c[0] - span, c[0] + span); ax.set_ylim(c[1] - span, c[1] + span); ax.set_zlim(max(0, c[2] - span), c[2] + span)
        ax.view_init(elev=el, azim=az); ax.set_box_aspect((1, 1, 1)); ax.set_axis_off()
        ax.set_title(f'{vn}  ·  ' + ', '.join(n for _, _, _, n in tris), fontsize=9)
        fig.savefig(os.path.join(outdir, f'render_{vn}.png'), dpi=90, bbox_inches='tight'); plt.close(fig)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('files', nargs='+'); ap.add_argument('--out', required=True)
    ap.add_argument('--nozzle', type=float, default=0.4); ap.add_argument('--layer', type=float, default=0.2)
    ap.add_argument('--min-wall', type=float, default=1.2); ap.add_argument('--max-tri', type=int, default=200000); ap.add_argument('--no-render', action='store_true')
    ap.add_argument('--max-bridge', type=float, default=7.0); ap.add_argument('--efc', type=float, default=0.15, help='슬라이서 코끼리발 보정(첫 층 윤곽 깎임) — 출력물 기준으로 1→2층 단차를 센다'); ap.add_argument('--single-wall', default='', help='의도된 단일 벽(0.8) 파트 이름, 쉼표 구분')
    args = ap.parse_args(); os.makedirs(args.out, exist_ok=True); args.single_wall = [t for t in args.single_wall.split(',') if t]
    parts = load(args.files); rep = {'files': args.files, 'parts': [qc_part(n, m, args) for n, m in parts.items()], 'collisions': collisions(parts)}
    rep['total_faces'] = sum(p['faces'] for p in rep['parts']); rep['total_weight_g_solid'] = round(sum(p['weight_g_solid'] for p in rep['parts'] if p['weight_g_solid'] == p['weight_g_solid']), 1)
    json.dump(rep, open(os.path.join(args.out, 'report.json'), 'w'), ensure_ascii=False, indent=1)
    L = ['# QC 보고 — ' + ', '.join(os.path.basename(f) for f in args.files), '',
         '| 파트 | 삼각형 | 닫힘 | 조각 | 크기 (mm) | 부피 cm³ / PLA g(통짜) | 바닥 접지 / 첫 층 mm² | 얇은 살 mm² | 오버행(한쪽) mm² | 브리지 mm² (최대 폭) | 판정 |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for p in rep['parts']:
        L.append(f"| {p['name']} | {p['faces']:,} | {'O' if p['watertight'] and p['is_volume'] else 'X'} | {p['bodies']} | {p['size_mm'][0]}×{p['size_mm'][1]}×{p['size_mm'][2]} | {p['volume_cm3']} / {p['weight_g_solid']} | {p['bed_contact_mm2']} / {p['first_layer_mm2']} | {p['thin_area_mm2']} | {p['overhang_mm2']} | {p['bridge_mm2']} ({p['bridge_max_span']}) | {'⚠ ' + '; '.join(p['flags']) if p['flags'] else '✓'}{(' (' + p['note'] + ')') if p.get('note') else ''} |")
    L += ['', f"합계: 삼각형 {rep['total_faces']:,}, PLA 통짜 무게 {rep['total_weight_g_solid']} g (실제는 인필 비율에 따라 30~50 %)", '', '## 파트 간 충돌·간격', '']
    if rep['collisions']:
        L += ['| A | B | 교집합 mm³ | 최소 간격 mm | 판정 |', '|---|---|---|---|---|']
        for c in rep['collisions']:
            g = c['min_gap_mm']
            v = '⚠ 충돌' if c['intersection_mm3'] > 0.01 else ('접촉(얹힘·면접촉)' if g is not None and abs(g) < 0.02 else ('⚠ 간격 <0.2' if g is not None and g < 0.2 else '✓'))
            L.append(f"| {c['a']} | {c['b']} | {c['intersection_mm3']} | {c['min_gap_mm']} | {v} |")
    else: L.append('(겹치는 범위의 파트 쌍 없음)')
    L += ['', '## 오버행(한쪽 지지) 상위 위치 (z, mm², x/y 범위)', '']
    for p in rep['parts']:
        if p['overhang_top']: L.append(f"- {p['name']}: " + '; '.join(f"z={z} {a} mm² {b}" for z, a, b in p['overhang_top']))
    L += ['', '## 브리지(양쪽 지지) 상위 위치 (z, mm², 폭)', '']
    for p in rep['parts']:
        if p.get('bridge_top'): L.append(f"- {p['name']}: " + '; '.join(f"z={z} {a} mm² 폭 {s}" for z, a, s in p['bridge_top']))
    if not args.no_render:
        render(parts, args.out); L += ['', '## 렌더링', '', '![iso](render_iso.png) ![top](render_top.png)', '', '![side](render_side.png) ![bottom](render_bottom.png)']
    open(os.path.join(args.out, 'report.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L[:len(rep['parts']) + 4]))
    print('written', args.out)
if __name__ == '__main__': main()
