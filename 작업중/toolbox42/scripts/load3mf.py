import trimesh, numpy as np, xml.etree.ElementTree as ET, zipfile
NS={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
def M(s):
    v=[float(x) for x in s.split()]; m=np.eye(4); m[:3,:3]=np.array(v[:9]).reshape(3,3).T; m[:3,3]=v[9:]; return m
def load_parts(path):
    z=zipfile.ZipFile(path); r=ET.fromstring(z.read('3D/3dmodel.model'))
    objs={o.get('id'):o for o in r.find('m:resources',NS)}; out={}
    for it in r.find('m:build',NS):
        T=M(it.get('transform')); top=objs[it.get('objectid')]
        comps=top.find('m:components',NS)
        for c in (comps if comps is not None else []):
            o=objs[c.get('objectid')]; me=o.find('m:mesh',NS)
            V=np.array([[float(v.get(k)) for k in 'xyz'] for v in me.find('m:vertices',NS)])
            F=np.array([[int(t.get(k)) for k in ('v1','v2','v3')] for t in me.find('m:triangles',NS)])
            m=trimesh.Trimesh(V,F,process=False); m.apply_transform(T); out[o.get('name')]=m
    return out
