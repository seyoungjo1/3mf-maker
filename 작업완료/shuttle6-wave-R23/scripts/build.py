from pathlib import Path
import pickle,json,numpy as np,trimesh as tm
O=Path(__file__).resolve().parent.parent
p=pickle.load(open(O/'AS/reference_R22_parts.pkl','rb'))
def cylinder(r,z0,z1):
 m=tm.creation.cylinder(radius=r,height=z1-z0,sections=192);m.apply_translation([0,0,(z0+z1)/2]);return m
def box(a,b):
 a=np.array(a);b=np.array(b);m=tm.creation.box(b-a);m.apply_translation((a+b)/2);return m
# Extend the complete round front-cone root into the separate lid. Keep the
# original square key and its reliefs below the circular seating surface.
plug=cylinder(34.6,6.2,10.1)
reliefs=[]
for sign in [-1,1]:
 for xa,ya,za,xb,yb,zb in [(11.2,-27.6,3.19,11.8,.1,7.4),(11.2,-5.,3.19,15.55,.1,7.4),(11.2,-27.6,6.,15.55,.1,7.4)]:
  xa,xb=sorted([sign*xa,sign*xb]);reliefs.append(box([xa,ya,za],[xb,yb,zb]))
plug=tm.boolean.difference([plug,*reliefs],engine='manifold')
p['drawer']=tm.boolean.union([p['drawer'],plug],engine='manifold')
# A full circular pocket, not the old semicircular pocket, supports the plug
# around its whole circumference. Existing lower foot/square key remain.
socket=cylinder(34.8,6.,10.2);p['cap']=tm.boolean.difference([p['cap'],socket],engine='manifold')
assert all(m.is_volume and len(m.split())==1 for m in p.values())
pickle.dump({n:m.copy(include_cache=False) for n,m in p.items()},open(O/'parts_nominal.pkl','wb'))
params=json.load(open(O/'AS/keyring_parameters.json'));params.update(front_cap_socket_radius_mm=34.8,front_cap_socket_floor_z_mm=6.,front_plug_radius_mm=34.6,front_plug_start_z_mm=6.2,front_plug_engagement_mm=3.8,front_radial_clearance_mm=.2,front_axial_floor_gap_mm=.2,front_round_root_backing_thickness_mm=5.05,front_socket_shape='Full circle in cap, original lower shoe and square key retained')
json.dump(params,open(O/'AS/keyring_parameters.json','w'),indent=2)
features=pickle.load(open(O/'AS/changed_features.pkl','rb'));features.update(front_plug=plug.copy(include_cache=False),cap_socket_cut=socket.copy(include_cache=False));pickle.dump(features,open(O/'AS/changed_features.pkl','wb'))
print([(n,len(m.faces),m.is_volume) for n,m in p.items()],flush=True)
