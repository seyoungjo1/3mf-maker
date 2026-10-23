from pathlib import Path
import sys,pickle,json,numpy as np,trimesh as tm
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(OUT/'AS/reference_R15_scripts'))
from pipeline import inter
from trimesh.transformations import rotation_matrix as R,translation_matrix as T
p=pickle.load(open(OUT/'parts_nominal.pkl','rb'));up=p['shell_upper'].copy();up.apply_translation([0,0,121.5]);shell=tm.util.concatenate([p['shell_lower'],up]);closed=T([0,0,253])@R(np.pi,[0,1,0]);cap=p['cap'].copy();cap.apply_transform(closed)
keys={n:p[n] for n in ['stop_left','stop_right']};static=tm.util.concatenate([shell,*keys.values()]);pivot=np.array([0,45.5,247.]);checks={'slide':[],'latch_sweep':[],'locked_pull':[],'key_insertion':[],'key_final_body_overlap':{n:inter(shell,k) for n,k in keys.items()}}
for distance in [0,36,72,108,144,180,200,215,220,224,225,225.1,225.5,226]:
 q=p['drawer'].copy();q.apply_transform(T([0,0,distance])@closed);checks['slide'].append({'travel_mm':distance,'body_overlap_mm3':inter(shell,q),'stop_key_overlap_mm3':sum(inter(k,q) for k in keys.values())})
for deg in [0,2,4,6,10,15,30,45,60,75,90]:
 q=p['latch'].copy();q.apply_transform(T(pivot)@R(np.deg2rad(deg),[1,0,0])@T(-pivot));checks['latch_sweep'].append({'deg':deg,'body_overlap_mm3':inter(shell,q),'cap_overlap_mm3':inter(cap,q)})
for d in [0,.2,.3,.4,.8,1.,2.]:
 q=p['latch'].copy();q.apply_translation([0,0,d]);checks['locked_pull'].append({'travel_mm':d,'body_overlap_mm3':inter(shell,q)})
for name,s in [('stop_left',-1),('stop_right',1)]:
 for offset in [0,.25,.5,1.,2.,4.,6.]:
  q=keys[name].copy();q.apply_translation([s*offset,0,0]);checks['key_insertion'].append({'key':name,'outward_offset_mm':offset,'rigid_interference_mm3':inter(shell,q)})
# The original six rigid dimensional envelopes are reused without importing
# assembly.py under its own conflicting module name.
import importlib.util
sp=importlib.util.spec_from_file_location('legacy_assembly',OUT/'AS/reference_R15_scripts/assembly.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);gauge=a.envelope();checks['gauge_overlap_mm3']=inter(p['drawer'],gauge)
pickle.dump({'contents':gauge.copy(include_cache=False)},open(OUT/'contents.pkl','wb'))
json.dump(checks,open(OUT/'qc/assembly.json','w'),indent=2);print(json.dumps(checks),flush=True)
