from pathlib import Path
import pickle,json,numpy as np,trimesh as tm
from shapely.geometry import Point,box as rect,Polygon
from shapely.affinity import scale
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
O=Path(__file__).resolve().parent.parent
p=pickle.load(open(O/'AS/reference_R20_parts.pkl','rb'));original=pickle.load(open(O/'AS/reference_R18_parts.pkl','rb'))
def box(x0,y0,z0,x1,y1,z1):
 m=tm.creation.box([x1-x0,y1-y0,z1-z0]);m.apply_translation([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2]);return m
def cyl(radius,z0,z1):
 m=tm.creation.cylinder(radius=radius,height=z1-z0,sections=192);m.apply_translation([0,0,(z0+z1)/2]);return m
def extr(poly,z0,z1):
 m=tm.creation.extrude_polygon(poly,z1-z0,engine='earcut');m.apply_translation([0,0,z0]);return m
def union(*ms):return tm.boolean.union(list(ms),engine='manifold')
def diff(a,*ms):return tm.boolean.difference([a,*ms],engine='manifold')
# Fill the old rear void first: no hidden remnant of the old cone is retained.
drawer=union(p['drawer'],cyl(34.6,235.,249.8))
profile=Polygon([(0,228.9),(32,228.9),(32.5,231.),(32.5,244.),(0,244.)])
rear_void=tm.creation.revolve(np.array(profile.exterior.coords),sections=192);rear_void.fix_normals();drawer=diff(drawer,rear_void)
# Open boat ending. Keep only the two original side-stop posts above the rim.
keep_posts=union(box(30,0,242,40,9,248.8),box(-40,0,242,-30,9,248.8))
upper_cut=diff(box(-40,0,235,40,40,250),keep_posts);drawer=diff(drawer,upper_cut)
# Reuse the existing hat profile itself, mirror it to the cap side, and leave
# its top open for cork pickup. This is not a substitute new cone profile.
hat=tm.boolean.intersection([original['drawer'],cyl(34.6,235.,249.8)],engine='manifold')
hat.apply_transform(T([0,0,259.8])@R(np.pi,[0,1,0]));hat=tm.boolean.intersection([hat,box(-35,-35,9.9,35,0,24.9)],engine='manifold');drawer=union(drawer,hat)
pieces=drawer.split();tiny=[v for v in pieces if abs(v.volume)<1e-6];assert sum(abs(v.volume) for v in tiny)<1e-5;drawer=max(pieces,key=lambda v:abs(v.volume));p['drawer']=drawer
# Receiving D-shaped socket in the outer body's innermost base. The original
# 3mm end wall stays intact. The flat socket roof is0.2mm above the boat rim.
disk=Point(0,0).buffer(34.6,quad_segs=48);boat=disk.intersection(rect(-35,-35,35,0))
posts=disk.intersection(rect(30,0,35,9)).union(disk.intersection(rect(-35,0,-30,9)))
plan=Polygon([(32.5,-9),(34.3,-9),(36.8,-6),(36.8,6),(34.3,9),(32.5,9)]).buffer(-.6,join_style=1).buffer(.6,join_style=1)
pocket=boat.union(posts).union(plan).union(scale(plan,xfact=-1,origin=(0,0)))
receiver=diff(cyl(35.3,3.,7.3),extr(pocket.buffer(.2),2.9,7.6),extr(pocket.buffer(.35),6.5,7.6));p['shell_lower']=union(p['shell_lower'],receiver)
from thin_housing import thin
thinning=thin(p,O);json.dump(thinning,open(O/'qc/housing_thinning.json','w'),indent=2)
print('SOLIDS',[(n,m.is_volume,len(m.split())) for n,m in p.items()],flush=True)
assert all(m.is_volume and len(m.split())==1 for m in p.values())
pickle.dump({n:m.copy(include_cache=False) for n,m in p.items()},open(O/'parts_nominal.pkl','wb'))
params=json.load(open(O/'AS/keyring_parameters.json'));params={k:v for k,v in params.items() if not k.startswith(('rear_','front_')) and k!='roof_z_mm'};params.update(rear_cavity_transition_z_mm=None,rear_constant_bore_diameter_mm=65.,rear_constant_bore_start_z_mm=231.,rear_flat_wall_z_mm=244.,rear_feather_rim_z_mm=238.,rear_axial_clearance_mm=6.,rear_end_wall_thickness_mm=5.8,front_hat_start_z_mm=10.,front_hat_end_z_mm=24.8,front_hat_source='AS/reference_R18_parts.pkl rear235..249.8, mirrored at259.8, upper half removed',stack_translation_from_R20_mm=3.,rear_shape='Open semicircular boat ending; original two side stop posts only',outer_rear_socket_body_z_range_mm=[3.,7.3],socket_radial_and_rim_gap_mm=.2,socket_entry_gap_mm=.35,socket_tight_body_z_range_mm=[3.,6.5],housing_max_outer_inset_mm=1.2,socket_axial_floor_gap_mm=.2)
json.dump(params,open(O/'AS/keyring_parameters.json','w'),indent=2)
pickle.dump({'front_hat':hat.copy(include_cache=False),'rear_receiver':receiver.copy(include_cache=False)},open(O/'AS/changed_features.pkl','wb'))
print([(n,len(m.faces)) for n,m in p.items()],flush=True)
