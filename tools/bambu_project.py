#!/usr/bin/env python3
"""Bambu Studio 프로젝트 3MF 작성기 — 사용자가 Bambu Studio 에서 내보낸 3MF 를 '틀'로 삼아 설정(project_settings)·메타데이터를 그대로 두고
오브젝트/파트/플레이트만 바꿔 넣는다. 손으로 지어낸 설정으로는 열리지 않았다(Toolbox42 v4) → 설정은 항상 sample/ 의 실제 내보내기에서.
  python tools/bambu_project.py <플레이트.3mf> --out X_bambu.3mf [--template sample/nameplate_50x30x7_EtoA.3mf] [--colors '#30949D,#F2AF38'] [--set enable_support=1 ...]
  read_plate(path) → [{'name', 'parts': [(trimesh 베드좌표, 파트이름, 필라멘트번호)]}]
  write_bambu_project(out, objects, template, ...) / verify_bambu_project(path, template) → dict
구조(틀 02.08.02.61 실측): 3D/3dmodel.model(루트 오브젝트 = 하위 모델 컴포넌트, build item = 베드 위치) · 3D/Objects/object_N.model(파트 메시, 파트 중심 기준 좌표)
 · Metadata/model_settings.config(파트 이름·행렬·extruder, plate, assemble) · project_settings.config(틀 그대로) · plate_1.json · 썸네일 · cut_information · filament_sequence · slice_info."""
import os, sys, io, json, re, uuid, zipfile, datetime, argparse, numpy as np, trimesh
import xml.etree.ElementTree as ET
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from load3mf import _mesh, M as _M, NS, PPATH
DEFAULT_TEMPLATE = os.path.join(os.path.dirname(HERE), 'sample', 'nameplate_50x30x7_EtoA.3mf')
def read_plate(path):
    """우리 플레이트 3MF(generic3mf 형식이든 Bambu 형식이든) → 오브젝트 목록(베드 좌표 메시, 이름, extruder)"""
    z = zipfile.ZipFile(path); r = ET.fromstring(z.read('3D/3dmodel.model'))
    objs = {o.get('id'): o for o in r.find('m:resources', NS).findall('m:object', NS)}
    meta = {}
    if 'Metadata/model_settings.config' in z.namelist():
        ms = ET.fromstring(z.read('Metadata/model_settings.config'))
        for ob in ms.findall('object'):
            om = {m.get('key'): m.get('value') for m in ob.findall('metadata') if m.get('key')}
            parts = {pt.get('id'): {m.get('key'): m.get('value') for m in pt.findall('metadata') if m.get('key')} for pt in ob.findall('part')}
            meta[ob.get('id')] = (om, parts)
    sub = {}
    def subobjs(p):
        if p not in sub: rr = ET.fromstring(z.read(p.lstrip('/'))); sub[p] = {o.get('id'): o for o in rr.find('m:resources', NS).findall('m:object', NS)}
        return sub[p]
    out = []
    for it in r.find('m:build', NS):
        T = _M(it.get('transform')); oid = it.get('objectid'); top = objs[oid]; om, pm = meta.get(oid, ({}, {}))
        ob = {'name': om.get('name', top.get('name') or f'object{oid}'), 'parts': []}
        comps = top.find('m:components', NS)
        if comps is None:
            m = _mesh(top); m.apply_transform(T); ob['parts'].append((m, ob['name'], int(om.get('extruder', 1)))); out.append(ob); continue
        for c in comps:
            pp = c.get(PPATH); o = (subobjs(pp) if pp else objs)[c.get('objectid')]
            m = _mesh(o); m.apply_transform(_M(c.get('transform'))); m.apply_transform(T)
            md = pm.get(c.get('objectid'), {}); ob['parts'].append((m, md.get('name', o.get('name') or f'part{c.get("objectid")}'), int(md.get('extruder', om.get('extruder', 1)))))
        out.append(ob)
    return out
def _f(v): return f'{v:.7g}'
def _object_model(parts_local, ids, uuids):
    L = ['<?xml version="1.0" encoding="UTF-8"?>', '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">',
         ' <metadata name="BambuStudio:3mfVersion">1</metadata>', ' <resources>']
    for m, pid, u in zip(parts_local, ids, uuids):
        L.append(f'  <object id="{pid}" p:UUID="{u}" type="model">'); L.append('   <mesh>'); L.append('    <vertices>')
        L += [f'     <vertex x="{_f(a)}" y="{_f(b)}" z="{_f(c)}"/>' for a, b, c in np.asarray(m.vertices)]
        L.append('    </vertices>'); L.append('    <triangles>')
        L += [f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in np.asarray(m.faces)]
        L.append('    </triangles>'); L.append('   </mesh>'); L.append('  </object>')
    L += [' </resources>', ' <build/>', '</model>']; return '\n'.join(L)
def _thumb(objects, colors, size, top=True):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(size / 100, size / 100), dpi=100); ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor('#1a1d21'); fig.patch.set_facecolor('#1a1d21')
    for ob in objects:
        for m, _, e in sorted(ob['parts'], key=lambda p: p[0].bounds[1, 2]):
            T = m.triangles; up = m.face_normals[:, 2] > 0.2
            ax.add_collection(matplotlib.collections.PolyCollection(T[up][:, :, :2], facecolors=colors[(e - 1) % len(colors)], edgecolors='none'))
    allb = np.array([m.bounds for ob in objects for m, _, _ in ob['parts']]); lo, hi = allb[:, 0].min(0), allb[:, 1].max(0); c = (lo + hi) / 2; s = (hi - lo)[:2].max() / 2 * 1.08
    ax.set_xlim(c[0] - s, c[0] + s); ax.set_ylim(c[1] - s, c[1] + s); ax.set_aspect('equal'); ax.axis('off')
    buf = io.BytesIO(); fig.savefig(buf, format='png', facecolor=fig.get_facecolor()); plt.close(fig); return buf.getvalue()
def write_bambu_project(out, objects, template=DEFAULT_TEMPLATE, plate_name='', filament_colours=None, settings=None, title='', print_sequence='by layer'):
    tz = zipfile.ZipFile(template); tn = set(tz.namelist())
    ps = json.loads(tz.read('Metadata/project_settings.config')); nfil = len(ps['filament_colour'])
    used = sorted({e for ob in objects for _, _, e in ob['parts']}); assert max(used) <= nfil, f'필라멘트 {max(used)}번 > 틀의 필라멘트 수 {nfil}'
    if filament_colours:
        for i, c in enumerate(filament_colours[:nfil]): ps['filament_colour'][i] = c.upper()
    for k, v in (settings or {}).items():
        assert k in ps, f'틀 project_settings 에 없는 키 {k} — 지어낸 설정 금지'
        assert type(v) is type(ps[k]) and (not isinstance(v, list) or len(v) == len(ps[k])), f'{k}: 형식이 틀과 다름 ({type(ps[k]).__name__}, 길이 {len(ps[k]) if isinstance(ps[k], list) else "-"})'
        ps[k] = v
    hdr = ET.fromstring(tz.read('3D/3dmodel.model')); today = datetime.date.today().isoformat()
    meta_xml = []
    for md in hdr.findall('m:metadata', NS):
        n = md.get('name'); v = md.text or ''
        if n in ('CreationDate', 'ModificationDate'): v = today
        if n == 'Title': v = title
        meta_xml.append(f' <metadata name="{n}">{v}</metadata>')
    files = {}; res = []; build = []; ms_obj = []; assemble = []; cut = []; rels = []; plate_inst = []; bbox_objs = []; counter = 0
    base_name = os.path.basename(out)
    for i, ob in enumerate(objects, start=1):
        allb = np.array([m.bounds for m, _, _ in ob['parts']]); lo, hi = allb[:, 0].min(0), allb[:, 1].max(0)
        O = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
        ids = list(range(counter + 1, counter + 1 + len(ob['parts']))); root = counter + len(ob['parts']) + 1; counter = root
        locs, centers, uu = [], [], []
        for k, (m, _, _) in enumerate(ob['parts']):
            c = (m.bounds[0] + m.bounds[1]) / 2; mm = m.copy(); mm.apply_translation(-c); locs.append(mm); centers.append(c - O); uu.append(f'{i:04x}{k:04x}-81cb-4c03-9d28-80fed5dfa1dc')
        path = f'3D/Objects/object_{i}.model'; files[path] = _object_model(locs, ids, uu); rels.append(f' <Relationship Target="/{path}" Id="rel-{i}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
        comps = [f'    <component p:path="/{path}" objectid="{pid}" p:UUID="{i:04x}{k:04x}-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 {_f(t[0])} {_f(t[1])} {_f(t[2])}"/>' for k, (pid, t) in enumerate(zip(ids, centers))]
        res.append(f'  <object id="{root}" p:UUID="{i:08x}-61cb-4c03-9d28-80fed5dfa1dc" type="model">\n   <components>\n' + '\n'.join(comps) + '\n   </components>\n  </object>')
        build.append(f'  <item objectid="{root}" p:UUID="{root:08x}-b1ec-4553-aec9-835e5b724bb4" transform="1 0 0 0 1 0 0 0 1 {_f(O[0])} {_f(O[1])} {_f(O[2])}" printable="1"/>')
        fc = sum(len(m.faces) for m, _, _ in ob['parts'])
        P = [f'  <object id="{root}">', f'    <metadata key="name" value="{ob["name"]}"/>', f'    <metadata key="extruder" value="{ob["parts"][0][2]}"/>']
        for k2, v2 in (ob.get('object_settings') or {}).items(): P.append(f'    <metadata key="{k2}" value="{v2}"/>')
        P.append(f'    <metadata face_count="{fc}"/>')
        for k, ((m, pn, e), pid, t) in enumerate(zip(ob['parts'], ids, centers)):
            P += [f'    <part id="{pid}" subtype="normal_part" uuid="{uuid.uuid5(uuid.NAMESPACE_URL, base_name + str(i) + "/" + str(k))}">', f'      <metadata key="name" value="{pn}"/>',
                  f'      <metadata key="matrix" value="1 0 0 {_f(t[0])} 0 1 0 {_f(t[1])} 0 0 1 {_f(t[2])} 0 0 0 1"/>', f'      <metadata key="source_file" value="{base_name}"/>',
                  f'      <metadata key="source_object_id" value="{i - 1}"/>', f'      <metadata key="source_volume_id" value="{k}"/>',
                  f'      <metadata key="source_offset_x" value="{_f(t[0])}"/>', f'      <metadata key="source_offset_y" value="{_f(t[1])}"/>', f'      <metadata key="source_offset_z" value="{_f(t[2])}"/>',
                  f'      <metadata key="extruder" value="{e}"/>',
                  f'      <mesh_stat face_count="{len(m.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>', '    </part>']
            assemble.append(f'   <assemble_item object_id="{root}" volume_id="{k}" transform="1 0 0 0 1 0 0 0 1 {_f(t[0])} {_f(t[1])} {_f(t[2])}" />')
        P.append('  </object>'); ms_obj.append('\n'.join(P))
        assemble.insert(len(assemble) - len(ob['parts']), f'   <assemble_item object_id="{root}" instance_id="0" transform="1 0 0 0 1 0 0 0 1 {_f(O[0])} {_f(O[1])} {_f(O[2])}" offset="0 0 0" />')
        ident = 100 + 37 * i; plate_inst.append(f'    <model_instance>\n      <metadata key="object_id" value="{root}"/>\n      <metadata key="instance_id" value="0"/>\n      <metadata key="identify_id" value="{ident}"/>\n    </model_instance>')
        from overhang import layer_poly
        from shapely.ops import unary_union
        area = unary_union([layer_poly(m, m.bounds[0, 2] + 0.1) for m, _, _ in ob['parts']]).area
        bbox_objs.append({'area': float(area), 'bbox': [float(lo[0]), float(lo[1]), float(hi[0]), float(hi[1])], 'id': ident, 'layer_height': 0.2, 'name': ob['name']})
        cut.append(f' <object id="{i}">\n  <cut_id id="0" check_sum="1" connectors_cnt="0"/>\n </object>')
    root_xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">'] + meta_xml
    root_xml += [' <resources>'] + res + [' </resources>', f' <build p:UUID="{uuid.uuid5(uuid.NAMESPACE_URL, base_name)}">'] + build + [' </build>', '</model>']
    files['3D/3dmodel.model'] = '\n'.join(root_xml)
    files['3D/_rels/3dmodel.model.rels'] = '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n' + '\n'.join(rels) + '\n</Relationships>'
    tms = ET.fromstring(tz.read('Metadata/model_settings.config')); tpl = tms.find('plate'); pmeta = []
    for md in tpl.findall('metadata'):
        k, v = md.get('key'), md.get('value')
        if k == 'plater_name': v = plate_name
        if k == 'print_sequence': v = print_sequence
        pmeta.append(f'    <metadata key="{k}" value="{v}"/>')
    files['Metadata/model_settings.config'] = '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + '\n'.join(ms_obj) + '\n  <plate>\n' + '\n'.join(pmeta) + '\n' + '\n'.join(plate_inst) + '\n  </plate>\n  <assemble>\n' + '\n'.join(assemble) + '\n  </assemble>\n</config>\n'
    files['Metadata/project_settings.config'] = json.dumps(ps, indent=4, ensure_ascii=False)
    pj = json.loads(tz.read('Metadata/plate_1.json')); allb = np.array([b['bbox'] for b in bbox_objs])
    pj.update({'bbox_all': [float(allb[:, 0].min()), float(allb[:, 1].min()), float(allb[:, 2].max()), float(allb[:, 3].max())], 'bbox_objects': bbox_objs, 'is_seq_print': print_sequence == 'by object', 'first_layer_time': 0.0})
    files['Metadata/plate_1.json'] = json.dumps(pj, ensure_ascii=False)
    files['Metadata/cut_information.xml'] = '<?xml version="1.0" encoding="utf-8"?>\n<objects>\n' + '\n'.join(cut) + '\n</objects>\n'
    cols = [c for c in ps['filament_colour']]
    big = _thumb(objects, cols, 512); files['Metadata/plate_1.png'] = big; files['Metadata/plate_no_light_1.png'] = big; files['Metadata/top_1.png'] = big; files['Metadata/pick_1.png'] = big
    files['Metadata/plate_1_small.png'] = _thumb(objects, cols, 128)
    for keep in ['[Content_Types].xml', '_rels/.rels', 'Metadata/slice_info.config', 'Metadata/filament_sequence.json']:
        if keep in tn: files[keep] = tz.read(keep)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zo:
        for n in ['[Content_Types].xml', '_rels/.rels', '3D/3dmodel.model', '3D/_rels/3dmodel.model.rels'] + sorted(k for k in files if k.startswith('3D/Objects')) + sorted(k for k in files if k.startswith('Metadata')):
            d = files[n]; zo.writestr(n, d if isinstance(d, bytes) else d.encode('utf-8'))
    return out
def verify_bambu_project(path, template=DEFAULT_TEMPLATE, objects=None):
    """구조 검증(Bambu Studio 없이 할 수 있는 만큼): 틀과 같은 파일 종류·설정 키 집합·Application, XML 파싱, id·파트 수 일치, 메시 왕복(부피)·닫힘."""
    z = zipfile.ZipFile(path); tz = zipfile.ZipFile(template); r = {'path': path}; errs = []
    kinds = lambda names: sorted({re.sub(r'\d+', 'N', n) for n in names})
    if kinds(z.namelist()) != kinds(tz.namelist()): errs.append(f'파일 종류 다름: {set(kinds(z.namelist())) ^ set(kinds(tz.namelist()))}')
    for n in z.namelist():
        if n.endswith(('.model', '.config', '.xml', '.rels')) and not n.endswith('project_settings.config'):
            try: ET.fromstring(z.read(n))
            except Exception as e: errs.append(f'XML 오류 {n}: {e}')
    ps, tps = json.loads(z.read('Metadata/project_settings.config')), json.loads(tz.read('Metadata/project_settings.config'))
    if set(ps) != set(tps): errs.append(f'project_settings 키 다름: {set(ps) ^ set(tps)}')
    diff = {k: (tps[k], ps[k]) for k in tps if ps.get(k) != tps[k]}; r['settings_changed'] = {k: v[1] for k, v in diff.items()}
    app = re.search(r'name="Application">([^<]*)', z.read('3D/3dmodel.model').decode()); r['application'] = app.group(1) if app else None
    if r['application'] != re.search(r'name="Application">([^<]*)', tz.read('3D/3dmodel.model').decode()).group(1): errs.append('Application 태그가 틀과 다름')
    root = ET.fromstring(z.read('3D/3dmodel.model')); ncomp = sum(len(o.find('m:components', NS)) for o in root.find('m:resources', NS).findall('m:object', NS) if o.find('m:components', NS) is not None)
    ms = ET.fromstring(z.read('Metadata/model_settings.config')); nparts = sum(len(o.findall('part')) for o in ms.findall('object'))
    if ncomp != nparts: errs.append(f'컴포넌트 {ncomp} ≠ model_settings 파트 {nparts}')
    back = read_plate(path); r['objects'] = [{'name': ob['name'], 'parts': [(pn, e, round(float(abs(m.volume)), 2), bool(m.is_volume)) for m, pn, e in ob['parts']]} for ob in back]
    if objects is not None:
        for a, b in zip(objects, back):
            for (m1, n1, e1), (m2, n2, e2) in zip(a['parts'], b['parts']):
                if n1 != n2 or e1 != e2 or abs(abs(m1.volume) - abs(m2.volume)) > 1e-3 * max(1, abs(m1.volume)) or np.abs(m1.bounds - m2.bounds).max() > 1e-3:
                    errs.append(f'왕복 불일치 {n1}: 부피 {m1.volume:.3f}→{m2.volume:.3f}, extruder {e1}→{e2}')
    r['errors'] = errs; r['ok'] = not errs; return r
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('plate'); ap.add_argument('--out', required=True); ap.add_argument('--template', default=DEFAULT_TEMPLATE)
    ap.add_argument('--colors', default=''); ap.add_argument('--plate_name', default=''); ap.add_argument('--title', default=''); ap.add_argument('--set', nargs='*', default=[])
    a = ap.parse_args(); obs = read_plate(a.plate)
    settings = {}
    for kv in a.set:
        k, v = kv.split('=', 1); settings[k] = json.loads(v) if v[:1] in '[{"' else v
    write_bambu_project(a.out, obs, a.template, a.plate_name, [c for c in a.colors.split(',') if c], settings, a.title)
    print(json.dumps(verify_bambu_project(a.out, a.template, obs), ensure_ascii=False, indent=1, default=str))
