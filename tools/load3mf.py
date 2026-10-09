import trimesh, numpy as np, xml.etree.ElementTree as ET, zipfile
NS={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02','p':'http://schemas.microsoft.com/3dmanufacturing/production/2015/06'}
PPATH='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}path'
def M(s):
    if not s: return np.eye(4)
    v=[float(x) for x in s.split()]; m=np.eye(4); m[:3,:3]=np.array(v[:9]).reshape(3,3).T; m[:3,3]=v[9:]; return m
def _mesh(o):
    me=o.find('m:mesh',NS)
    V=np.array([[float(v.get(k)) for k in 'xyz'] for v in me.find('m:vertices',NS)])
    F=np.array([[int(t.get(k)) for k in ('v1','v2','v3')] for t in me.find('m:triangles',NS)])
    return trimesh.Trimesh(V,F,process=False)
def load_parts(path):
    """returns {name: mesh in world coords}; names from model_settings.config part names if present"""
    z=zipfile.ZipFile(path); r=ET.fromstring(z.read('3D/3dmodel.model'))
    objs={o.get('id'):o for o in r.find('m:resources',NS).findall('m:object',NS)}
    names={}
    if 'Metadata/model_settings.config' in z.namelist():
        ms=ET.fromstring(z.read('Metadata/model_settings.config'))
        for ob in ms.findall('object'):
            for pt in ob.findall('part'):
                for md in pt.findall('metadata'):
                    if md.get('key')=='name': names[(ob.get('id'),pt.get('id'))]=md.get('value')
    subcache={}
    def sub(pth):
        if pth not in subcache:
            rr=ET.fromstring(z.read(pth.lstrip('/'))); subcache[pth]={o.get('id'):o for o in rr.find('m:resources',NS).findall('m:object',NS)}
        return subcache[pth]
    out={}
    for it in r.find('m:build',NS):
        T=M(it.get('transform')); top=objs[it.get('objectid')]
        comps=top.find('m:components',NS)
        if comps is None:
            m=_mesh(top); m.apply_transform(T); nm=top.get('name') or f'obj{top.get("id")}'; base=nm; k=2
            while nm in out: nm=f'{base}#{k}'; k+=1
            out[nm]=m; continue
        for c in comps:
            pp=c.get(PPATH); o=(sub(pp) if pp else objs)[c.get('objectid')]
            m=_mesh(o); m.apply_transform(M(c.get('transform'))); m.apply_transform(T)
            nm=names.get((it.get('objectid'),c.get('objectid'))) or o.get('name') or f'obj{c.get("objectid")}'
            base=nm; k=2
            while nm in out: nm=f'{base}#{k}'; k+=1      # 같은 이름의 오브젝트가 여러 개면 #2, #3 … 로 구분
            out[nm]=m
    return out
