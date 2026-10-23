import numpy as np,trimesh as tm
from shapely.geometry import Polygon
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
def individual_gauges():
 meshes=[]
 for i in reversed(range(6)):
  start=10.+28*i;center=start+71;theta=np.linspace(0,np.pi/2,41)
  pts=[(0,start),(32,start),(12.5,start+62),(14,start+62),(14,center)]
  pts += [(14*np.cos(a),center+14*np.sin(a)) for a in theta[1:]];pts += [(0,start)]
  m=tm.creation.revolve(np.array(Polygon(pts).exterior.coords),sections=96);m.fix_normals();m.apply_transform(T([0,0,248.])@R(np.pi,[0,1,0]));meshes.append(m)
 return meshes
def envelope():return tm.boolean.union(individual_gauges(),engine='manifold')
