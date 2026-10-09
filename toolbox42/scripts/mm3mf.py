#!/usr/bin/env python3
"""색상별로 필라멘트(익스트루더)가 자동 지정되는 멀티컬러 3MF 작성기.

trimesh 기본 3MF 내보내기는 색/재질을 전혀 넣지 않아, 슬라이서에서 모든
객체가 같은 필라멘트로 들어온다. 이 모듈은 하나의 오브젝트 안에 색깔별
'볼륨'을 두고:
  1) 3MF 표준 재질(basematerials)로 각 색을 넣어 어떤 슬라이서에서든 색이 보이고,
  2) 각 삼각형에 재질 인덱스를 달아(per-triangle) 색이 실제로 칠해지며,
  3) PrusaSlicer/OrcaSlicer 용 Metadata/Slic3r_PE_model.config 에 볼륨별
     extruder 를 적어, 불러오자마자 색깔별로 다른 필라멘트가 자동 지정된다.
같은 색을 쓰는 파트는 같은 필라멘트로 묶인다(색 교체 최소화).
"""

import zipfile
from pathlib import Path

import numpy as np

_CT = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
    "</Types>"
)
_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
    "</Relationships>"
)


def _hex(color: str) -> str:
    """'#rrggbb' / 'rrggbb' → '#RRGGBBFF' (3MF displaycolor, 알파 포함)."""
    c = (color or "#808080").lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) == 6:
        c += "FF"
    return "#" + c.upper()[:8]


_IDENT = "1 0 0 0 1 0 0 0 1 0 0 0"   # 3MF component/build transform(4x3 항등)


def write_multicolor_3mf(path, groups, object_name="model"):
    """groups: [(mesh, color_hex, name), ...] → 멀티컬러 3MF.
    같은 color_hex 는 같은 필라멘트(익스트루더)로 묶인다.

    슬라이서 호환(핵심): 색 파트를 '별도 object + components'로 저장하고
      1) basematerials(displaycolor)  → 어떤 3MF 뷰어에서든 색이 보이고,
      2) Metadata/model_settings.config → Bambu Studio/OrcaSlicer 가 파트별
         extruder 로 필라멘트를 자동 지정(이 둘이 표준 Slic3r_PE config 를 무시하므로
         이게 없으면 색이 안 잡혔던 것),
      3) Metadata/Slic3r_PE_model.config → PrusaSlicer 가 volume 별 extruder 로 지정.
    세 경로를 모두 넣어 슬라이서에 상관없이 색이 자동 지정된다.

    mesh 는 trimesh.Trimesh (vertices, faces). 빈/None 그룹은 건너뛴다."""
    groups = [(m, c, n) for (m, c, n) in groups
              if m is not None and len(getattr(m, "faces", [])) > 0]
    if not groups:
        raise ValueError("멀티컬러 3MF: 내보낼 메시가 없습니다.")

    # 색(대소문자 무시) → 재질/익스트루더 인덱스. 첫 등장 순서 유지(밑판색이 보통 1번).
    mat_order = []       # displaycolor 문자열 목록
    mat_index = {}       # normalized hex → index
    for _, col, _ in groups:
        key = _hex(col)
        if key not in mat_index:
            mat_index[key] = len(mat_order)
            mat_order.append(key)

    ASSEMBLY_ID = 2
    parts = []           # (part_object_id, matidx, name, first_tri, last_tri)
    part_bodies = []     # 각 파트 <object>...</object>
    tri_cursor = 0       # 파트를 이어붙였을 때의 누적 삼각형 인덱스(PrusaSlicer용)
    for k, (mesh, col, name) in enumerate(groups):
        oid = 3 + k      # 파트 오브젝트 id (assembly=2 뒤로)
        mi = mat_index[_hex(col)]
        v = np.asarray(mesh.vertices, dtype=float)
        f = np.asarray(mesh.faces, dtype=np.int64)
        # 소수 6자리: 4자리로 적으면 불러올 때 서로 다른 정점이 병합되어
        # 메시가 깨진다(퇴화 면 발생). 파일이 조금 커지는 대신 안전하다.
        vx = "".join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in v)
        tx = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}" pid="1" p1="{mi}"/>'
                     for a, b, c in f)
        # 파트 오브젝트: 기본 재질=자기 색(pindex) → 뷰어 프리뷰 색.
        part_bodies.append(
            f'<object id="{oid}" type="model" pid="1" pindex="{mi}">'
            f'<mesh><vertices>{vx}</vertices><triangles>{tx}</triangles></mesh></object>')
        first = tri_cursor; tri_cursor += len(f)
        parts.append((oid, mi, name, first, tri_cursor - 1))

    # ---- 3D/3dmodel.model : basematerials + 파트 object들 + assembly(components) ----
    out = ['<?xml version="1.0" encoding="UTF-8"?>\n',
           '<model unit="millimeter" xml:lang="en-US" '
           'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
           'xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02">',
           "<resources>", '<basematerials id="1">']
    for i, dc in enumerate(mat_order):
        out.append(f'<base name="Filament {i + 1}" displaycolor="{dc}"/>')
    out.append("</basematerials>")
    out.extend(part_bodies)
    # assembly: 파트들을 components 로 묶는다(색별 파트 유지 = Bambu/Orca 네이티브 구조).
    out.append(f'<object id="{ASSEMBLY_ID}" type="model"><components>')
    for oid, *_ in parts:
        out.append(f'<component objectid="{oid}" transform="{_IDENT}"/>')
    out.append("</components></object></resources>")
    out.append(f'<build><item objectid="{ASSEMBLY_ID}" transform="{_IDENT}"/></build></model>')
    model_xml = "".join(out)

    # ---- Metadata/model_settings.config (Bambu Studio / OrcaSlicer) ----
    ms = ['<?xml version="1.0" encoding="UTF-8"?>\n<config>\n',
          f'  <object id="{ASSEMBLY_ID}">\n',
          f'    <metadata key="name" value="{_xml(object_name)}"/>\n']
    for oid, mi, name, _, _ in parts:
        ms.append(f'    <part id="{oid}" subtype="normal_part">\n')
        ms.append(f'      <metadata key="name" value="{_xml(name)}"/>\n')
        ms.append(f'      <metadata key="matrix" value="{_IDENT}"/>\n')
        ms.append(f'      <metadata key="extruder" value="{mi + 1}"/>\n')
        ms.append("    </part>\n")
    ms.append("  </object>\n</config>\n")
    model_settings_xml = "".join(ms)

    # ---- Metadata/Slic3r_PE_model.config (PrusaSlicer) ----
    # PrusaSlicer는 components를 하나의 오브젝트로 flatten 후 volume(firstid/lastid,
    # 파트 순서대로 이어진 삼각형 범위)별 extruder를 읽는다.
    cfg = ['<?xml version="1.0" encoding="UTF-8"?>\n<config>\n',
           f'  <object id="{ASSEMBLY_ID}" instances_count="1">\n',
           f'    <metadata type="object" key="name" value="{_xml(object_name)}"/>\n']
    for oid, mi, name, first, last in parts:
        cfg.append(f'    <volume firstid="{first}" lastid="{last}">\n')
        cfg.append(f'      <metadata type="volume" key="name" value="{_xml(name)}"/>\n')
        cfg.append('      <metadata type="volume" key="volume_type" value="ModelPart"/>\n')
        cfg.append(f'      <metadata type="volume" key="matrix" value="{_IDENT}"/>\n')
        cfg.append('      <metadata type="volume" key="source_object_id" value="0"/>\n')
        cfg.append('      <metadata type="volume" key="source_volume_id" value="0"/>\n')
        cfg.append(f'      <metadata type="volume" key="extruder" value="{mi + 1}"/>\n')
        cfg.append("    </volume>\n")
    cfg.append("  </object>\n</config>\n")
    config_xml = "".join(cfg)

    path = str(path)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CT)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("3D/3dmodel.model", model_xml)
        z.writestr("Metadata/model_settings.config", model_settings_xml)
        z.writestr("Metadata/Slic3r_PE_model.config", config_xml)
    return path


def _xml(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))
