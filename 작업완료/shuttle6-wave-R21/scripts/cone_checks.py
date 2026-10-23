from pathlib import Path
import sys,pickle,json,numpy as np,trimesh as tm
from content_gauges import envelope
O=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(O.parents[1]/'tools'))
from pipeline import inter
p=pickle.load(open(O/'parts_nominal.pkl','rb'));base=pickle.load(open(O/'AS/reference_R20_parts.pkl','rb'));source=pickle.load(open(O/'AS/reference_R18_parts.pkl','rb'));m=p['drawer']
unchanged={n:bool(np.array_equal(v.vertices,base[n].vertices) and np.array_equal(v.faces,base[n].faces)) for n,v in p.items() if n not in ['drawer','shell_lower','shell_upper']};assert all(unchanged.values())
def hit(mesh,origin,direction):
 h,_,_=mesh.ray.intersects_location([origin],[direction],multiple_hits=True)
 return float(np.min(np.linalg.norm(h-np.array(origin),axis=1)))
front=[]
for z in [13.5,14.,16.,20.,24.]:
 r=hit(m,[0,0,z],[0,-1,0]);old=hit(source['drawer'],[0,0,259.8-z],[0,-1,0]);cork=np.sqrt(14**2-(27-z)**2)
 front.append({'tray_z_mm':z,'actual_lower_cavity_radius_mm':r,'original_hat_mirrored_radius_mm':old,'profile_copy_error_mm':abs(r-old),'cork_radius_mm':float(cork),'radial_gap_mm':float(r-cork)})
assert all(v['profile_copy_error_mm']<.05 and v['radial_gap_mm']>.5 for v in front),front
rear=[{'tray_z_mm':z,'lower_cavity_radius_mm':hit(m,[0,0,z],[0,-1,0])} for z in [231.5,235.,238.,240.,243.5]]
assert all(abs(v['lower_cavity_radius_mm']-32.5)<.025 for v in rear),rear
roof=[]
for z in [236.,240.,245.,249.]:
 h,_,_=m.ray.intersects_location([[0,.2,z]],[[0,1,0]],multiple_hits=True);roof.append({'tray_z_mm':z,'upper_roof_hit_count':len(h)});assert len(h)==0,(z,h)
wall=238.1+hit(m,[0,-10,238.1],[0,0,1]);assert abs(wall-244.)<.025,wall
# Terminal face is a thick half-disc, not a thin roof membrane.
back=238.1+max((m.ray.intersects_location([[0,-10,238.1]],[[0,0,1]],multiple_hits=True)[0])[:,2]-238.1);thickness=back-wall;assert thickness>5.7,thickness
fit=[];g=envelope()
for dz in [0.,2.,4.]:
 q=g.copy();q.apply_translation([0,0,dz]);v=inter(m,q);assert v<.01,(dz,v);fit.append({'rearward_stack_shift_mm':dz,'solid_overlap_mm3':v})
rim_tests=[]
for dz in [0.,2.,4.]:
 for dx,dy in [(0,0),(.25,0),(-.25,0),(0,.25),(0,-.25)]:
  disk=tm.creation.cylinder(radius=32.,height=.2,sections=192);disk.apply_translation([dx,dy,238.+dz]);v=inter(m,disk);assert v<.01,(dx,dy,dz,v);rim_tests.append({'dx_mm':dx,'dy_mm':dy,'dz_mm':dz,'solid_overlap_mm3':v})
socket=[]
for z in [5.,7.]:
 lower_radius=1+hit(p['shell_lower'],[0,-1,z],[0,-1,0]);flat_roof=hit(p['shell_lower'],[0,-1,z],[0,1,0])-1;socket.append({'body_z_mm':z,'socket_lower_radius_mm':lower_radius,'radial_gap_to_rear34p6_mm':lower_radius-34.6,'flat_roof_gap_mm':flat_roof})
assert .17<socket[0]['radial_gap_to_rear34p6_mm']<.23 and .17<socket[0]['flat_roof_gap_mm']<.23,socket
assert .32<socket[1]['radial_gap_to_rear34p6_mm']<.38,socket
thinning=[]
new_up=p['shell_upper'].copy();new_up.apply_translation([0,0,121.5]);old_up=base['shell_upper'].copy();old_up.apply_translation([0,0,121.5]);newbody=tm.util.concatenate([p['shell_lower'],new_up]);oldbody=tm.util.concatenate([base['shell_lower'],old_up])
for z in [60.,180.]:
 for d in [[0,-1,0],[0,1,0],[1,0,0]]:
  allhits=[]
  for mesh in [oldbody,newbody]:
   h,_,_=mesh.ray.intersects_location([[0,0,z]],[d],multiple_hits=True);ds=sorted(np.linalg.norm(h-np.array([0,0,z]),axis=1));allhits.append(ds)
  old,new=allhits;assert abs(old[0]-new[0])<.01
  thinning.append({'body_z_mm':z,'direction':d,'old_wall_mm':old[-1]-old[0],'new_wall_mm':new[-1]-new[0],'bore_change_mm':new[0]-old[0]})
dock=pickle.load(open(O/'AS/changed_features.pkl','rb'))['rear_receiver'];dock_slide=[]
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
for distance in [0.,.5,1.,2.,3.,4.,5.,8.,12.]:
 q=m.copy();q.apply_transform(T([0,0,253+distance])@R(np.pi,[0,1,0]));v=inter(dock,q);assert v<.01,(distance,v);dock_slide.append({'travel_mm':distance,'receiver_overlap_mm3':v})
report={'receiver_slide_raw_solid_checks':dock_slide,'front_original_hat_profile_samples':front,'rear_open_boat_lower_radius_samples':rear,'rear_upper_roof_checks':roof,'rear_flat_wall_measured_z_mm':wall,'rear_feather_rim_z_mm':238.,'rear_axial_gap_measured_mm':wall-238.,'rear_end_half_disc_thickness_mm':thickness,'rear_radial_gap_to64mm_rim_mm':min(v['lower_cavity_radius_mm'] for v in rear)-32.,'stack_axial_shift_checks':fit,'feather_rim_offset_checks':rim_tests,'docking_socket_samples':socket,'docking_insertion_depth_mm':7.3-(253-back),'housing_wall_samples':thinning,'other6_parts_unchanged_from_R20':unchanged,'scope':'Actual nominal mesh ray/solid measurements.225mm/64mm dimensional shuttle gauge; no real feather friction, insertion force, impact or physical strength validation.'}
json.dump(report,open(O/'qc/cone_checks.json','w'),ensure_ascii=False,indent=2);print(json.dumps(report),flush=True)
