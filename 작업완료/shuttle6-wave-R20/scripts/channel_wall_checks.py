from pathlib import Path
import pickle,trimesh as tm,numpy as np,json
from shapely.geometry import Polygon,LineString
from shapely import make_valid
O=Path(__file__).resolve().parent.parent
p=pickle.load(open(O/'parts_nominal.pkl','rb'));up=p['shell_upper'].copy();up.apply_translation([0,0,121.5]);body=tm.util.concatenate([p['shell_lower'],up]);results=[]
for z in [60,90,110,120,170,200,220]:
 s=body.section(plane_origin=[0,0,z],plane_normal=[0,0,1]);material=None
 for loop in s.discrete:
  poly=make_valid(Polygon(loop[:,:2]));material=poly if material is None else material.symmetric_difference(poly)
 vals=[]
 for y in np.linspace(-9.4,9.4,95):
  seg=material.intersection(LineString([(33,y),(43,y)]))
  if seg.is_empty:continue
  lines=[seg] if seg.geom_type=='LineString' else [v for v in seg.geoms if v.geom_type=='LineString']
  if not lines:continue
  line=max(lines,key=lambda v:v.bounds[2]);vals.append((line.length,float(y)))
 m=min(vals);results.append({'body_z_mm':z,'minimum_x_wall_interval_mm':m[0],'at_y_mm':m[1]})
assert min(x['minimum_x_wall_interval_mm'] for x in results)>1.2,results
json.dump({'method':'Actual mesh cross-sections; outermost material interval along+X at95 lateral positions per plane. Samples do not establish a global minimum. Joint and intentional stop pockets excluded. Invalid section loops repaired only for the2D measurement, not the mesh.','samples':results},open(O/'qc/channel_wall_samples.json','w'),indent=2)
print(json.dumps(results),flush=True)
