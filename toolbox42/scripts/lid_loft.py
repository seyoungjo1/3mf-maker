import sys; sys.path.insert(0,'/home/claude')
from load3mf import load_parts; import mm3mf, numpy as np, trimesh, shapely
from shapely.geometry import Polygon, Point
from trimesh.creation import triangulate_polygon
p=load_parts('/tmp/claude-0/-home-claude/896aa1c8-8e29-58d9-8e4f-9137638ec972/scratchpad/3mf/in.3mf')
lid=p['lid']; logo=p['logo']; base=p['base']
def loops(mesh,z):
    sec=mesh.section(plane_origin=[0,0,z],plane_normal=[0,0,1]); return [Polygon(d[:,:2]) for d in sec.discrete if len(d)>3]
def outer(mesh,z): return max(loops(mesh,z),key=lambda q:q.area)
# base fillet profile at a clean cut (x+16), gaps interpolated, monotone
zz=np.arange(0,6.01,0.1); x0=base.bounds[0,0]+16
s=base.section(plane_origin=[x0,0,0],plane_normal=[1,0,0]); d=np.vstack(s.discrete); yfull=d[(d[:,2]>5.8)&(d[:,2]<7.5),1].min()
ins=np.array([d[np.abs(d[:,2]-z)<0.051,1].min()-yfull if (np.abs(d[:,2]-z)<0.051).any() else np.nan for z in zz])
ins[ins>3]=np.nan; ok=~np.isnan(ins); ins=np.interp(zz,zz[ok],ins[ok]); ins=np.maximum.accumulate(ins[::-1])[::-1]; ins=np.clip(ins,0,None)
ZTOP=6.0; ins[zz>=ZTOP]=0
print('profile:',' '.join(f'{z:.1f}:{v:.2f}' for z,v in zip(zz[::5],ins[::5])))
full=outer(lid,2.0).buffer(1.15)
M=1400
def ring_pts(poly):
    ext=poly.exterior; L=ext.length; xc=(poly.bounds[0]+poly.bounds[2])/2
    start=ext.project(Point(xc,poly.bounds[1])); t=(start+np.linspace(0,L,M,endpoint=False))%L
    pts=np.array([ext.interpolate(v).coords[0] for v in t]); return pts if ext.is_ccw else pts[::-1]
zs=[z for z in zz if z<=ZTOP]; rings=[ring_pts(full.buffer(-float(ins[i])) if ins[i]>1e-4 else full) for i,z in enumerate(zs)]
V=[np.column_stack([r,np.full(M,z)]) for z,r in zip(zs,rings)]; V=np.vstack(V); F=[]
for k in range(len(zs)-1):
    a=k*M; b=(k+1)*M; i=np.arange(M); j=(i+1)%M
    F.append(np.column_stack([a+i,a+j,b+j])); F.append(np.column_stack([a+i,b+j,b+i]))
F=np.vstack(F).tolist()
for k,sign in [(0,-1),(len(zs)-1,1)]:
    vv,ff=triangulate_polygon(Polygon(rings[k]),engine='earcut'); bi=len(V)
    V=np.vstack([V,np.column_stack([vv,np.full(len(vv),zs[k])])]); F.extend(((ff[:,::-1] if sign<0 else ff)+bi).tolist())
loft=trimesh.Trimesh(V,np.array(F),process=True); loft.merge_vertices(); trimesh.repair.fix_normals(loft)
print('loft watertight',loft.is_watertight,'volume',loft.is_volume,round(loft.volume))
pad_hole=outer(lid,0.5).buffer(-0.3)
L5=loops(lid,4.0); innerw=sorted(L5,key=lambda q:q.area)[-2]
P1=trimesh.creation.extrude_polygon(full.buffer(0.5).difference(pad_hole),3.0); P1.apply_translation([0,0,-0.1])
P2=trimesh.creation.extrude_polygon(full.buffer(0.5).difference(innerw),ZTOP-2.8+0.2); P2.apply_translation([0,0,2.8])
band=P1.union(P2,engine='manifold'); cap=loft.intersection(band,engine='manifold'); print('cap volume',cap.is_volume,round(cap.volume))
new=lid.union(cap,engine='manifold')
print('NEW watertight',new.is_watertight,'volume',new.is_volume,'vol',round(lid.volume),'->',round(new.volume),'faces',len(new.faces))
print('lid∩logo',round(new.intersection(logo,engine='manifold').volume,3))
def inner_area(mesh,z):
    L=loops(mesh,z); o=max(L,key=lambda q:q.area); c=[q for q in L if q is not o and q.area>5000]; return round(max(c,key=lambda q:q.area).area) if c else None
print('inner skirt opening z=4: old',inner_area(lid,4),'new',inner_area(new,4))
nz=new.face_normals[:,2]; fc=new.triangles_center; A=new.area_faces
ov=(nz<-0.5)&(fc[:,2]>=0.25)&(fc[:,2]<3); print('downward(<-0.5) 0.25<z<3:',round(A[ov].sum()),' logo floor:',round(A[(nz<-0.7)&(np.abs(fc[:,2]-0.6)<0.05)].sum()))
new.export('Toolbox42_lid_flat.stl')
mm3mf.write_multicolor_3mf('Toolbox42_lid_flat.3mf',[(new,'#30949D','lid'),(logo,'#F2AF38','logo')],object_name='Toolbox42 lid flat')
import lib3mf; w=lib3mf.get_wrapper(); mdl=w.CreateModel(); r=mdl.QueryReader('3mf'); r.SetStrictModeActive(True); r.ReadFromFile('Toolbox42_lid_flat.3mf'); print('lib3mf strict OK')
t=trimesh.load('Toolbox42_lid_flat.3mf'); print('reload (merged) watertight:',[v.is_watertight for v in t.geometry.values()])
