from pathlib import Path
import sys,pickle,json,numpy as np,trimesh as tm
from shapely.geometry import Polygon,box
from trimesh.transformations import rotation_matrix as R,translation_matrix as T
PTH=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(PTH/'scripts'))
from build import P,pressed,union,cap_pressed

def envelope():
 """Rigid dimensional gauge only, not a rigid material model of feather shuttlecocks."""
 meshes=[]
 for i in range(6):
  start=10.+28*i;center=start+71
  theta=np.linspace(0,np.pi/2,41)
  pts=[(0,start),(32,start),(12.5,start+62),(14,start+62),(14,center)]
  pts += [(14*np.cos(a),center+14*np.sin(a)) for a in theta[1:]]
  pts += [(0,start)]
  m=tm.creation.revolve(np.asarray(Polygon(pts).exterior.coords),sections=96);m.fix_normals();m.apply_translation([0,2,0]);meshes.append(m)
 return union(*meshes)

def define(parts):
 from pipeline import inter,gaps
 shell=pickle.load(open(PTH/'assembled_shell.pkl','rb'))['shell']
 core=envelope();pickle.dump({'contents':core},open(PTH/'content_envelopes.pkl','wb'))
 closed=T([0,0,P['CLOSED_L']])@R(np.pi,[0,1,0])
 in_shell=core.copy();in_shell.apply_transform(closed)
 measures={'drawer_vs_dimensional_gauge_mm3':inter(parts['drawer'],core),'shell_vs_dimensional_gauge_mm3':inter(shell,in_shell),'cap_joint_overlap_mm3':inter(parts['cap'],parts['drawer'])}
 assert all(0<=v<.01 for v in measures.values()),measures
 dim=json.load(open(PTH/'dimensions.json'))
 # Actual straight section ray hit; compensate the1mm off-axis offset analytically.
 hits,_,_=parts['drawer'].ray.intersects_location([[0,-1,100]],[[1,0,0]],multiple_hits=True)
 xs=sorted(hits[:,0]);inner=2*float(np.sqrt(xs[0]**2+1))
 floor_hits,_,_=parts['drawer'].ray.intersects_location([[0,0,100]],[[0,-1,0]],multiple_hits=True)
 fy=sorted(abs(floor_hits[:,1]));floor=float(fy[-1]-fy[0])
 assert abs(inner-64)<.015 and abs(floor-2.6)<.015,(inner,floor)
 dim['measured_open_tray_id_mm']=inner;dim['measured_flat_floor_thickness_mm']=floor
 dim['measured_flat_base_width_mm']=float(2*np.sqrt(P['TRAY_R']**2-P['FLAT_OUTER_Y']**2))
 dim['detent']['actual_boss_x_extreme_mm']=float(parts['drawer'].bounds[1,0])
 dim['detent']['actual_x_interference_mm']=float(parts['drawer'].bounds[1,0]-np.sqrt((P['ID']/2)**2-P['DETENT_Y']**2))
 v_detent=parts['drawer'].vertices
 radial=np.linalg.norm(v_detent[:,:2],axis=1)
 dim['detent']['measured_vertex_radial_interference_mm']=float(np.max(radial[(v_detent[:,2]>15)&(v_detent[:,2]<205)])-P['ID']/2)
 from rail_checks import validate_rail
 measures['rail_and_detents']=validate_rail(parts,shell,closed)
 dim['rail']['measured']=measures['rail_and_detents']['flat_measurements']
 dim['cap_joint']['actual_solid_overlap_mm3']=measures['cap_joint_overlap_mm3']
 h,_,_=parts['cap'].ray.intersects_location([[24,-12,12]],[[0,0,-1]],multiple_hits=True)
 pocket_floor=float(np.max(h[:,2]));pocket_depth=10-pocket_floor
 h,_,_=parts['drawer'].ray.intersects_location([[24,-12,0]],[[0,0,1]],multiple_hits=True)
 zz=sorted(h[:,2]);nose_front=float(zz[0]);nose_end=float(zz[1])
 assert abs(pocket_depth-4)<.015 and abs(nose_end-nose_front-3.8)<.015,(pocket_depth,zz)
 dim['cap_joint']['measured_pocket_depth_mm']=pocket_depth
 dim['cap_joint']['measured_solid_tongue_length_mm']=nose_end-nose_front
 dim['cap_joint']['measured_floor_gap_mm']=nose_front-pocket_floor
 measures['cap_joint_measured']=dict(dim['cap_joint'])
 cap_insertions=[]
 for distance in [-6,-4,-2,-1,0]:
  m=parts['cap'].copy();m.apply_translation([0,0,distance])
  cap_insertions.append({'cap_offset_mm':distance,'solid_overlap_mm3':inter(parts['drawer'],m)})
 assert cap_insertions[-1]['solid_overlap_mm3']<.01,cap_insertions
 # Intermediate raw hook overlap is intentional; deflected arms are checked separately.
 deflected=cap_pressed(parts['drawer'])
 cap_passes=[]
 for distance in [-1.5,-1.,-.5]:
  m=parts['cap'].copy();m.apply_translation([0,0,distance])
  cap_passes.append({'cap_offset_mm':distance,'compressed_overlap_mm3':inter(deflected,m)})
 assert all(0<=v['compressed_overlap_mm3']<.01 for v in cap_passes),cap_passes
 measures['cap_deflected_insertion_checks']=cap_passes
 measures['cap_joint_insertion_checks']=cap_insertions
 h,_,_=parts['cap'].ray.intersects_location([[0,-12,12]],[[0,0,-1]],multiple_hits=True)
 square_floor=float(np.max(h[:,2]));dim['cap_joint']['measured_square_pocket_depth_mm']=pocket_floor-square_floor
 h,_,_=parts['cap'].ray.intersects_location([[0,-15,4]],[[1,0,0]],multiple_hits=True)
 dim['cap_joint']['measured_square_pocket_side_mm']=2*float(np.min(h[:,0]))
 assert abs(dim['cap_joint']['measured_square_pocket_side_mm']-30)<.02
 assert abs(dim['cap_joint']['measured_square_pocket_depth_mm']-3)<.02
 measures['cap_joint_measured']=dict(dim['cap_joint'])
 import mm
 spring=mm.run('snapfit',L=22.6,t=3.,b=2.8,Y=.4,E=3300.,Q=1.,mu=.3,lead=26.565,allow=.02)
 assert spring['nominal_root_stress_MPa']<12.5,spring
 spring['orientation_note']='Spring length is in printerZ for horizontal tray; use12.5MPa conservative nominal stress target. Excludes notch stress, fatigue and actual layer strength.'
 json.dump(spring,open(PTH/'cap_snap_linear_R13.json','w'),ensure_ascii=False,indent=1,allow_nan=False)


 roof=P['END_ACTUAL_ROOF_Z'];v=np.asarray(parts['drawer'].vertices)
 sel=(np.abs(v[:,0])<1e-4)&(v[:,1]>-2.3)&(v[:,1]<-1.8)&(v[:,2]>roof-.4)&(v[:,2]<roof+.001)
 tip=np.unique(v[sel],axis=0);tip=tip[np.argsort(tip[:,2])];a,b=tip[-2:]
 angle=float(np.rad2deg(np.arctan2(b[2]-a[2],b[1]-a[1])))
 dim['end_geometry']['measured_nominal_mesh_chord_from_bed_deg']=angle
 dim['end_geometry']['measured_nominal_bridge_width_mm']=2*abs(float(b[1]))
 assert abs(angle-30)<.6
 json.dump(dim,open(PTH/'dimensions.json','w'),ensure_ascii=False,indent=2)
 compressed=pressed(parts['drawer']);coupon_compressed=pressed(parts['drawer_coupon'])
 # Record the intended elastic bead crossing as interference, not a zero-force/zero-collision claim.
 crossings=[]
 for distance in [0,.5,2,10,18,34,36,54,72,90,108,126,144,162,180,190,216,236]:
  m=parts['drawer'].copy();m.apply_transform(T([0,0,distance])@closed)
  crossings.append({'extraction_mm':distance,'rigid_overlap_mm3':inter(shell,m)})
 assert all(v['rigid_overlap_mm3']<.01 for v in crossings if v['extraction_mm'] in [0,36,72,108,144,180,216,236]),crossings
 measures['detent_crossing_without_compliance']=crossings
 upper=parts['shell_upper'].copy();upper.apply_translation([0,0,P['BODY_SPLIT_Z']])
 rotations=[]
 for deg in [0,-.5,.5,-1,1,-3,3,90]:
  rotated=upper.copy();rotated.apply_transform(R(np.deg2rad(deg),[0,0,1]))
  rotations.append({'angle_deg':deg,'solid_overlap_mm3':inter(parts['shell_lower'],rotated)})
 assert rotations[0]['solid_overlap_mm3']<.01,rotations
 assert all(item['solid_overlap_mm3']>.01 for item in rotations[3:]),rotations
 measures['glue_key_rotation_checks']=rotations
 # Measure the mating geometry from nominal mesh ray hits in key-local coordinates.
 lo=parts['shell_lower'].copy();up=upper.copy()
 inv=R(-np.deg2rad(P['GLUE_KEY_ANGLE']),[0,0,1]);lo.apply_transform(inv);up.apply_transform(inv)
 z=P['BODY_SPLIT_Z']+7
 def ray_hits(mesh,origin,direction):
  h,_,_=mesh.ray.intersects_location([origin],[direction],multiple_hits=True)
  return sorted(np.linalg.norm(h-np.array(origin),axis=1).tolist())
 a=ray_hits(lo,[0,0,z],[-1,0,0]);b=ray_hits(up,[0,0,z],[-1,0,0])
 kr=ray_hits(lo,[0,0,z],[1,0,0]);sr=ray_hits(up,[0,0,z],[1,0,0])
 ks=ray_hits(lo,[37.5,0,z],[0,1,0]);ss=ray_hits(up,[37.5,0,z],[0,1,0])
 joint={'collar_wall_mm':a[1]-a[0],'radial_gap_mm':b[0]-a[1],'key_tip_gap_mm':sr[0]-kr[1],'key_side_gap_mm':ss[0]-ks[0],'key_width_mm':2*ks[0]}
 assert abs(joint['collar_wall_mm']-2.2)<.02,joint
 assert abs(joint['radial_gap_mm']-.15)<.02,joint
 assert abs(joint['key_tip_gap_mm']-.15)<.02,joint
 assert abs(joint['key_side_gap_mm']-.10)<.02,joint
 insertions=[]
 for dz in [0,2,5,10,14,16]:
  m=upper.copy();m.apply_translation([0,0,dz])
  insertions.append({'remaining_insertion_mm':dz,'overlap_mm3':inter(parts['shell_lower'],m)})
 assert all(0<=v['overlap_mm3']<.01 for v in insertions),insertions
 measures['glue_joint_measured']=joint
 measures['glue_joint_axial_insertion_checks']=insertions
 dim['glue_joint']['measured']=joint
 json.dump(dim,open(PTH/'dimensions.json','w'),ensure_ascii=False,indent=2)

 measures['scope']='Nominal64mm dimensional gauge offset upward2mm over flat floor,6 nested225mm assumption. Not a measured feather envelope or deformation/contact simulation. Six paired broad beads have intentional elastic crossing; trough-wall compliance is not simulated and click force is not calculated.'
 json.dump(measures,open(PTH/'fit_R13.json','w'),ensure_ascii=False,indent=2)
 G=T([100,255,40])@R(np.pi/2,[1,0,0])
 st={'닫힘':{'shell':G,'drawer':G@closed,'cap':G@closed}}
 for d in [18,54,90,126,162,186]:st[f'딸깍 통과 {d}mm']={'shell':G,'drawer_compressed':G@T([0,0,d])@closed,'cap':G@T([0,0,d])@closed}
 for d in [36,72,108,144,180,216,236]:st[f'인출 {d}mm']={'shell':G,'drawer':G@T([0,0,d])@closed,'cap':G@T([0,0,d])@closed}
 st['열림']={'shell':G,'drawer':G@T([0,0,236])@closed,'cap':G@T([0,0,236])@closed}
 st['분리']={'shell':G,'drawer':T([90,0,0])@G@T([0,0,236])@closed,'cap':T([90,0,0])@G@T([0,0,256])@closed}
 st['몸통 접착']={'shell_lower':G,'shell_upper':G@T([0,0,P['BODY_SPLIT_Z']])}
 st['뚜껑 끼움 전']={'drawer':np.eye(4),'cap':T([0,0,-15])}
 st['뚜껑 딸깍 통과']={'drawer_cap_pressed':np.eye(4),'cap':T([0,0,-1.])}
 st['뚜껑 끼움 완료']={'drawer':np.eye(4),'cap':np.eye(4)}
 st['64 공칭 게이지']={'drawer':np.eye(4),'contents':np.eye(4)}
 cc=T([0,0,46])@R(np.pi,[0,1,0])
 st['딸깍 시험편 닫힘']={'shell_coupon':np.eye(4),'drawer_coupon':cc}
 st['딸깍 시험편 통과']={'shell_coupon':np.eye(4),'coupon_compressed':T([0,0,3])@cc}
 placed={}
 for name,m,M in [('shell',shell,G),('drawer',parts['drawer'],G@closed),('cap',parts['cap'],G@closed)]:
  q=m.copy();q.apply_transform(M);placed[name]=q
 pickle.dump(placed,open(PTH/'figures/closed_coordinates_R13.pkl','wb'))
 import drawing
 return {'states':st,'extra':{'shell':shell,'drawer_compressed':compressed,'contents':core,'coupon_compressed':coupon_compressed,'drawer_cap_pressed':deflected},
 'pairs':[['drawer_cap_pressed','cap',{'contact':True}],['shell','drawer',{'contact':True}],['shell','drawer_compressed',{'contact':True}],['shell','cap',{'contact':True}],['drawer','cap',{'contact':True}],['drawer_compressed','cap',{'contact':True}],['shell_lower','shell_upper',{'contact':True}],['drawer','contents',{'contact':True}],['shell_coupon','drawer_coupon',{'contact':True}],['shell_coupon','coupon_compressed',{'contact':True}]],
 'notes':['R13: Open nominal ID64, flat lower plane and2.6mm floor. Feather compliance is not modelled as rigid plastic.','Tray prints horizontally on diagonal; cap separately face down. Body only2pieces upright.','Long clip and release button removed; six pairs of low broad solid beads meet matching inner-shell pockets. Pull-through feel only, no rated positive lock.','Bead crossing poses use a geometrically compressed bead for collision checks; this is a kinematic representation, not FEA or force validation.',f'Actual dimensional/closed joint overlaps: {measures}.','Cap has4mm full half-disc socket plus30x30x3mm square pocket; solid boat nose has protected spring hooks. Nominal closed overlap and deflected passage are checked; no rated real retention strength.'], 'sweeps':[]}
