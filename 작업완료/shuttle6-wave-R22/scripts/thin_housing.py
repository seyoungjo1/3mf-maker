"""Thin the decorated wall while retaining the actual bore and load interfaces."""
import numpy as np
from scipy.spatial import cKDTree
from pathlib import Path
import importlib.util
def thin(parts,project):
 sp=importlib.util.spec_from_file_location('outer_reference',Path(project)/'AS/reference_R15_scripts/build.py');b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b)
 xy,normals,_=b.double_curve(4096);tree=cKDTree(xy)
 def smooth(u):
  u=np.clip(u,0,1);return u*u*(3-2*u)
 report={}
 for name in ['shell_lower','shell_upper']:
  m=parts[name].copy(include_cache=False);v=m.vertices.copy();z=v[:,2]+(121.5 if name=='shell_upper' else 0)
  _,ids=tree.query(v[:,:2]);n=normals[ids];depth=np.einsum('ij,ij->i',v[:,:2]-xy[ids],n)
  # End docking, joint and cap/lock remain unchanged. Preserve side rails.
  axial=np.maximum(smooth((z-15)/30)*smooth((105-z)/30),smooth((z-155)/30)*smooth((215-z)/30))
  side=smooth((np.abs(v[:,1])-10)/8)
  radial=np.clip((depth+2.2)/1.6,0,1)
  offset=1.2*axial*side*radial;v[:,:2]-=offset[:,None]*n;m.vertices=v
  assert m.is_volume and len(m.split())==1,(name,m.is_volume,len(m.split()))
  report[name]={'before_volume_mm3':float(parts[name].volume),'after_volume_mm3':float(m.volume),'max_outer_inset_mm':float(offset.max()),'moved_vertex_count':int(np.count_nonzero(offset>1e-8)),'protected_body_z_mm':[[0,15],[105,155],[215,253]],'side_rail_no_move_abs_y_mm':10.}
  parts[name]=m.copy(include_cache=False)
 return report
