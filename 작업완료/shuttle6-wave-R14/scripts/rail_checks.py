"""Measure chamber preservation, real rail gap, six stages and rotation limits."""
import numpy as np
from trimesh.transformations import rotation_matrix as R,translation_matrix as T
from build import P,pressed
from rail_geometry import foot_profile,cam_axes
from pipeline import inter

def validate_rail(parts,shell,closed):
 drawer=parts['drawer'];measurements={}
 angles=np.deg2rad(np.arange(-175,0,5));directions=np.c_[np.cos(angles),np.sin(angles),np.zeros(len(angles))]
 origins=np.tile([0.,0.,100.],(len(angles),1));hits,ids,_=drawer.ray.intersects_location(origins,directions,multiple_hits=True)
 radii=[float(np.min(np.linalg.norm(hits[ids==i]-origins[i],axis=1))) for i in range(len(angles))]
 assert all(abs(r-32.)<.01 for r in radii),radii
 h,_,_=drawer.ray.intersects_location([[0,0,100]],[[0,-1,0]],multiple_hits=True)
 ys=sorted(abs(h[:,1]));assert abs(ys[0]-32)<.01 and abs(ys[-1]-35.2)<.01,ys
 body=shell.copy();body.apply_transform(closed)
 foot_profile();y=P['CAM_FACE_Y'];face=np.array([P['FOOT_HALF_BASE']+P['FOOT_SIDE_SLOPE']*(y-P['FOOT_BOTTOM_Y']),y,100.])
 normal=cam_axes(1)[:,0];origin=face-normal
 def first(mesh):
  h,_,_=mesh.ray.intersects_location([origin],[normal],multiple_hits=True)
  return float(np.min(np.linalg.norm(h-origin,axis=1)))
 gap=first(body)-first(drawer);assert abs(gap-.3)<.015,gap
 measurements.update(inner_radius_min_mm=min(radii),inner_radius_max_mm=max(radii),inner_bottom_y_mm=-ys[0],outer_cradle_bottom_y_mm=-ys[-1],bottom_total_mm=ys[-1]-ys[0],rail_normal_gap_mm=gap,flat_base_width_mm=2*P['FOOT_HALF_BASE'])
 stages=[]
 for d in [0,36,72,108,144,180,216,236]:
  m=drawer.copy();m.apply_transform(T([0,0,d])@closed);v=inter(shell,m)
  assert 0<=v<.01,(d,v)
  stages.append({'extraction_mm':d,'overlap_mm3':v})
 rotations=[];compressed=pressed(drawer);compressed.apply_transform(closed)
 for deg in [0,-.25,.25,-.5,.5,-1,1,-2,2,-3,3,90,180]:
  m=compressed.copy();m.apply_transform(R(np.deg2rad(deg),[0,0,1]));v=inter(shell,m);assert v>=0
  rotations.append({'angle_deg':deg,'overlap_mm3':v})
 assert rotations[0]['overlap_mm3']<.01
 assert all(v['overlap_mm3']>.01 for v in rotations if abs(v['angle_deg'])>=2),rotations
 return {'measurements':measurements,'inner_chamber_ray_radii_mm':radii,'stage_checks':stages,'rotation_checks':rotations,
         'scope':'Actual nominal meshes; chamber is circular and not filled. Compressed cams are kinematic trimming only, not shell elasticity, force, wear or fatigue simulation.'}
