import xml.etree.ElementTree as ET, sys, json
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
for f in ['x/3D/3dmodel.model','x/Metadata/model_settings.config','x/Metadata/project_settings.config','x/[Content_Types].xml','x/_rels/.rels']:
    p='3mf/'+f
    try:
        if f.endswith('project_settings.config'):
            d=json.load(open(p)); print(f,'JSON OK, keys',len(d))
            for k in ['printer_model','printer_settings_id','print_settings_id','filament_settings_id','version','printable_area','nozzle_diameter','filament_colour','printable_height']:
                print('  ',k,'=',d.get(k))
        else:
            r=ET.parse(p).getroot(); print(f,'XML OK')
    except Exception as e: print(f,'ERROR',e)
r=ET.parse('3mf/x/3D/3dmodel.model').getroot()
print('root attrs',r.attrib)
for o in r.find('m:resources',ns):
    oid=o.get('id'); mesh=o.find('m:mesh',ns)
    if mesh is not None:
        vs=mesh.find('m:vertices',ns); ts=mesh.find('m:triangles',ns)
        nv=len(vs); nt=len(ts)
        bad=0; degen=0
        for t in ts:
            a,b,c=int(t.get('v1')),int(t.get('v2')),int(t.get('v3'))
            if max(a,b,c)>=nv or min(a,b,c)<0: bad+=1
            if a==b or b==c or a==c: degen+=1
        # bbox
        xs=[float(v.get('x')) for v in vs]; ys=[float(v.get('y')) for v in vs]; zs=[float(v.get('z')) for v in vs]
        print(f"obj {oid} {o.get('name')}: verts={nv} tris={nt} badidx={bad} degen={degen} bbox x[{min(xs):.1f},{max(xs):.1f}] y[{min(ys):.1f},{max(ys):.1f}] z[{min(zs):.1f},{max(zs):.1f}]")
        # manifold check: each edge used exactly twice opposite
        from collections import Counter
        ec=Counter()
        for t in ts:
            a,b,c=int(t.get('v1')),int(t.get('v2')),int(t.get('v3'))
            for e in ((a,b),(b,c),(c,a)): ec[e]+=1
        open_e=sum(1 for e in ec if ec.get((e[1],e[0]),0)!=1 or ec[e]!=1)
        print('   non-manifold/open edge count:',open_e)
    else:
        comps=o.find('m:components',ns)
        print(f"obj {oid} {o.get('name')}: components ->",[c.attrib for c in comps])
for it in r.find('m:build',ns): print('build item',it.attrib)
