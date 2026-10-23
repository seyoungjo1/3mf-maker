from pathlib import Path
import pickle,json,numpy as np,trimesh as tm
from shapely.geometry import Point,box,Polygon
from shapely.affinity import rotate
O=Path(__file__).resolve().parent.parent
# R18 has the reinforced stops but no obsolete bottom eyelet.
p=pickle.load(open(O/'AS/reference_R18_parts.pkl','rb'))
angle=45.;distance=50.5;center=np.array([distance/2**.5,distance/2**.5])
outer=Point(distance,0).buffer(6.5,quad_segs=48).union(box(37.8,-8,45.5,8)).convex_hull
outer=outer.buffer(-1.,join_style=1).buffer(1.,join_style=1)
section=rotate(outer.difference(Point(distance,0).buffer(2.5,quad_segs=48)),angle,origin=(0,0))
lug=tm.creation.extrude_polygon(section,4.,engine='earcut');lug.apply_translation([0,0,239.-121.5])
p['shell_upper']=tm.boolean.union([p['shell_upper'],lug],engine='manifold')
# Preserve the outer14.8mm guide and all stop roots. Expand only the inner void.
# The reversed feather rim ends at235, with2mm axial room before narrowing.
u=np.linspace(0,1,121);r=32-30*u;z=237.+11.55*(.35*u+(.5533333333333333-.35)*u*u/2)/(.45166666666666666)
assert abs(z[-1]-248.55)<1e-6
profile=Polygon([(0,234.9),(32,234.9),(32,237.),*list(zip(r[1:],z[1:])),(0,248.55)])
void=tm.creation.revolve(np.array(profile.exterior.coords),sections=192);void.fix_normals()
p['drawer']=tm.boolean.difference([p['drawer'],void],engine='manifold')
assert all(m.is_volume and len(m.split())==1 for m in p.values())
pickle.dump({n:m.copy(include_cache=False) for n,m in p.items()},open(O/'parts_nominal.pkl','wb'))
json.dump(dict(hole_diameter_mm=5.,hole_center_xy_mm=center.tolist(),hole_center_angle_deg=angle,outer_radius_mm=6.5,thickness_mm=4.,root_width_mm=16.,body_z_low_mm=239.,body_z_high_mm=243.,root_corner_radius_mm=1.,rear_cavity_transition_z_mm=237.,rear_feather_rim_z_mm=235.,rear_axial_clearance_mm=2.,roof_z_mm=248.55),open(O/'AS/keyring_parameters.json','w'),indent=2)
print([(n,len(m.faces)) for n,m in p.items()],flush=True)
