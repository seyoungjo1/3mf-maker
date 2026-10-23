from pathlib import Path
import sys,pickle,json,numpy as np,trimesh as tm
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
O=Path(__file__).resolve().parent.parent;ROOT=O.parents[1];sys.path.insert(0,str(ROOT/'tools'))
from pipeline import inter
from beam import calc
p=pickle.load(open(O/'parts_nominal.pkl','rb'));base=pickle.load(open(O/'AS/reference_R18_parts.pkl','rb'))
unchanged={n:bool(np.array_equal(m.vertices,base[n].vertices) and np.array_equal(m.faces,base[n].faces)) for n,m in p.items() if n!='shell_upper'}
assert all(unchanged.values())
up=p['shell_upper'].copy();up.apply_translation([0,0,121.5]);cap=p['cap'].copy();cap.apply_transform(T([0,0,253])@R(np.pi,[0,1,0]))
cap_overlap=inter(up,cap);assert cap_overlap<.001,cap_overlap
gauge=tm.creation.cylinder(radius=2.5,height=6.,sections=192);gauge.apply_translation([0,-47,241.]);hole_overlap=inter(up,gauge);assert hole_overlap<.001,hole_overlap
section=up.section(plane_origin=[0,0,241.],plane_normal=[0,0,1])
holes=[loop for loop in section.discrete if np.max(np.abs(loop[:,0]))<3 and loop[:,1].min()>-50 and loop[:,1].max()<-44]
assert len(holes)==1,len(holes)
loop=holes[0];r=np.linalg.norm(loop[:,:2]-np.array([0,-47]),axis=1)
diameter=(loop[:,:2].max(axis=0)-loop[:,:2].min(axis=0)).tolist()
assert all(abs(v-5.)<.002 for v in diameter),diameter
printed=pickle.load(open(O/'parts_print.pkl','rb'))['shell_upper'];M=np.array(json.load(open(O/'print_transforms.json'))['shell_upper'])
end=M@np.array([0,-47,243-121.5,1]);assert abs(end[2])<1e-5,end
beam=calc('cantilever',14.5,12.,4.,20.)
q={'hole_nominal_mm':5.,'measured_section_xy_mm':diameter,'hole_gauge_intersection_mm3':hole_overlap,'closed_cap_overlap_mm3':cap_overlap,'other_nominal_parts_bytewise_arrays_unchanged':unchanged,'loop_end_print_z_mm':float(end[2]),'loop_thickness_mm':4.,'minimum_nominal_hole_surround_mm':4.,'root_width_mm':16.,'hole_center_xy_body_mm':[0,-47],'static_beam_screening':{'assumptions':'20N transverse force; rectangular cantilever approximation,L14.5mm,b12mm,h4mm,E3300MPa. Excludes hole stress concentration, actual curved root, layer adhesion, impact and fatigue. No physical load rating.',**beam}}
json.dump(q,open(O/'qc/keyring_checks.json','w'),ensure_ascii=False,indent=2);print(json.dumps(q),flush=True)
