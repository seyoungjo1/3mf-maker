"""Same-revision cap-joint update; preserve the exact body meshes under independent QC."""
from pathlib import Path
import sys,pickle,json,hashlib,numpy as np
P=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(P/'scripts'));from build import make_cap,make_drawer,print_transform
sys.path.insert(0,str(P.parent.parent/'tools'));from efc import pre_expand_first_layer
nominal=pickle.load(open(P/'parts_nominal.pkl','rb'));printed=pickle.load(open(P/'parts.pkl','rb'))
before={n:hashlib.sha256(nominal[n].vertices.tobytes()+nominal[n].faces.tobytes()).hexdigest() for n in ['shell_lower','shell_upper']}
names=['drawer','drawer_coupon'] if '--tray-only' in sys.argv else ['cap','drawer','drawer_coupon']
nominal.update(drawer=make_drawer(),drawer_coupon=make_drawer(42.,False,False))
if 'cap' in names:nominal['cap']=make_cap()
for n in names:
 m=nominal[n];assert m.is_volume and len(m.split())==1,(n,m.is_volume)
 m.export(P/'models'/f'{n}_nominal.stl')
 q=m.copy();q.apply_transform(print_transform(n,m));printed[n]=pre_expand_first_layer(q)
 if len(printed[n].faces)>(130000 if n=='cap' else 190000):
  import manifold3d as mf
  import trimesh as tm
  raw=printed[n]
  for tolerance in [.005,.01,.02,.04]:
   g=mf.Manifold(mf.Mesh(vert_properties=np.asarray(raw.vertices,np.float32),tri_verts=np.asarray(raw.faces,np.uint32))).simplify(tolerance).to_mesh()
   candidate=tm.Trimesh(np.asarray(g.vert_properties)[:,:3],np.asarray(g.tri_verts),process=False)
   if candidate.is_volume and len(candidate.faces)<(130000 if n=='cap' else 190000):printed[n]=candidate;break
 printed[n].export(P/'models'/f'{n}_print.stl')
 pickle.dump({n:printed[n]},open(P/'models'/f'{n}_qc.pkl','wb'))
 assert len(printed[n].faces)<200000
pickle.dump(nominal,open(P/'parts_nominal.pkl','wb'));pickle.dump(printed,open(P/'parts.pkl','wb'))
d=json.load(open(P/'dimensions.json'));d['parameters_mm']['CAP_JOINT_L']=4.
d['parameters_mm'].update(CAP_SQUARE_SIDE=30.,CAP_SQUARE_DEPTH=3.,CAP_KEY_SIDE=29.6,CAP_SNAP_L=22.6,CAP_SNAP_T=3.,CAP_SNAP_B=2.8,CAP_SNAP_DEFLECTION=.4)
d['cap_joint']={'pocket_depth_mm':4.,'tongue_length_mm':3.8,'gap_per_side_mm':.2,'floor_gap_mm':.2,'primary_pocket_floor_z_mm':6.,'minimum_front_wall_mm':3.,'square_pocket_side_mm':30.,'square_pocket_depth_mm':3.,'square_key_side_mm':29.6,'square_key_length_mm':3.,'mode':'Full half-disc socket plus30mm square pocket and protected snap beams. Physical cap retention is not rated.'}
for n in names:
 d['print_transforms'][n]=print_transform(n,nominal[n]).tolist();d['print_dimensions_mm'][n]=(printed[n].bounds[1]-printed[n].bounds[0]).tolist()
json.dump(d,open(P/'dimensions.json','w'),ensure_ascii=False,indent=2)
after={n:hashlib.sha256(nominal[n].vertices.tobytes()+nominal[n].faces.tobytes()).hexdigest() for n in before};assert before==after
json.dump({'same_revision_body_meshes_unchanged':True,'body_sha256':after,'updated':['cap','drawer','drawer_coupon'],'scope':'Latest user changes only the front cap/tray connection. Default build.py reproduces complete geometry from scratch.'},open(P/'qc/cap_joint_update.json','w'),ensure_ascii=False,indent=1)
print({n:len(m.faces) for n,m in printed.items()})
