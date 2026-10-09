#!/usr/bin/env python3
"""열쇠고리 프로젝트(3d-print/mm3mf.py)에서 Bambu Studio로 실제 출력에 성공한 방식 그대로의 일반 3MF 작성기.

mm3mf.py 와 같은 세 경로를 모두 넣는다:
  1) basematerials(displaycolor)        → 어떤 뷰어/슬라이서에서든 색이 보인다
  2) Metadata/model_settings.config     → Bambu Studio / OrcaSlicer 가 파트별 extruder 로 필라멘트를 자동 지정
  3) Metadata/Slic3r_PE_model.config    → PrusaSlicer 가 volume 별 extruder 로 지정
차이점: 오브젝트를 여러 개(본체·손잡이·걸쇠 …) 둘 수 있고, build item transform 으로 베드 위치를 정한다.
Application 태그를 넣지 않는다 → Bambu Studio 는 "형상만 불러옴" 알림을 띄우지만 파트 이름·extruder 는 그대로 읽는다
(bbs_3mf.cpp: model_settings.config 파싱은 dont_load_config 와 무관).
"""
import zipfile
import numpy as np

_CT = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
       '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
       '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
_RELS = ('<?xml version="1.0" encoding="UTF-8"?>\n'
         '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
         '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
_IDENT = '1 0 0 0 1 0 0 0 1 0 0 0'
_IDENT16 = '1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'

def _hex(c):
    c = (c or '#808080').lstrip('#')
    if len(c) == 3: c = ''.join(ch * 2 for ch in c)
    if len(c) == 6: c += 'FF'
    return '#' + c.upper()[:8]

def _xml(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def write_generic_3mf(path, objects, title='model'):
    """objects: [{'name': str, 'parts': [(trimesh, color_hex, part_name), ...]}, ...]
    메시는 베드(월드) 좌표 그대로 (0..256, z>=0). 같은 색은 같은 필라멘트(익스트루더) 번호."""
    mat_order, mat_index = [], {}
    for ob in objects:
        for _, col, _ in ob['parts']:
            k = _hex(col)
            if k not in mat_index: mat_index[k] = len(mat_order); mat_order.append(k)
    res, builds, ms, pe = [], [], [], []
    next_id = 2
    for ob in objects:
        parts = []
        for mesh, col, pname in ob['parts']:
            oid = next_id; next_id += 1; mi = mat_index[_hex(col)]
            v = np.asarray(mesh.vertices, float); f = np.asarray(mesh.faces, np.int64)
            vx = ''.join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in v)
            tx = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}" pid="1" p1="{mi}"/>' for a, b, c in f)
            res.append(f'<object id="{oid}" name="{_xml(pname)}" type="model" pid="1" pindex="{mi}"><mesh><vertices>{vx}</vertices><triangles>{tx}</triangles></mesh></object>')
            parts.append((oid, mi, pname, len(f)))
        aid = next_id; next_id += 1
        res.append(f'<object id="{aid}" name="{_xml(ob["name"])}" type="model"><components>'
                   + ''.join(f'<component objectid="{oid}" transform="{_IDENT}"/>' for oid, *_ in parts) + '</components></object>')
        builds.append(f'<item objectid="{aid}" transform="{_IDENT}"/>')
        ms.append(f'  <object id="{aid}">\n    <metadata key="name" value="{_xml(ob["name"])}"/>\n')
        for oid, mi, pname, _ in parts:
            ms.append(f'    <part id="{oid}" subtype="normal_part">\n      <metadata key="name" value="{_xml(pname)}"/>\n'
                      f'      <metadata key="matrix" value="{_IDENT16}"/>\n      <metadata key="extruder" value="{mi + 1}"/>\n    </part>\n')
        ms.append('  </object>\n')
        pe.append(f'  <object id="{aid}" instances_count="1">\n    <metadata type="object" key="name" value="{_xml(ob["name"])}"/>\n')
        cur = 0
        for oid, mi, pname, n in parts:
            pe.append(f'    <volume firstid="{cur}" lastid="{cur + n - 1}">\n      <metadata type="volume" key="name" value="{_xml(pname)}"/>\n'
                      '      <metadata type="volume" key="volume_type" value="ModelPart"/>\n'
                      f'      <metadata type="volume" key="matrix" value="{_IDENT16}"/>\n'
                      f'      <metadata type="volume" key="extruder" value="{mi + 1}"/>\n    </volume>\n'); cur += n
        pe.append('  </object>\n')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02">'
             f'<metadata name="Title">{_xml(title)}</metadata><resources><basematerials id="1">'
             + ''.join(f'<base name="Filament {i + 1}" displaycolor="{dc}"/>' for i, dc in enumerate(mat_order))
             + '</basematerials>' + ''.join(res) + '</resources><build>' + ''.join(builds) + '</build></model>')
    with zipfile.ZipFile(str(path), 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', _CT); z.writestr('_rels/.rels', _RELS)
        z.writestr('3D/3dmodel.model', model)
        z.writestr('Metadata/model_settings.config', '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + ''.join(ms) + '</config>\n')
        z.writestr('Metadata/Slic3r_PE_model.config', '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + ''.join(pe) + '</config>\n')
    return str(path)
