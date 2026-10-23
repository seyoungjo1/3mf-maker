from pathlib import Path
import pickle,sys,numpy as np,trimesh as tm
from shapely.geometry import Point,box
O=Path(__file__).resolve().parent.parent
p=pickle.load(open(O/'AS/reference_R18_parts.pkl','rb'))
# Body coordinates: the upper shell is printed mouth-down at bodyZ243.
# The opposite side from the positive-Y latch remains clear when the cap opens.
params=dict(hole_diameter_mm=5.,hole_center_xy_mm=[0.,-47.],outer_radius_mm=6.5,thickness_mm=4.,root_width_mm=16.,root_inside_y_mm=-35.,body_z_low_mm=239.,body_z_high_mm=243.,root_corner_radius_mm=1.)
outer=Point(0,-47).buffer(6.5,quad_segs=48).union(box(-8,-42,8,-35)).convex_hull
outer=outer.buffer(-1.,join_style=1).buffer(1.,join_style=1)
section=outer.difference(Point(0,-47).buffer(2.5,quad_segs=48))
lug=tm.creation.extrude_polygon(section,4.,engine='earcut');lug.apply_translation([0,0,239.-121.5])
p['shell_upper']=tm.boolean.union([p['shell_upper'],lug],engine='manifold')
assert all(m.is_volume and len(m.split())==1 for m in p.values())
pickle.dump({n:m.copy(include_cache=False) for n,m in p.items()},open(O/'parts_nominal.pkl','wb'))
import json
json.dump(params,open(O/'AS/keyring_parameters.json','w'),indent=2)
print([(n,len(m.faces)) for n,m in p.items()],flush=True)
