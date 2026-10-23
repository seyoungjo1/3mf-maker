"""Measure positive/negative outer waves and the unchanged straight inner fit."""
import numpy as np
from build import P,double_curve
from rail_geometry import seam_from_s,joint_row

def validate(lower,upper_world):
 xy,normals,circ=double_curve(256);rows=[];base,_,r=joint_row()
 for i in range(0,256,4):
  q=xy[i]*(1-.7/np.linalg.norm(xy[i]));o=[q[0],q[1],base-1]
  def first(m):
   h,_,_=m.ray.intersects_location([o],[[0,0,1]],multiple_hits=True)
   return float(np.min(h[:,2]))
  lo,up=first(lower),first(upper_world);expected=float(seam_from_s(np.array([i*circ/256]))[0]);gap=up-lo
  assert abs(lo-(expected-.05))<.15,(i,lo,expected)
  assert .075<gap<.125,(i,gap)
  rows.append({'circumference_mm':i*circ/256,'lower_positive_top_z_mm':lo,'upper_negative_start_z_mm':up,'axial_gap_mm':gap})
 return {'mode':'Existing straight inner collar/key; actual positive/negative outer scallops follow engraved fourth arcs','crest_flat_width_mm':4.,'min_inner_overlap_mm':float(P['BODY_SPLIT_Z']+P['GLUE_L']-base-np.sqrt(r*r-4.)), 'samples':rows,'scope':'Measured actual nominal meshes. Hidden inner fit is checked separately; glued seam visibility and strength are not physically verified.'}
