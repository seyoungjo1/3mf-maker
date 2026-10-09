"""Bambu Studio project 3MF writer that mirrors _BBS_3MF_Exporter (SaveStrategy::SplitModel | ProductionExt).

Layout produced (same file set / tags / UUID rules as Bambu Studio's own "Save project"):
  [Content_Types].xml
  _rels/.rels                      rel-1 model, rel-2 thumbnail, rel-4/5 bambu cover thumbnails
  3D/3dmodel.model                 metadata + assembly objects (components with p:path) + build
  3D/_rels/3dmodel.model.rels      one Relationship per sub-model file
  3D/Objects/object_N.model        mesh objects only (one file per ModelObject), empty <build/>
  Metadata/model_settings.config   objects/parts (name, extruder, matrix, mesh_stat), plates, assemble
  Metadata/project_settings.config full print/filament/printer config (JSON) with "version"
  Metadata/slice_info.config       header only (unsliced project)
  Metadata/cut_information.xml     one entry per object
  Metadata/plate_N.png, plate_N_small.png  thumbnails

ID rules (from the exporter): for each object in order, its volumes get ids v, v+1, ..., then the
assembly object gets the next id.  backup_id = 1-based object index.
  object  p:UUID = hex8(backup_id) + "-61cb-4c03-9d28-80fed5dfa1dc"
  volume  p:UUID = hex8(vol_index + (backup_id<<16)) + "-81cb-4c03-9d28-80fed5dfa1dc"
  comp.   p:UUID = hex8(vol_index + (backup_id<<16)) + "-b206-40ff-9872-83e8017abed1"
  build   p:UUID = "2c7c17d8-22b5-4d84-8835-1976022ea369"
  item    p:UUID = hex8(object_id) + "-b1ec-4553-aec9-835e5b724bb4"
Vertices are written with %.9g (round-trippable float).  Mesh coordinates are object-local; the
instance placement goes into the build item transform (12 numbers, column-major 3x4).
Plate i (0-based) origin = (col*W*1.2, -row*D*1.2) with cols = round(sqrt(n)) (+1 if sqrt > round).
"""
import io, json, zipfile, datetime
import numpy as np

CORE = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
PROD = 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
BBL  = 'http://schemas.bambulab.com/package/2021'
OBJ_SUF, SUB_SUF, COMP_SUF = '-61cb-4c03-9d28-80fed5dfa1dc', '-81cb-4c03-9d28-80fed5dfa1dc', '-b206-40ff-9872-83e8017abed1'
BUILD_UUID, ITEM_SUF = '2c7c17d8-22b5-4d84-8835-1976022ea369', '-b1ec-4553-aec9-835e5b724bb4'
IDENT12 = '1 0 0 0 1 0 0 0 1 0 0 0'
IDENT16 = '1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'

def _h8(n): return f'{int(n) & 0xffffffff:08x}'
def _x(s): return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
def _g(v): return f'{float(v):.9g}'
def _t12(tx, ty, tz=0.0): return f'1 0 0 0 1 0 0 0 1 {_g(tx)} {_g(ty)} {_g(tz)}'

def _model_header():
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<model unit="millimeter" xml:lang="en-US" xmlns="{CORE}" xmlns:BambuStudio="{BBL}" '
            f'xmlns:p="{PROD}" requiredextensions="p">\n')

def _mesh_xml(mesh):
    v = np.asarray(mesh.vertices, dtype=np.float64); f = np.asarray(mesh.faces, dtype=np.int64)
    buf = io.StringIO()
    buf.write('   <mesh>\n    <vertices>\n')
    for a, b, c in v: buf.write(f'     <vertex x="{a:.9g}" y="{b:.9g}" z="{c:.9g}"/>\n')
    buf.write('    </vertices>\n    <triangles>\n')
    for a, b, c in f: buf.write(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>\n')
    buf.write('    </triangles>\n   </mesh>\n')
    return buf.getvalue()

def _png_thumbnail(meshes, size, bed=(256, 256)):
    """Simple top-view render of the plate (bed outline + part footprints)."""
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    fig = plt.figure(figsize=(size / 100, size / 100), dpi=100); ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor('#e8ebe8'); ax.set_xlim(-8, bed[0] + 8); ax.set_ylim(-8, bed[1] + 8); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(plt.Rectangle((0, 0), bed[0], bed[1], fill=False, ec='#8a948c', lw=1))
    for m, col in meshes:
        tri = np.asarray(m.triangles)[:, :, :2]
        ax.add_collection(PolyCollection(tri, facecolor=col, edgecolor='none'))
    out = io.BytesIO(); fig.savefig(out, format='png', dpi=100); plt.close(fig); return out.getvalue()

def write_bbl_project(path, plates, project_settings, app_version='02.00.00.00', plate_w=256, plate_d=256,
                      title='', filament_colours=None):
    """plates: [{'name': str, 'objects': [{'name': str, 'extruder': int,
                                            'parts': [(trimesh, part_name, extruder), ...]}]}]
    Part meshes are given in *plate-local* world coordinates (0..plate_w, 0..plate_d, z>=0)."""
    n = len(plates); r = int(round(np.sqrt(n))); cols = r + 1 if np.sqrt(n) > r else max(r, 1)
    sx, sy = plate_w * 1.2, plate_d * 1.2
    colours = filament_colours or (project_settings.get('filament_colour') or ['#30949D', '#F2AF38'])
    today = datetime.date.today().isoformat()

    sub_files = {}      # 'Objects/object_N.model' -> xml
    main_res, items, ms_objects, ms_plates, assemble, cut_xml = [], [], [], [], [], []
    next_id = 1; backup_id = 0; identify = 100
    for pi, pl in enumerate(plates):
        ox, oy = (pi % cols) * sx, -(pi // cols) * sy
        plate_insts = []; thumbs = []
        for ob in pl['objects']:
            backup_id += 1
            parts = ob['parts']
            allv = np.vstack([np.asarray(m.vertices) for m, _, _ in parts])
            cx, cy, zmin = allv[:, 0].mean(), allv[:, 1].mean(), allv[:, 2].min()
            vol_ids = list(range(next_id, next_id + len(parts))); obj_id = next_id + len(parts); next_id = obj_id + 1
            sub_name = f'3D/Objects/object_{backup_id}.model'
            # ---- sub-model file: mesh objects only
            sb = io.StringIO(); sb.write(_model_header())
            sb.write(f' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n')
            for k, (m, pname, ext) in enumerate(parts):
                mm = m.copy(); mm.apply_translation([-cx, -cy, -zmin])
                sb.write(f'  <object id="{vol_ids[k]}" p:UUID="{_h8(k + (backup_id << 16))}{SUB_SUF}" type="model">\n')
                sb.write(_mesh_xml(mm)); sb.write('  </object>\n')
                thumbs.append((m, colours[(ext - 1) % len(colours)]))
            sb.write(' </resources>\n <build/>\n</model>\n'); sub_files[sub_name] = sb.getvalue()
            # ---- main model: assembly object with components
            comps = ''.join(f'    <component p:path="/{sub_name}" objectid="{vol_ids[k]}" p:UUID="{_h8(k + (backup_id << 16))}{COMP_SUF}" transform="{IDENT12}"/>\n' for k in range(len(parts)))
            main_res.append(f'  <object id="{obj_id}" p:UUID="{_h8(backup_id)}{OBJ_SUF}" type="model">\n   <components>\n{comps}   </components>\n  </object>\n')
            items.append(f'  <item objectid="{obj_id}" p:UUID="{_h8(obj_id)}{ITEM_SUF}" transform="{_t12(ox + cx, oy + cy, 0)}" printable="1"/>\n')
            # ---- model_settings object
            face_total = sum(len(m.faces) for m, _, _ in parts)
            o = [f'  <object id="{obj_id}">\n', f'    <metadata key="name" value="{_x(ob["name"])}"/>\n',
                 f'    <metadata key="extruder" value="{ob.get("extruder", 1)}"/>\n', f'    <metadata face_count="{face_total}"/>\n']
            for k, (m, pname, ext) in enumerate(parts):
                o.append(f'    <part id="{vol_ids[k]}" subtype="normal_part">\n      <metadata key="name" value="{_x(pname)}"/>\n'
                         f'      <metadata key="matrix" value="{IDENT16}"/>\n      <metadata key="extruder" value="{ext}"/>\n'
                         f'      <mesh_stat face_count="{len(m.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n    </part>\n')
            o.append('  </object>\n'); ms_objects.append(''.join(o))
            plate_insts.append(f'    <model_instance>\n      <metadata key="object_id" value="{obj_id}"/>\n      <metadata key="instance_id" value="0"/>\n      <metadata key="identify_id" value="{identify}"/>\n    </model_instance>\n'); identify += 1
            assemble.append(f'   <assemble_item object_id="{obj_id}" instance_id="0" transform="{_t12(ox + cx, oy + cy, 0)}" offset="0 0 0" />\n')
            cut_xml.append(f'  <object id="{backup_id}"><cut_id id="0" check_sum="1" connectors_cnt="0"/></object>\n')
        pl['_thumbs'] = thumbs
        ms_plates.append(f'  <plate>\n    <metadata key="plater_id" value="{pi + 1}"/>\n    <metadata key="plater_name" value="{_x(pl["name"])}"/>\n'
                         f'    <metadata key="locked" value="false"/>\n    <metadata key="thumbnail_file" value="Metadata/plate_{pi + 1}.png"/>\n{"".join(plate_insts)}  </plate>\n')

    meta = {'Application': f'BambuStudio-{app_version}', 'BambuStudio:3mfVersion': '1', 'Copyright': '', 'CreationDate': today,
            'Description': '', 'Designer': '', 'DesignerCover': '', 'DesignerUserId': '', 'License': '', 'ModificationDate': today,
            'Origin': '', 'ProfileCover': '', 'ProfileDescription': '', 'ProfileTitle': '', 'Title': title}
    main = io.StringIO(); main.write(_model_header())
    for k in sorted(meta): main.write(f' <metadata name="{k}">{_x(meta[k])}</metadata>\n')
    main.write(' <resources>\n'); main.write(''.join(main_res)); main.write(' </resources>\n')
    main.write(f' <build p:UUID="{BUILD_UUID}">\n'); main.write(''.join(items)); main.write(' </build>\n</model>\n')
    model_rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                  + ''.join(f' <Relationship Target="/{p}" Id="rel-{i + 1}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n' for i, p in enumerate(sub_files))
                  + '</Relationships>')
    ms = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + ''.join(ms_objects) + ''.join(ms_plates)
          + '  <assemble>\n' + ''.join(assemble) + '  </assemble>\n</config>\n')
    slice_info = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n  <header>\n    <header_item key="X-BBL-Client-Type" value="slicer"/>\n'
                  f'    <header_item key="X-BBL-Client-Version" value="{app_version}"/>\n  </header>\n</config>\n')
    cut_info = '<?xml version="1.0" encoding="utf-8"?>\n<objects>\n' + ''.join(cut_xml) + '</objects>\n'
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
            ' <Relationship Target="/Metadata/plate_1.png" Id="rel-2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/>\n'
            f' <Relationship Target="/Metadata/plate_1.png" Id="rel-4" Type="{BBL}/cover-thumbnail-middle"/>\n'
            f' <Relationship Target="/Metadata/plate_1_small.png" Id="rel-5" Type="{BBL}/cover-thumbnail-small"/>\n</Relationships>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
          ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
          ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
          ' <Default Extension="png" ContentType="image/png"/>\n <Default Extension="gcode" ContentType="text/x.gcode"/>\n</Types>')
    ps = dict(project_settings); ps['version'] = app_version
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct)
        for pi, pl in enumerate(plates):
            z.writestr(f'Metadata/plate_{pi + 1}.png', _png_thumbnail(pl['_thumbs'], 512, (plate_w, plate_d)))
            z.writestr(f'Metadata/plate_{pi + 1}_small.png', _png_thumbnail(pl['_thumbs'], 128, (plate_w, plate_d)))
        z.writestr('Metadata/project_settings.config', json.dumps(ps, indent=4, ensure_ascii=False))
        z.writestr('Metadata/model_settings.config', ms)
        z.writestr('Metadata/cut_information.xml', cut_info)
        z.writestr('Metadata/slice_info.config', slice_info)
        z.writestr('3D/_rels/3dmodel.model.rels', model_rels)
        for name, xml in sub_files.items(): z.writestr(name, xml)
        z.writestr('3D/3dmodel.model', main.getvalue())
        z.writestr('_rels/.rels', rels)
    return path
