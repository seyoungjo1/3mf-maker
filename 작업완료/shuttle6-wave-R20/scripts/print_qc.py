import os
from pathlib import Path
import sys,pickle,json,numpy as np,trimesh as tm,manifold3d as mf
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(OUT/'AS/reference_R15_scripts'))
import importlib.util
sp=importlib.util.spec_from_file_location("reference_print",OUT/"AS/reference_R15_scripts/build.py");ref=importlib.util.module_from_spec(sp);sp.loader.exec_module(ref);print_transform=ref.print_transform
from efc import pre_expand_first_layer
from qc_model import qc_part
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
p=pickle.load(open(OUT/'parts_nominal.pkl','rb'));printed={};qc=[];trans={}
selective=os.environ.get('R20_PARTS','')
if selective:
 oldparts=pickle.load(open(OUT/'parts_print.pkl','rb'));oldqc={r['name']:r for r in json.load(open(OUT/'qc/printed_parts.json'))};oldtrans=json.load(open(OUT/'print_transforms.json'))
for n,m in p.items():
 if selective and n not in selective.split(','):
  printed[n]=oldparts[n];qc.append(oldqc[n]);trans[n]=oldtrans[n];continue
 if n=='drawer':
  a=mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices,np.float32),tri_verts=np.asarray(m.faces,np.uint32))).simplify(.015).to_mesh();m=tm.Trimesh(np.asarray(a.vert_properties)[:,:3],np.asarray(a.tri_verts),process=False);p[n]=m
 if n=='latch':
  old=np.array([[1,0,0,142.100006],[0,0,1,-173.9],[0,-1,0,49.],[0,0,0,1]],float);F=T([0,1.5,468.7])@R(np.pi,[0,1,0]);M=old@np.linalg.inv(F)
 elif n.startswith('stop_'):
  M=R((-1 if n=='stop_right' else 1)*np.pi/2,[0,1,0]);tmp=m.copy();tmp.apply_transform(M);M[2,3]-=tmp.bounds[0,2]
 else:M=print_transform(n,m)
 q=m.copy();q.apply_transform(M);q=pre_expand_first_layer(q)
 if len(q.faces)>190000:
  a=mf.Manifold(mf.Mesh(vert_properties=np.asarray(q.vertices,np.float32),tri_verts=np.asarray(q.faces,np.uint32))).simplify(.01).to_mesh();q=tm.Trimesh(np.asarray(a.vert_properties)[:,:3],np.asarray(a.tri_verts),process=False)
 assert q.is_volume and len(q.split())==1,(n,q.is_volume,len(q.split()))
 printed[n]=q.copy(include_cache=False);trans[n]=M.tolist();q.export(OUT/'models'/f'{n}_print.stl')
 print('QC',n,len(q.faces),flush=True)
 r=qc_part(n,q.copy(include_cache=False),SimpleNamespace(layer=.2,min_wall=1.2,max_bridge=5.,efc=.15,max_tri=200000,single_wall=[]));qc.append(r);json.dump(qc,open(OUT/'qc/printed_parts.json','w'),ensure_ascii=False,indent=2);print(n,r['flags'],flush=True)
 pickle.dump(printed,open(OUT/'parts_print.pkl','wb'))
json.dump(qc,open(OUT/'qc/printed_parts.json','w'),ensure_ascii=False,indent=2)
pickle.dump(printed,open(OUT/'parts_print.pkl','wb'))
assert sum(len(q.faces) for q in printed.values())<=500000
pickle.dump({n:m.copy(include_cache=False) for n,m in p.items()},open(OUT/'parts_nominal.pkl','wb'));json.dump(trans,open(OUT/'print_transforms.json','w'),indent=2)
