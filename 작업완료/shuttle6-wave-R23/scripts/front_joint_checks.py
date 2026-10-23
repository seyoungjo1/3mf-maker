from pathlib import Path
import pickle,numpy as np,trimesh as tm,json,sys,importlib.util
O=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(O.parents[1]/'tools'));sys.path.insert(0,str(O/'AS/reference_R15_scripts'))
from pipeline import inter
p=pickle.load(open(O/'parts_nominal.pkl','rb'));old=pickle.load(open(O/'AS/reference_R22_parts.pkl','rb'))
unchanged={n:bool(np.array_equal(m.vertices,old[n].vertices) and np.array_equal(m.faces,old[n].faces)) for n,m in p.items() if n not in ['drawer','cap']};assert all(unchanged.values())
rows=[]
for z in [7.6,8.,9.5]:
 for a in np.linspace(0,2*np.pi,32,endpoint=False):
  d=np.array([np.cos(a),np.sin(a),0]);values=[]
  for name in ['drawer','cap']:
   h,_,_=p[name].ray.intersects_location([[0,0,z]],[d],multiple_hits=True);ds=np.linalg.norm(h-[0,0,z],axis=1);values.append(float(max(ds) if name=='drawer' else min(ds)))
  gap=values[1]-values[0];assert .17<gap<.24,(z,a,values)
  rows.append({'z_mm':z,'angle_deg':float(np.rad2deg(a)),'plug_outer_radius_mm':values[0],'socket_inner_radius_mm':values[1],'radial_gap_mm':gap})
h,_,_=p['drawer'].ray.intersects_location([[0,.1,5.]],[[0,0,1]],multiple_hits=True);zs=sorted(h[:,2]);assert abs(zs[0]-6.2)<.02 and abs(zs[1]-11.25)<.03,zs
h,_,_=p['cap'].ray.intersects_location([[0,10,8]],[[0,0,-1]],multiple_hits=True);floor=max(h[:,2]);assert abs(floor-6)<.01
sp=importlib.util.spec_from_file_location('original_press',O/'AS/reference_R15_scripts/build.py');ref=importlib.util.module_from_spec(sp);sp.loader.exec_module(ref)
raw=inter(p['drawer'],p['cap']);proxy=inter(ref.cap_pressed(p['drawer']),p['cap']);oldraw=inter(old['drawer'],old['cap']);assert proxy<.01 and raw<=oldraw+.05,(raw,proxy,oldraw)
box=tm.creation.box([100,100,4]);box.apply_translation([0,0,8]);round_part=tm.boolean.intersection([p['drawer'],box],engine='manifold');v=inter(round_part,p['cap']);assert v<.01,v
result={'other7_parts_unchanged_from_R22':unchanged,'radial_measurements':rows,'radial_gap_min_p1_p5_mm':np.percentile([r['radial_gap_mm'] for r in rows],[0,1,5]).tolist(),'upper_root_start_z_mm':zs[0],'front_cavity_tip_z_mm':zs[1],'solid_root_axial_thickness_mm':zs[1]-zs[0],'cap_socket_floor_z_mm':float(floor),'axial_floor_gap_mm':float(zs[0]-floor),'engagement_length_mm':10-zs[0],'round_zone_cap_overlap_mm3':v,'square_snap_raw_overlap_mm3':raw,'previous_square_snap_raw_overlap_mm3':oldraw,'square_snap_pressed_proxy_overlap_mm3':proxy,'scope':'Actual mesh ray and solid measurements. Original square snap geometry and reliefs retained; seated overlaps recorded separately. Pressed proxy is not force, fatigue or physical fit validation.'}
json.dump(result,open(O/'qc/front_joint_checks.json','w'),indent=2);print(json.dumps({k:v for k,v in result.items() if k!='radial_measurements'}),flush=True)
