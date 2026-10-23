from pathlib import Path
import sys,pickle,json,numpy as np,trimesh as tm
from shapely.geometry import Polygon,box as rect
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(OUT/'AS/reference_R15_scripts'))
# Import legacy geometry under its own module name to avoid this build.py name.
import importlib.util
spec=importlib.util.spec_from_file_location('legacy_build',OUT/'AS/reference_R15_scripts/build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
P=b.P;box=b.box;extr=b.extr;cyl=b.cyl;union=b.union;diff=b.diff
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
nom=pickle.load(open(OUT/'AS/reference_R15_parts.pkl','rb'));drawer=pickle.load(open(OUT/'AS/integrated_candidate_nominal.pkl','rb'))['drawer']
# Rigid stops belong to the rear cup, opposite the cap. No long spring arms.
bosses=[]
# Wide rigid shoulders, with a rounded load-face root and tapered side roots.
# The2mm working land stays straight; the rounded root extends into solid cup.
profile=Polygon([(32.5,242.),(36.8,242.),(36.8,245.5),(34.6,248.8),(32.5,248.8)])

plan=Polygon([(32.5,-9),(34.3,-9),(36.8,-6),(36.8,6),(34.3,9),(32.5,9)])
plan=plan.buffer(-.6,join_style=1).buffer(.6,join_style=1)
for sign in [-1,1]:
 q=extr(profile,18.);q.apply_transform(np.array([[1,0,0,0],[0,0,1,-9.],[0,1,0,0],[0,0,0,1]],float))
 q=tm.boolean.intersection([q,extr(plan,10.,241.)],engine='manifold')
 if sign==-1:q.apply_transform(np.diag([-1,1,1,1]))
 bosses.append(q)
drawer=union(drawer,*bosses)
# Both bosses stay outside the64mm cavity and fuse to the solid rear cup.
lo=nom['shell_lower'];up=nom['shell_upper'].copy();up.apply_translation([0,0,P['BODY_SPLIT_Z']])
channels=[];collar_cuts=[]
for sign in [-1,1]:
 # Follow the shoulder envelope instead of cutting a wide rectangular slot.
 # This preserves the shell wall beside the wide root.
 q=extr(plan.buffer(.3),241.,3.)
 if sign==-1:q.apply_transform(np.diag([-1,1,1,1]))
 channels.append(q)
 xa,xb=sorted([sign*34.4,sign*37.3]);collar_cuts.append(box(xa,-3.3,108.,xb,3.3,143.6))
 # Only the protruding male collar needs the wider open pass slot.
 xa,xb=sorted([sign*33.1,sign*37.3]);collar_cuts.append(box(xa,-9.3,121.5,xb,9.3,143.6))
lo=diff(lo,*channels,*collar_cuts);up=diff(up,*channels)
# Side snap-in blocks carry axial draw force through solid pocket walls.
xy,_,_=b.double_curve(256);outer=Polygon(xy);inner=outer.buffer(-1.8)
keys={};pockets=[];seats=[]
for sign,name in [(-1,'stop_left'),(1,'stop_right')]:
 xa,xb=sorted([sign*34.8,sign*45.]);ha,hb=sorted([sign*34.8,sign*45.])
 head_section=outer.difference(inner).intersection(rect(ha,-10.5,hb,10.5))
 stem=tm.boolean.intersection([box(xa,-9.2,236,xb,9.2,240),extr(outer,4.,236.)],engine='manifold')
 key=union(stem,extr(head_section,5.,235.5))
 for y in [-9.2,9.2]:
  nub=tm.creation.icosphere(subdivisions=2,radius=.5);nub.apply_translation([sign*35.4,y,238.]);key=union(key,nub)
  seat=tm.creation.icosphere(subdivisions=2,radius=.65);seat.apply_translation([sign*35.4,y,238.]);seats.append(seat)
 keys[name]=key
 xa,xb=sorted([sign*34.6,sign*45.]);pockets.append(box(xa,-9.4,235.8,xb,9.4,240.2))
 recess=outer.difference(outer.buffer(-2.0)).intersection(rect(ha,-10.7,hb,10.7))
 pockets.append(extr(recess,5.4,235.3))
lo=diff(lo,*pockets,*seats);up=diff(up,*pockets,*seats)
# Reversed latch: pivot on cap; hooks point back toward the body.
latch=pickle.load(open(OUT/'AS/reference_R16_latch.pkl','rb'))['latch'];reverse=T([0,0,468.7])@R(np.pi,[0,1,0]);latch.apply_transform(reverse);latch.apply_translation([0,1.5,0])
closed=T([0,0,253.])@R(np.pi,[0,1,0]);cap=nom['cap'].copy();cap.apply_transform(closed)
# Two ears surround each ring. Same fixed6x3.2x6.8 sleeve bypasses moving ring.
lug_poly=Polygon([(32.,243.),(32.,253.),(47.5,253.),(51.,246.7),(41.5,241.5),(41.5,243.)])
for xa in [-26.4,-15.6,11.6,22.4]:
 q=extr(lug_poly,4.);q.apply_transform(np.array([[0,0,1,xa],[1,0,0,0],[0,1,0,0],[0,0,0,1]],float))
 hole=cyl(1.7,6.);hole.apply_transform(R(np.pi/2,[0,1,0]));hole.apply_translation([xa-1,45.5,247.]);cap=union(cap,diff(q,hole))
# Broad buttresses connect the body catches to the shell; no tall isolated ears.
receiver=Polygon([(33.,225.7),(45.3,225.7),(45.3,223.),(43.8,223.),(39.5,215.7),(33.,215.7)])
forward=Polygon([(33.,225.7),(45.3,225.7),(35.5,243.),(33.,243.)])
receiver=receiver.union(forward)
from shapely.affinity import translate
receiver=translate(receiver,xoff=1.5)
for xa in [-25.5,22.5]:
 q=extr(receiver,3.);q.apply_transform(np.array([[0,0,1,xa],[1,0,0,0],[0,1,0,0],[0,0,0,1]],float));up=union(up,q)
cap.apply_transform(np.linalg.inv(closed));up.apply_translation([0,0,-P['BODY_SPLIT_Z']])
p={'shell_lower':lo,'shell_upper':up,'drawer':drawer,'cap':cap,'latch':latch,**keys,'shell_coupon':nom['shell_coupon'],'drawer_coupon':nom['drawer_coupon']}
for n,m in p.items():assert m.is_volume and len(m.split())==1,(n,m.is_volume,len(m.split()))
pickle.dump({n:m.copy(include_cache=False) for n,m in p.items()},open(OUT/'parts_nominal.pkl','wb'));print([(n,len(m.faces)) for n,m in p.items()],flush=True)
