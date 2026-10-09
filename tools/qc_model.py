#!/usr/bin/env python3
"""3D 출력 모델 품질검사 + 렌더링 — 보내기 전 항상 돌린다 (SKILL 3절).
사용: python tools/qc_model.py <file.3mf | a.stl b.stl ...> --out <dir> [--nozzle 0.4] [--layer 0.2] [--min-wall 1.2] [--max-tri 200000]
결과: <dir>/report.md, report.json, render_iso/top/side/bottom.png, assembly.png
검사: 닫힘(watertight/is_volume/조각 수), 삼각형 예산, 크기·부피·PLA 무게, 바닥 접지 면적·비율, 얇은 살(<min-wall), 작은 부품,
      오버행 규칙(0.2 층당 0.115), 파트 간 충돌(교집합 부피)·최소 간격.
"""
import os, sys, json, argparse, numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from load3mf import load_parts
from overhang import check as overhang_check, layer_poly
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
        thin = p.difference(p.buffer(-r).buffer(r + 0.01)); a = thin.area
        if a > worst[0]: worst = (a, round(z, 2), tuple(round(v, 1) for v in thin.bounds))
    return worst

def qc_part(name, m, args):
    r = {'name': name, 'faces': int(len(m.faces)), 'vertices': int(len(m.vertices))}
    r['watertight'] = bool(m.is_watertight); r['is_volume'] = bool(m.is_volume)
    r['bodies'] = int(len(m.split(only_watertight=False)))
    b = m.bounds; r['size_mm'] = [round(float(v), 2) for v in (b[1] - b[0])]; r['min_z'] = round(float(b[0, 2]), 3)
    vol = float(abs(m.volume)) if m.is_volume else float('nan'); r['volume_cm3'] = round(vol / 1000, 2); r['weight_g_solid'] = round(vol * PLA_DENSITY, 1)
    sel = (m.face_normals[:, 2] < -0.99) & (m.triangles_center[:, 2] < b[0, 2] + 0.05)
    r['bed_contact_mm2'] = round(float(m.area_faces[sel].sum()), 1)
    foot = layer_poly(m, b[0, 2] + args.layer / 2 + 0.0137); r['first_layer_mm2'] = round(foot.area, 1)
    hull = m.convex_hull; hb = hull.bounds; r['footprint_hull_mm2'] = round(float(layer_poly(hull, b[0, 2] + 0.05).area), 1) if hull.is_volume else None
    h = r['size_mm'][2]; w = min(r['size_mm'][0], r['size_mm'][1]); r['aspect_h_over_w'] = round(h / w, 2) if w else None
    zs = np.linspace(b[0, 2] + 0.3, b[1, 2] - 0.3, 12) if h > 1 else [b[0, 2] + h / 2]
    ta, tz, tb = thin_regions(m, args.min_wall, zs); r['thin_area_mm2'] = round(ta, 1); r['thin_at_z'] = tz; r['thin_bounds'] = tb
    tot, bad = overhang_check(m, args.layer, 0.115); r['overhang_mm2'] = round(tot, 1); r['overhang_top'] = bad[:4]
    flags = []
    if not r['watertight'] or not r['is_volume']: flags.append('열린 메시(watertight 아님) — 출력 금지')
    if r['bodies'] > 1: flags.append(f'조각 {r["bodies"]}개로 분리됨')
    if r['faces'] > args.max_tri: flags.append(f'삼각형 {r["faces"]:,} > 예산 {args.max_tri:,} — 단순화 필요')
    if max(r['size_mm']) < 5 or (vol == vol and vol < 50): flags.append('너무 작은 부품(최대 치수 <5 mm 또는 부피 <50 mm³)')
    if r['bed_contact_mm2'] < 0.3 * r['first_layer_mm2']: flags.append(f'안착 불량: 바닥 접지 {r["bed_contact_mm2"]} mm² < 첫 층 {r["first_layer_mm2"]} mm² 의 30 %')
    if r['bed_contact_mm2'] < 100: flags.append(f'바닥 접지 {r["bed_contact_mm2"]} mm² < 100 mm² — 브림 필수')
    if r['aspect_h_over_w'] and r['aspect_h_over_w'] > 3: flags.append(f'가늘고 높음(높이/폭 {r["aspect_h_over_w"]}) — 넘어질 위험, 브림')
    if ta > 2.0: flags.append(f'{args.min_wall} mm 보다 얇은 살 {ta:.1f} mm² (z={tz}, x/y {tb})')
    if tot > 50: flags.append(f'오버행 규칙 위반 {tot:.0f} mm² (서포트 또는 재설계)')
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
    args = ap.parse_args(); os.makedirs(args.out, exist_ok=True)
    parts = load(args.files); rep = {'files': args.files, 'parts': [qc_part(n, m, args) for n, m in parts.items()], 'collisions': collisions(parts)}
    rep['total_faces'] = sum(p['faces'] for p in rep['parts']); rep['total_weight_g_solid'] = round(sum(p['weight_g_solid'] for p in rep['parts'] if p['weight_g_solid'] == p['weight_g_solid']), 1)
    json.dump(rep, open(os.path.join(args.out, 'report.json'), 'w'), ensure_ascii=False, indent=1)
    L = ['# QC 보고 — ' + ', '.join(os.path.basename(f) for f in args.files), '',
         '| 파트 | 삼각형 | 닫힘 | 조각 | 크기 (mm) | 부피 cm³ / PLA g(통짜) | 바닥 접지 / 첫 층 mm² | 얇은 살 mm² | 오버행 mm² | 판정 |', '|---|---|---|---|---|---|---|---|---|---|']
    for p in rep['parts']:
        L.append(f"| {p['name']} | {p['faces']:,} | {'O' if p['watertight'] and p['is_volume'] else 'X'} | {p['bodies']} | {p['size_mm'][0]}×{p['size_mm'][1]}×{p['size_mm'][2]} | {p['volume_cm3']} / {p['weight_g_solid']} | {p['bed_contact_mm2']} / {p['first_layer_mm2']} | {p['thin_area_mm2']} | {p['overhang_mm2']} | {'⚠ ' + '; '.join(p['flags']) if p['flags'] else '✓'} |")
    L += ['', f"합계: 삼각형 {rep['total_faces']:,}, PLA 통짜 무게 {rep['total_weight_g_solid']} g (실제는 인필 비율에 따라 30~50 %)", '', '## 파트 간 충돌·간격', '']
    if rep['collisions']:
        L += ['| A | B | 교집합 mm³ | 최소 간격 mm | 판정 |', '|---|---|---|---|---|']
        for c in rep['collisions']:
            v = '⚠ 충돌' if c['intersection_mm3'] > 0.01 else ('⚠ 간격 <0.2' if c['min_gap_mm'] is not None and c['min_gap_mm'] < 0.2 else '✓')
            L.append(f"| {c['a']} | {c['b']} | {c['intersection_mm3']} | {c['min_gap_mm']} | {v} |")
    else: L.append('(겹치는 범위의 파트 쌍 없음)')
    L += ['', '## 오버행 상위 위치 (z, mm², x/y 범위)', '']
    for p in rep['parts']:
        if p['overhang_top']: L.append(f"- {p['name']}: " + '; '.join(f"z={z} {a} mm² {b}" for z, a, b in p['overhang_top']))
    if not args.no_render:
        render(parts, args.out); L += ['', '## 렌더링', '', '![iso](render_iso.png) ![top](render_top.png)', '', '![side](render_side.png) ![bottom](render_bottom.png)']
    open(os.path.join(args.out, 'report.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L[:len(rep['parts']) + 4]))
    print('written', args.out)
if __name__ == '__main__': main()
