"""Incremental R12 -> R13 build, keeping the verified exterior surface exactly.

Fresh reproduction remains scripts/build.py; this avoids re-meshing ornaments.
"""
from pathlib import Path
import sys, pickle, json, hashlib
import numpy as np
import trimesh as tm
PTH=Path(__file__).resolve().parent.parent
ROOT=PTH.parent.parent
sys.path.insert(0,str(PTH/'scripts'));sys.path.insert(0,str(ROOT/'tools'))
from build import P,make_drawer,print_transform,diff,sphere,cyl,box,extr,double_curve,union
from rail_geometry import finish_shell_pair,finish_shell_coupon
from shapely.geometry import Polygon
from efc import pre_expand_first_layer

base=ROOT/'작업완료/shuttle6-wave-R12'
parts=pickle.load(open(base/'parts_nominal.pkl','rb'))
printed=pickle.load(open(base/'parts.pkl','rb'))
unchanged=['cap','tip_coupon']
preserved={n:hashlib.sha256(parts[n].vertices.tobytes()+parts[n].faces.tobytes()).hexdigest() for n in unchanged}
# Restore a complete bore band around the old mouth pockets, with positive
# overlap into the parent wall. A tangent sphere-only patch left near-zero
# duplicate faces and invalid sliced inner loops despite a watertight mesh.
old_pocket_z=233.-P['BODY_SPLIT_Z']
parts['shell_upper']=diff(union(parts['shell_upper'],cyl(36.,8.,old_pocket_z-4.)),
                          cyl(34.9,8.04,old_pocket_z-4.02))
parts['shell_lower'],parts['shell_upper']=finish_shell_pair(parts['shell_lower'],parts['shell_upper'])
# Delete the old oversized mouth pockets by rebuilding this simple coupon.
coupon=diff(extr(Polygon(double_curve()[0]),36),cyl(P['ID']/2,38,-1),
            *[sphere(P['DETENT_POCKET_R'],[sign*P['DETENT_X'],P['DETENT_Y'],26.]) for sign in [-1,1]])
parts.update(drawer=make_drawer(),drawer_coupon=make_drawer(42.,False,False),shell_coupon=finish_shell_coupon(coupon))
changed=[n for n in parts if n not in unchanged]
for n in changed:
 m=parts[n]
 assert m.is_volume and len(m.split())==1,(n,m.is_volume,len(m.split()))
 m.export(PTH/'models'/f'{n}_nominal.stl')
 q=m.copy();q.apply_transform(print_transform(n,m))
 printed[n]=pre_expand_first_layer(q)
 assert printed[n].is_volume and len(printed[n].split())==1,n
 assert len(printed[n].faces)<=200000,(n,len(printed[n].faces))
 print(n,len(m.faces),'->',len(printed[n].faces),'faces',flush=True)
for n in parts:
 parts[n].export(PTH/'models'/f'{n}_nominal.stl')
 printed[n].export(PTH/'models'/f'{n}_print.stl')
 pickle.dump({n:printed[n]},open(PTH/'models'/f'{n}_qc.pkl','wb'))
assert sum(len(m.faces) for m in printed.values())<=500000
for n in unchanged:
 assert preserved[n]==hashlib.sha256(parts[n].vertices.tobytes()+parts[n].faces.tobytes()).hexdigest()
pickle.dump(parts,open(PTH/'parts_nominal.pkl','wb'))
pickle.dump(printed,open(PTH/'parts.pkl','wb'))
up=parts['shell_upper'].copy();up.apply_translation([0,0,P['BODY_SPLIT_Z']])
pickle.dump({'shell':tm.util.concatenate([parts['shell_lower'],up])},open(PTH/'assembled_shell.pkl','wb'))
d=json.load(open(base/'dimensions.json'))
d['parameters_mm'].update(P)
d['rail']={'flat_y_mm':-32.9,'tray_flat_y_mm':-32.6,'nominal_normal_gap_mm':.3,
 'body_half_socket_relief_mm':3.5,'upper_ramp_length_mm':4.,
 'scope':'Single lower flat in bore. Lower male sleeve carries flat; upper socket retains glue clearance, then a 4mm lead-in resumes guide. No thin tongue cut.'}
d['detent']={'stations':6,'paired_bosses':12,'paired_pockets':12,'pitch_mm':36.,
 'tray_stations_mm':[20.+36*i for i in range(6)],'shell_stations_mm':[233.-36*i for i in range(6)],
 'extraction_stops_mm':[36.*i for i in range(6)],'boss_radius_mm':3.,'pocket_radius_mm':3.2,
 'pocket_surface_gap_mm':.2,'radial_interference_mm':.15,'wall_mm':2.6,
 'scope':'Low broad solid nubs, no slots or thin cantilever tabs. Open trough wall provides compliance. All aligned rows engage together; resistance changes as rows leave. Actual click force and fatigue life require print trials.'}
d['preserved_R12_parts_sha256']=preserved
d['print_transforms']={n:print_transform(n,m).tolist() for n,m in parts.items()}
d['print_dimensions_mm']={n:m.extents.tolist() for n,m in printed.items()}
d['status']='R13 unverified build: internal flat guide + six paired detent rows; physical fit/force/durability untested'
json.dump(d,open(PTH/'dimensions.json','w'),ensure_ascii=False,indent=2)
print('R13 built',sum(len(m.faces) for m in printed.values()),'total faces',flush=True)
