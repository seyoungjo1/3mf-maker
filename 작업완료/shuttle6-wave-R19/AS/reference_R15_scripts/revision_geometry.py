"""R15: preserve C silhouette; shallow foot, round rear guide, patterned seam."""
from pathlib import Path
import sys,json,pickle
import numpy as np,trimesh as tm
from shapely.geometry import Polygon,box as rect
from build import P,PROJ,ROOT,box,cyl,extr,union,diff,cone_cavity_profile,ring_solid,print_transform
sys.path.insert(0,str(ROOT/'tools'))
from efc import pre_expand_first_layer

from build import trough_profiles

def tray_main(end=222.,end_stop=True,decorate=True):
 outer_poly,_,section=trough_profiles()
 trough=extr(section,end-10,10)
 # Broad half-disc boat nose, with a29.6mm square key and protected side springs.
 tongue=union(extr(outer_poly,3.8,6.2),box(-14.8,-29.8,3.2,14.8,-.2,6.2))
 hooks=[];reliefs=[]
 for sign in [-1,1]:
  profile=Polygon([(sign*14.6,3.3),(sign*14.8,3.3),(sign*15.3,4.3),(sign*15.3,5.),(sign*14.6,5.)])
  hook=extr(profile,2.5);hook.apply_transform(np.array([[1,0,0,0],[0,0,-1,-5.],[0,1,0,0],[0,0,0,1]],float));hooks.append(hook)
  def cut(xa,ya,za,xb,yb,zb):
   xa,xb=sorted([sign*xa,sign*xb]);return box(xa,ya,za,xb,yb,zb)
  reliefs.extend([cut(11.2,-27.6,3.19,11.8,.1,7.4),cut(11.2,-5.,3.19,15.55,.1,7.4),cut(11.2,-27.6,6.,15.55,.1,7.4)])
 tongue=diff(union(tongue,*hooks),*reliefs)
 m=union(trough,tongue)
 stations=[P['DETENT_Z']+i*P['DETENT_PITCH'] for i in range(P['DETENT_COUNT'])] if end_stop else [P['DETENT_Z']]
 from rail_geometry import rail_cam
 bosses=[rail_cam(sign,z) for z in stations for sign in [-1,1]]
 return union(m,*bosses)

def rear_head():
 start=P['REAR_START'];lap=P['REAR_LAP'];end=P['TRAY_END']
 outer=cyl(P['TRAY_R'],end-start,start)
 male=tm.boolean.intersection([cyl(P['REAR_MALE_R'],lap+.05,start-lap),box(-40,-40,start-lap-.1,40,0,start+.1)],engine='manifold')
 # Rear cup prints closed end down. The small collar throat has a gradual
 # inside lead; no thin snap tabs or unsupported rim across the print bed.
 profile=np.asarray(cone_cavity_profile(end));zz=np.unique(np.r_[start-lap-1,start-lap,start,np.linspace(start,end-P['STOP_T'],240),profile[:,1]])
 zz=zz[(zz>=start-lap-1)&(zz<=end-P['STOP_T'])]
 rr=np.interp(zz,profile[:,1],profile[:,0],left=32.)
 rr=np.minimum(rr,P['REAR_INNER_R']+.4*np.maximum(zz-start,0))
 theta=np.arange(192)*2*np.pi/192
 rings=[np.c_[r*np.cos(theta),r*np.sin(theta),np.full(192,z)] for r,z in zip(rr,zz)]
 m=diff(union(outer,male),ring_solid(rings))
 import manifold3d as mf
 g=mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices,np.float32),tri_verts=np.asarray(m.faces,np.uint32))).simplify(.015).to_mesh()
 q=tm.Trimesh(np.asarray(g.vert_properties)[:,:3],np.asarray(g.tri_verts),process=False);assert q.is_volume
 return q

def finalize(parts):
 printed={}
 for n,m in parts.items():
  assert m.is_volume and len(m.split())==1,(n,m.is_volume,len(m.split()))
  q=m.copy();q.apply_transform(print_transform(n,m));q=pre_expand_first_layer(q)
  limit=125000 if n=='cap' else 190000
  if len(q.faces)>limit:
   import manifold3d as mf
   for tol in [.005,.01,.02,.04]:
    g=mf.Manifold(mf.Mesh(vert_properties=np.asarray(q.vertices,np.float32),tri_verts=np.asarray(q.faces,np.uint32))).simplify(tol).to_mesh();c=tm.Trimesh(np.asarray(g.vert_properties)[:,:3],np.asarray(g.tri_verts),process=False)
    if c.is_volume and len(c.faces)<limit:q=c;break
  assert q.is_volume and len(q.split())==1 and len(q.faces)<=200000,n
  printed[n]=q;m.export(PROJ/'models'/f'{n}_nominal.stl');q.export(PROJ/'models'/f'{n}_print.stl');pickle.dump({n:q.copy()},open(PROJ/'models'/f'{n}_qc.pkl','wb'))
  print(n,len(m.faces),'->',len(q.faces),q.extents,flush=True)
 total=sum(len(m.faces) for m in printed.values());print('TOTAL',total,flush=True);assert total<=500000,total
 for file,obj in [('parts_nominal.pkl',parts),('parts.pkl',printed)]:pickle.dump({n:m.copy(include_cache=False) for n,m in obj.items()},open(PROJ/file,'wb'))
 up=parts['shell_upper'].copy();up.apply_translation([0,0,P['BODY_SPLIT_Z']]);pickle.dump({'shell':tm.util.concatenate([parts['shell_lower'],up]).copy(include_cache=False)},open(PROJ/'assembled_shell.pkl','wb'))
 seed=ROOT/'작업완료/shuttle6-wave-R14/dimensions.json'
 if not seed.exists():seed=PROJ/'AS/reference_R14_dimensions.json'
 d=json.load(open(seed));d['parameters_mm']=P
 d['print_transforms']={n:print_transform(n,m).tolist() for n,m in parts.items()};d['print_dimensions_mm']={n:m.extents.tolist() for n,m in printed.items()}
 d['detent']={'stations':6,'paired_bosses':12,'pitch_mm':36.,'normal_slide_gap_mm':.3,'nominal_normal_interference_mm':.2,'pocket_normal_offset_mm':.2,'force_N':None,'scope':'Solid low cams. Actual deformation/force/wear untested.'}
 d['rail']={'mode':'Original round C exterior; narrow rounded16mm shoe added only at bottom','foot_bottom_y_mm':-34.8,'foot_width_mm':16.,'normal_gap_mm':.3,'scope':'Partial supports accepted by user. No flared trapezoid and no exterior reinforcement.'}
 d['rear_guide']={'outer_diameter_mm':69.2,'full_round_length_mm':27.8,'male_overlap_mm':10.,'male_od_mm':63.6,'female_id_mm':64.,'glue_gap_per_side_mm':.2,'print':'Separate cup, closed end down; glue into tray. Actual wobble and feather protection require physical check.'}
 from rail_geometry import joint_row
 cy,shift,rr=joint_row()
 d['glue_joint'].pop('open_sector_y_mm',None)
 d['glue_joint'].update(overlap_length_mm=float(P['BODY_SPLIT_Z']+P['GLUE_L']-cy-np.sqrt(rr*rr-4.)),reference_key_span_mm=22.,collar_bottom_z_mm=cy-.05,collar_length_mm=P['BODY_SPLIT_Z']+P['GLUE_L']-cy+.05,key_entry_base_z_mm=cy-.2,key_lower_ramp_mm=2.,rail_passage={'x_halfwidth_mm':10.,'max_y_mm':-29.},scope='Straight cylindrical inner fit and45-degree key retained; outer positive/negative fourth-arc wave joint.')
 d['rail'].update(flat_contact_width_mm=15.,overall_foot_width_mm=16.)
 d['seam']={'mode':'Positive scalloped waves on lower body; matching negative wave sockets at bottom of upper body. Actual interlocking edge follows the fourth engraved arc of the existing motif.','groove_width_mm':1.6,'groove_depth_mm':.4,'wave_rise_mm':float(np.sqrt(rr*rr-4.)),'crest_flat_width_mm':4.,'wave_base_z_mm':cy,'axial_face_clearance_mm':.1,'minimum_collar_engagement_mm':float(P['BODY_SPLIT_Z']+P['GLUE_L']-cy-np.sqrt(rr*rr-4.)),'scope':'A geometric male/female joint, not a decorative line added across a straight seam. Glue and print errors may still show.'}
 d['status']='R15 geometry; awaiting QC, assembly, previews and export'
 json.dump(d,open(PROJ/'dimensions.json','w'),ensure_ascii=False,indent=2)
