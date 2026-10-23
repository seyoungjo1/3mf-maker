from pathlib import Path
import sys,pickle,json,numpy as np,trimesh as tm
from scipy.spatial import ConvexHull
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
from content_gauges import individual_gauges,envelope
O=Path(__file__).resolve().parent.parent;ROOT=O.parents[1];sys.path.insert(0,str(ROOT/'tools'))
from pipeline import inter
from beam import calc
p=pickle.load(open(O/'parts_nominal.pkl','rb'));base=pickle.load(open(O/'AS/reference_R18_parts.pkl','rb'))
unchanged={n:bool(np.array_equal(m.vertices,base[n].vertices) and np.array_equal(m.faces,base[n].faces)) for n,m in p.items() if n not in ['shell_upper','drawer']};assert all(unchanged.values())
params=json.load(open(O/'AS/keyring_parameters.json'));center=np.array(params['hole_center_xy_mm'])
up=p['shell_upper'].copy();up.apply_translation([0,0,121.5]);old=base['shell_upper'].copy();old.apply_translation([0,0,121.5]);closed=T([0,0,253])@R(np.pi,[0,1,0]);cap=p['cap'].copy();cap.apply_transform(closed)
cap_overlap=inter(up,cap);assert cap_overlap<.001,cap_overlap
gauge=tm.creation.cylinder(radius=2.5,height=6.,sections=192);gauge.apply_translation([*center,241.]);hole_overlap=inter(up,gauge);assert hole_overlap<.001,hole_overlap
section=up.section(plane_origin=[0,0,241.],plane_normal=[0,0,1]);holes=[loop for loop in section.discrete if np.max(np.linalg.norm(loop[:,:2]-center,axis=1))<3.1];assert len(holes)==1
diameter=np.ptp(holes[0][:,:2],axis=0).tolist();assert all(abs(v-5.)<.002 for v in diameter),diameter
M=np.array(json.load(open(O/'print_transforms.json'))['shell_upper']);end=M@np.array([*center,121.5,1]);assert abs(end[2])<1e-5,end
# Longitudinal table support from the original body and cap, without eyelet.
v=np.vstack([base['shell_lower'].vertices,old.vertices,cap.vertices]);hull=ConvexHull(v[:,[2,1]]);edges=[]
for indices,equation in zip(hull.simplices,hull.equations):
 span=np.ptp(v[indices,2])
 if equation[1]<-.95 and span>150:edges.append((span,equation))
assert edges,'No longitudinal lower support edge'
_,equation=max(edges,key=lambda item:item[0]);region=up.vertices[(up.vertices[:,0]>20)&(up.vertices[:,1]>20)&(up.vertices[:,2]>=238.9)];clearance=-(region[:,[2,1]]@equation[:2]+equation[2]);assert clearance.min()>40,clearance.min();assert abs(up.bounds[0,1]-old.bounds[0,1])<.001
gauges=individual_gauges();g=envelope();fit=inter(g,p['drawer']);assert fit<.01,fit
rear=max(m.bounds[1,2] for m in gauges);assert abs(rear-235)<.001;axial=params['rear_cavity_transition_z_mm']-rear;assert axial>=1.999
pickup=[]
for lift in [0,10,30,60,80]:
 q=gauges[0].copy();q.apply_translation([0,lift,0]);pickup.append({'lift_mm':lift,'drawer_overlap_mm3':inter(q,p['drawer']),'cap_overlap_mm3':inter(q,p['cap'])})
assert all(row['drawer_overlap_mm3']<.01 and row['cap_overlap_mm3']<.01 for row in pickup),pickup
hits,_,_=p['drawer'].ray.intersects_location([[0,-1,100]],[[1,0,0]],multiple_hits=True);inner=2*np.sqrt(np.min(hits[:,0])**2+1);assert abs(inner-64)<.03,inner
report={'hole_nominal_mm':5.,'measured_section_xy_mm':diameter,'hole_gauge_intersection_mm3':hole_overlap,'closed_cap_overlap_mm3':cap_overlap,'unchanged_other7_parts':unchanged,'loop_end_print_z_mm':float(end[2]),'hole_center_xy_body_mm':center.tolist(),'loop_thickness_mm':4.,'nominal_hole_surround_mm':4.,'table_support_equation_z_y_offset':equation.tolist(),'eyelet_table_clearance_mm':float(clearance.min()),'table_scope':'Closed assembly, tray opening upwards, longitudinal support by original body and cap. Eyelet and surrounding corner region X>20,Y>20,Z>=238.9 measured; separate metal keyring not modeled. Roll stability and real surface/print deformation not tested.','shuttle_orientation':'Cork tips toward cap; feather rims toward rear cup.','reversed_gauge_overlap_mm3':fit,'rear_feather_to_taper_axial_gap_mm':float(axial),'main_bore_measured_mm':float(inner),'first_pickup_vs_tray_and_cap':pickup,'pickup_scope':'Rigid envelope lifted through open side. Excludes interaction between adjacent flexible feathers, hand access and physical extraction force.','static_beam_screening':{'assumptions':'20N transverse force; simplified rectangular beam L15,b12,h4mm. Excludes hole concentration, impact, fatigue and actual layers. No load rating.',**calc('cantilever',15.,12.,4.,20.)}}
json.dump(report,open(O/'qc/keyring_checks.json','w'),ensure_ascii=False,indent=2);print(json.dumps(report),flush=True)
