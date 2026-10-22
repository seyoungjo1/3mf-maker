"""Build R14 while preserving the approved R13 ornamented parent surfaces."""
from pathlib import Path
import sys,pickle,json
import numpy as np
import trimesh as tm
PTH=Path(__file__).resolve().parent.parent;ROOT=PTH.parent.parent
sys.path.insert(0,str(PTH/'scripts'));sys.path.insert(0,str(ROOT/'tools'))
from build import P,make_drawer,make_cap,print_transform,box
from rail_geometry import adapt_R13_pair,make_shell_coupon,foot_profile
from efc import pre_expand_first_layer
base=ROOT/'작업완료/shuttle6-wave-R13'
old=pickle.load(open(base/'parts_nominal.pkl','rb'))
lo,up=adapt_R13_pair(old['shell_lower'],old['shell_upper'])
drawer=make_drawer()
tip=tm.boolean.intersection([drawer,box(-50,-50,240,50,50,251)],engine='manifold');tip.apply_translation([0,0,-240])
parts={'shell_lower':lo,'shell_upper':up,'drawer':drawer,'cap':make_cap(),'shell_coupon':make_shell_coupon(),'drawer_coupon':make_drawer(42.,False,False),'tip_coupon':tip}
printed={}
for n,m in parts.items():
 assert m.is_volume and len(m.split())==1,(n,m.is_volume,len(m.split()))
 q=m.copy();q.apply_transform(print_transform(n,m));printed[n]=pre_expand_first_layer(q)
 if len(printed[n].faces)>(130000 if n=='cap' else 190000):
  import manifold3d as mf
  raw=printed[n]
  for tol in [.005,.01,.02,.04]:
   g=mf.Manifold(mf.Mesh(vert_properties=np.asarray(raw.vertices,np.float32),tri_verts=np.asarray(raw.faces,np.uint32))).simplify(tol).to_mesh()
   candidate=tm.Trimesh(np.asarray(g.vert_properties)[:,:3],np.asarray(g.tri_verts),process=False)
   if candidate.is_volume and len(candidate.faces)<(130000 if n=='cap' else 190000):printed[n]=candidate;break
 assert printed[n].is_volume and len(printed[n].split())==1,n
 assert len(printed[n].faces)<=200000,(n,len(printed[n].faces))
 m.export(PTH/'models'/f'{n}_nominal.stl');printed[n].export(PTH/'models'/f'{n}_print.stl')
 pickle.dump({n:printed[n].copy()},open(PTH/'models'/f'{n}_qc.pkl','wb'))
 print(n,'faces',len(m.faces),'->',len(printed[n].faces),'size',printed[n].extents,flush=True)
assert sum(len(m.faces) for m in printed.values())<=500000
pickle.dump({n:m.copy() for n,m in parts.items()},open(PTH/'parts_nominal.pkl','wb'))
pickle.dump({n:m.copy() for n,m in printed.items()},open(PTH/'parts.pkl','wb'))
up=up.copy();up.apply_translation([0,0,P['BODY_SPLIT_Z']]);shell=tm.util.concatenate([lo,up])
pickle.dump({'shell':shell},open(PTH/'assembled_shell.pkl','wb'))
d=json.load(open(base/'dimensions.json'));d['parameters_mm'].update(P)
d['rail']={'mode':'Add external cradle; retain full circular64mm chamber','foot_bottom_y_mm':P['FOOT_BOTTOM_Y'],'base_width_mm':P['FOOT_HALF_BASE']*2,'normal_gap_mm':.3,'shell_reinforcement_mm':2.6,'sloped_side_dx_per_print_layer_mm':.08,'support_scope':'Full print QC still required; no promise of zero support before checking.'}
d['detent']={'stations':6,'paired_bosses':12,'pitch_mm':36.,'nominal_normal_interference_mm':.1,'pocket_normal_offset_mm':.2,'placement':'On the two flared cradle faces, inside the outer-shell rail channel. No upper-rim detents or thin tabs. Shell compliance, wear and force untested.'}

for obsolete in ['FLAT_OUTER_Y','FLAT_INNER_Y','DETENT_R','DETENT_X','DETENT_Y','DETENT_POCKET_R']:
 d['parameters_mm'].pop(obsolete,None)
d.pop('measured_flat_floor_thickness_mm',None)
d.pop('preserved_R12_parts_sha256',None)
d['glue_joint']['minimum_socket_outer_wall_mm']=1.45
d['glue_joint'].update(overlap_length_mm=P['GLUE_L'],open_sector_y_mm=P['COLLAR_CUT_Y'],scope='Bottom of collar is open for the cradle channel. Longer22mm engagement compensates nominal bonded wrap area; not a measured bond-strength guarantee.')
d['capacity_basis']='Full open semicircular64mm chamber restored, centered atY0. Six nested225mm remains an unmeasured brand assumption.'
d['print_transforms']={n:print_transform(n,m).tolist() for n,m in parts.items()};d['print_dimensions_mm']={n:m.extents.tolist() for n,m in printed.items()}
d['status']='R14 built; additive cradle and matching six-detent channel; awaiting QC/assembly/print export'
json.dump(d,open(PTH/'dimensions.json','w'),ensure_ascii=False,indent=2)
print('TOTAL',sum(len(m.faces) for m in printed.values()),flush=True)
