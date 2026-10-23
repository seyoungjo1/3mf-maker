from pathlib import Path
import sys,pickle,json
import numpy as np,trimesh as tm
from shapely.geometry import Polygon
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(OUT/'AS/reference_R15_scripts'));sys.path.insert(0,str(ROOT/'tools'))
from build import P,box,cyl,extr,union,diff
from pipeline import inter
from trimesh.transformations import rotation_matrix as R,translation_matrix as T
p=pickle.load(open(OUT/'stop_parts_nominal.pkl','rb'))
clip=pickle.load(open(OUT/'latch_closed_reference.pkl','rb'))['latch'];pivot=np.array([0,44.,221.7])
# Original clip outline is the reference; pivot rings enlarged for6mm fixed spacers.
for xa in [-22.100006,15.899994]:
 ring=cyl(5.,6.2);ring.apply_transform(R(np.pi/2,[0,1,0]));ring.apply_translation([xa,44.,221.7]);clip=union(clip,ring)
 hole=cyl(3.2,6.4);hole.apply_transform(R(np.pi/2,[0,1,0]));hole.apply_translation([xa-.1,44.,221.7]);clip=diff(clip,hole)
# Two positive hooks added at the outer crossbar.
hooks=[box(a,44.5,246.,b,46.8,249.5) for a,b in [(-25.5,-22.5),(22.5,25.5)]]
hooks += [box(a,44.5,247.,b,46.8,249.5) for a,b in [(-25.5,-20.),(20.,25.5)]]
clip=union(clip,*hooks)
# Broad flat outward back face: preserve the inner hook/mating surfaces.
# Ring enlargement otherwise leaves only22.7mm2 contact in flat printing.
from overhang import layer_poly
Mt=np.array([[1,0,0,142.100006],[0,0,1,-173.9],[0,-1,0,46.8],[0,0,0,1]],float)
tmp=clip.copy();tmp.apply_transform(Mt)
foot=layer_poly(tmp,1.)
pad=extr(foot,2.31,-2.2);pad.apply_transform(np.linalg.inv(Mt));clip=union(clip,pad)
for xa in [-22.100006,15.899994]:
 hole=cyl(3.2,6.4);hole.apply_transform(R(np.pi/2,[0,1,0]));hole.apply_translation([xa-.1,44.,221.7]);clip=diff(clip,hole)

# Upper-only relief retains the6.4mm circular bearing envelope and ends with
# a4mm flat bridge, rather than the5.4mm arch bridge measured by print QC.
roof_poly=Polygon([(-3.2,0),(3.2,0),(3.2,1.04),(2,3.2),(-2,3.2),(-3.2,1.04)])
for xa in [-22.100006,15.899994]:
 cut=extr(roof_poly,6.4);cut.apply_transform(np.array([[0,0,1,xa-.1],[0,-1,0,44.],[1,0,0,221.7],[0,0,0,1]],float));clip=diff(clip,cut)
# Matching cap ears sit0.3mm behind the hook faces; contact is above pivot,
# so axial drawer pull acts toward closing, not unlatching.
cap=p['cap'].copy();closed=T([0,0,253.])@R(np.pi,[0,1,0]);cap.apply_transform(closed)
ears=[box(a,33.,243.,b,45.3,245.7) for a,b in [(-25.5,-22.5),(22.5,25.5)]]
cap=union(cap,*ears)
# Two inner pivot lugs, each4mm thick, with measured3.4mm original clip bore.
lugs=[]
poly=Polygon([(34.5,216.2),(49.5,216.2),(49.5,218.5),(41.4,232.8),(41.4,235.),(37.,243.),(34.5,243.)])
for xa in [-26.4,-15.6,11.6,22.4]:
 q=extr(poly,4.);q.apply_transform(np.array([[0,0,1,xa],[1,0,0,0],[0,1,0,0],[0,0,0,1]],float))
 hole=cyl(1.7,6.);hole.apply_transform(R(np.pi/2,[0,1,0]));hole.apply_translation([xa-1,44.,221.7]);q=diff(q,hole);lugs.append(q)
up=p['shell_upper'].copy();up.apply_translation([0,0,P['BODY_SPLIT_Z']]);up=union(up,*lugs)
assert up.is_volume and len(up.split())==1
shell=union(p['shell_lower'],up)
checks={'clip_body_closed_overlap_mm3':inter(shell,clip),'clip_cap_closed_overlap_mm3':inter(cap,clip),'hinge_axis_body':[0,44.,221.7],'clip_bore_diameter_mm':6.4,'ear_bolt_bore_diameter_mm':3.4,'spacer_OD_ID_length_mm':[6.,3.2,6.8],'clip_ring_width_mm':6.2,'clip_side_gap_mm':.3,'clamp_path':'M3 bolt head -> outer ear -> fixed spacer -> inner ear -> nut. Moving clip ring is outside clamp path.','hook_face_gap_mm':.3,'latch_rotation_sweep':[],'locked_cap_pull':[],'open_cap_pull':[]}
for deg in [0,2,4,6,10,15,30,45,60,75,90]:
 q=clip.copy();q.apply_transform(T(pivot)@R(-np.radians(deg),[1,0,0])@T(-pivot))
 checks['latch_rotation_sweep'].append({'deg':deg,'body_overlap_mm3':inter(shell,q),'cap_overlap_mm3':inter(cap,q)})
for dz in [0,.2,.3,.4,.8,1.,2.]:
 q=cap.copy();q.apply_translation([0,0,dz]);checks['locked_cap_pull'].append({'pull_mm':dz,'overlap_mm3':inter(clip,q)})
openclip=clip.copy();openclip.apply_transform(T(pivot)@R(-np.pi/2,[1,0,0])@T(-pivot))
for dz in [0,2,10,30,100,225]:
 q=cap.copy();q.apply_translation([0,0,dz]);checks['open_cap_pull'].append({'pull_mm':dz,'overlap_mm3':inter(openclip,q)})
cap.apply_transform(np.linalg.inv(closed));up.apply_translation([0,0,-P['BODY_SPLIT_Z']]);p['shell_upper']=up;p['cap']=cap;p['latch']=clip
for n,m in p.items():assert m.is_volume and len(m.split())==1,(n,m.is_volume,len(m.split()))
pickle.dump(p,open(OUT/'parts_nominal.pkl','wb'));json.dump(checks,open(OUT/'lock_checks.json','w'),ensure_ascii=False,indent=2);print(json.dumps(checks),flush=True)
