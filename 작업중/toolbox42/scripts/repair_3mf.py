import re, zipfile, json, uuid, shutil, os
src='3mf/in.3mf'
z=zipfile.ZipFile(src)
model=z.read('3D/3dmodel.model').decode('utf-8')
files={n:z.read(n) for n in z.namelist()}

def u(): return str(uuid.uuid4())

# ---------- 1) generic, spec-clean 3MF ----------
g=model.replace("<?xml version='1.0' encoding='utf-8'?>",'<?xml version="1.0" encoding="UTF-8"?>')
g=re.sub(r'<metadata name="BambuStudio:3mfVersion">1</metadata>','',g)
g=g.replace(' printable="1"','')
g=g.replace('<metadata name="Application">BambuStudio-02.03.01.51</metadata>','<metadata name="Application">Toolbox42 (repaired)</metadata>')
with zipfile.ZipFile('Toolbox42_generic.3mf','w',zipfile.ZIP_DEFLATED) as o:
    o.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="png" ContentType="image/png"/></Types>')
    o.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/><Relationship Target="/Metadata/thumbnail.png" Id="rel1" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/></Relationships>')
    o.writestr('3D/3dmodel.model',g)
    o.writestr('Metadata/thumbnail.png',files['Metadata/thumbnail.png'])

# ---------- 2) Bambu project 3MF with namespaces + UUIDs ----------
b=model.replace("<?xml version='1.0' encoding='utf-8'?>",'<?xml version="1.0" encoding="UTF-8"?>')
b=b.replace('<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" unit="millimeter" xml:lang="en-US">',
 '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">')
# object UUIDs
b=re.sub(r'<object id="(\d+)" type="model"', lambda m:f'<object id="{m.group(1)}" p:UUID="{u()}" type="model"', b)
b=re.sub(r'<component objectid="(\d+)" />', lambda m:f'<component objectid="{m.group(1)}" p:UUID="{u()}"/>', b)
b=b.replace("<build>",f"<build p:UUID=\"{u()}\">")
b=re.sub(r'<item objectid="(\d+)"', lambda m:f'<item objectid="{m.group(1)}" p:UUID="{u()}"', b)
assert 'xmlns:BambuStudio' in b
ps=json.loads(files['Metadata/project_settings.config'])
ps.setdefault('version','02.03.01.51')
ps.setdefault('curr_bed_type','Textured PEI Plate')
ps.setdefault('flush_volumes_matrix',['0','280','280','0'])
ps.setdefault('flush_volumes_vector',['140','140','140','140'])
ps.setdefault('flush_multiplier','1')
with zipfile.ZipFile('Toolbox42_P1S_fixed.3mf','w',zipfile.ZIP_DEFLATED) as o:
    for n,d in files.items():
        if n=='3D/3dmodel.model': d=b.encode()
        elif n=='Metadata/project_settings.config': d=json.dumps(ps,indent=4).encode()
        elif n=='_rels/.rels': d=b'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/><Relationship Target="/Metadata/thumbnail.png" Id="rel1" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/></Relationships>'
        o.writestr(n,d)
print('written')
