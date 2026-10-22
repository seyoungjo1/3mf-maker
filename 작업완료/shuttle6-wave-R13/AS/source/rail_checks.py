"""Mesh measurements; no elastic material or service-life claims."""
import numpy as np
from trimesh.transformations import rotation_matrix as R,translation_matrix as T
from build import P,pressed
from pipeline import inter,gaps

def validate_rail(parts,shell,closed):
 def y_first(mesh,z):
  hits,_,_=mesh.ray.intersects_location([[0,0,z]],[[0,-1,0]],multiple_hits=True)
  return float(np.max(hits[:,1]))
 shell_y=y_first(shell,100.)
 tray_y=y_first(parts['drawer'],153.)
 assert abs(shell_y+32.9)<.003,shell_y
 # The ray first crosses the tray's internal floor, then its external floor.
 hits,_,_=parts['drawer'].ray.intersects_location([[0,-31,153]],[[0,-1,0]],multiple_hits=True)
 tray_outer=float(np.max(hits[:,1]))
 assert abs(tray_outer+32.6)<.003,tray_outer
 assert abs(tray_outer-shell_y-.3)<.003
 stages=[]
 for d in [0,36,72,108,144,180,216,236]:
  m=parts['drawer'].copy();m.apply_transform(T([0,0,d])@closed)
  volume=inter(shell,m)
  assert 0<=volume<.01,(d,volume)
  stages.append({'extraction_mm':d,'overlap_mm3':volume,'remaining_rows':max(0,6-int(d/36))})
 rotations=[]
 m=pressed(parts['drawer']);m.apply_transform(closed)
 for deg in [0,-1,1,-2,2,-3,3,-5,5,-15,15,90,180]:
  q=m.copy();q.apply_transform(R(np.deg2rad(deg),[0,0,1]))
  overlap=inter(shell,q)
  assert overlap>=0
  rotations.append({'angle_deg':deg,'overlap_mm3':overlap})
 assert rotations[0]['overlap_mm3']<.01
 assert all(v['overlap_mm3']>.01 for v in rotations if 3<=abs(v['angle_deg'])<=90),rotations
 # Minimum nominal collar wall at a recess: conservative radial bound.
 min_collar=P['GLUE_R']-(np.hypot(P['DETENT_X'],P['DETENT_Y'])+P['DETENT_POCKET_R'])
 assert min_collar>=1.8,min_collar
 positions=[]
 for z in [53,89,125,161,197,233]:
  hit,_,_=shell.ray.intersects_location([[0,P['DETENT_Y'],z]],[[1,0,0]],multiple_hits=True)
  x=float(np.min(hit[:,0]));expected=P['DETENT_X']+P['DETENT_POCKET_R']
  assert abs(x-expected)<.03,(z,x,expected)
  positions.append({'body_z_mm':z,'pocket_x_extent_mm':x})
 return {'flat_measurements':{'shell_flat_y_mm':shell_y,'tray_outer_y_mm':tray_outer,'normal_gap_mm':tray_outer-shell_y},
         'aligned_stage_checks':stages,'rotation_samples_deg':rotations,'pocket_ray_measurements':positions,
         'minimum_collar_wall_radial_bound_mm':float(min_collar),
         'scope':'Rigid intersections and sample rotation obstruction only. Samples block continuous rotation from2deg. An open half-tray may be separately inserted upside-down at180deg; this is not unique orientation coding. Compressed nubs are kinematic proxies; no wall elasticity, click force, wear, torque rating or fatigue simulation.'}
