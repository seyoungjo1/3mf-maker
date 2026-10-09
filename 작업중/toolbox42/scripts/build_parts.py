import sys; sys.path.insert(0,'/home/claude')
from load3mf import load_parts; from overhang_check import check
import numpy as np, trimesh, pickle
from shapely.geometry import Polygon, Point
from trimesh.creation import triangulate_polygon, extrude_polygon
P=load_parts('/tmp/claude-0/-home-claude/896aa1c8-8e29-58d9-8e4f-9137638ec972/scratchpad/3mf/in.3mf')
lid=P['lid']; logo=P['logo']; base=P['base']; handle=P['handle']; latch=P['latch']
MAXSLOPE=0.115/0.2
def loops(mesh,z):
    sec=mesh.section(plane_origin=[0,0,z],plane_normal=[0,0,1]); return [Polygon(d[:,:2]) for d in sec.discrete if len(d)>3]
def outer(mesh,z): return max(loops(mesh,z),key=lambda q:q.area)
zz=np.arange(0,6.01,0.1); x0=base.bounds[0,0]+16
s=base.section(plane_origin=[x0,0,0],plane_normal=[1,0,0]); d=np.vstack(s.discrete); yfull=d[(d[:,2]>5.8)&(d[:,2]<7.5),1].min()
g=np.array([d[np.abs(d[:,2]-z)<0.051,1].min()-yfull if (np.abs(d[:,2]-z)<0.051).any() else np.nan for z in zz]); g[g>3]=np.nan
ok=~np.isnan(g); g=np.interp(zz,zz[ok],g[ok]); g=np.maximum.accumulate(g[::-1])[::-1]; g=np.clip(g,0,None); g[zz>=6.0]=0
f=np.array([np.min(g[i:]+MAXSLOPE*(zz[i:]-zz[i])) for i in range(len(zz))])
print('base g(z):',' '.join(f'{z:.1f}:{v:.2f}' for z,v in zip(zz[::5],g[::5])))
print('lid  f(z):',' '.join(f'{z:.1f}:{v:.2f}' for z,v in zip(zz[::5],f[::5])))
print('max horizontal step per 0.2 mm layer:',round(max(f[i]-f[i+2] for i in range(len(f)-2)),4))
full=outer(lid,2.0).buffer(1.15); M=1400
def ring_pts(poly):
    ext=poly.exterior; L=ext.length; xc=(poly.bounds[0]+poly.bounds[2])/2
    st=ext.project(Point(xc,poly.bounds[1])); t=(st+np.linspace(0,L,M,endpoint=False))%L
    pts=np.array([ext.interpolate(v).coords[0] for v in t]); return pts if ext.is_ccw else pts[::-1]
ZTOP=6.0; zs=[z for z in zz if z<=ZTOP]; rings=[ring_pts(full.buffer(-float(f[i])) if f[i]>1e-4 else full) for i,z in enumerate(zs)]
V=np.vstack([np.column_stack([r,np.full(M,z)]) for z,r in zip(zs,rings)]); F=[]
for k in range(len(zs)-1):
    a=k*M; b=(k+1)*M; i=np.arange(M); j=(i+1)%M; F.append(np.column_stack([a+i,a+j,b+j])); F.append(np.column_stack([a+i,b+j,b+i]))
F=np.vstack(F).tolist()
for k,sign in [(0,-1),(len(zs)-1,1)]:
    vv,ff=triangulate_polygon(Polygon(rings[k]),engine='earcut'); bi=len(V); V=np.vstack([V,np.column_stack([vv,np.full(len(vv),zs[k])])]); F.extend(((ff[:,::-1] if sign<0 else ff)+bi).tolist())
loft=trimesh.Trimesh(V,np.array(F),process=True); loft.merge_vertices(); trimesh.repair.fix_normals(loft)
pad_hole=outer(lid,0.5).buffer(-0.3); innerw=sorted(loops(lid,4.0),key=lambda q:q.area)[-2]
P1=extrude_polygon(full.buffer(0.5).difference(pad_hole),3.0); P1.apply_translation([0,0,-0.1])
P2=extrude_polygon(full.buffer(0.5).difference(innerw),ZTOP-2.8+0.2); P2.apply_translation([0,0,2.8])
cap=loft.intersection(P1.union(P2,engine='manifold'),engine='manifold')
lid2=lid.union(cap,engine='manifold'); print('lid2 volume ok',lid2.is_volume, round(lid.volume),'->',round(lid2.volume),'lid∩logo',round(lid2.intersection(logo,engine='manifold').volume,3))
# latch: orientation only (stand on long edge), no geometry change
R=trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0]); latch2=latch.copy(); latch2.apply_transform(R); latch2.apply_translation([0,0,-latch2.bounds[0,2]])
for n,m in [('lid2',lid2),('latch2 (standing)',latch2)]: check(m,n,report_top=4)
pickle.dump({'base':base,'lid':lid2,'logo':logo,'handle':handle,'latch':latch2},open('/home/claude/parts_v3.pkl','wb')); print('saved')
