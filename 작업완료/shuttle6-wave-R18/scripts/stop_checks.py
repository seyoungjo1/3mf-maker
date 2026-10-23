"""Measured contact lands and assembly clearances; not a strength certification."""
from pathlib import Path
import json,pickle,sys,numpy as np,trimesh as tm
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
O=Path(__file__).resolve().parent.parent;ROOT=O.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from pipeline import inter
p=pickle.load(open(O/'parts_nominal.pkl','rb'))
closed=T([0,0,253.])@R(np.pi,[0,1,0])
q=p['drawer'].copy();q.apply_transform(T([0,0,225.1])@closed)
areas={n:inter(q,p[n])/.1 for n in ['stop_left','stop_right']}
up=p['shell_upper'].copy();up.apply_translation([0,0,121.5])
joint=inter(p['shell_lower'],up)
assert joint<.01,joint
gaps={}
q=p['drawer'].copy();q.apply_transform(T([0,0,225.])@closed)
for name,sign in [('stop_left',-1),('stop_right',1)]:
 pts=np.array([[sign*34.8,y,z] for y in np.linspace(-4,4,11) for z in np.linspace(236.3,239.7,11)])
 _,d,_=tm.proximity.closest_point(q,pts)
 gaps[name]={'sample_count':len(pts),'scope':'Inner flat stem face to plain rear cup, excluding the axial stop face.',
             'minimum_mm':float(d.min()),'p1_mm':float(np.percentile(d,1)),'p5_mm':float(np.percentile(d,5))}
 assert d.min()>.18,(name,d.min())
report={'contact_area_each_mm2':areas,'contact_area_pair_mm2':sum(areas.values()),
        'R17_reference_pair_mm2':16.801043702289462,
        'area_ratio_to_R17':sum(areas.values())/16.801043702289462,
        'hypothetical_static_pull_N':30,
        'balanced_mean_pressure_MPa':30/sum(areas.values()),
        'one_side_only_mean_pressure_MPa':30/min(areas.values()),
        'body_joint_overlap_mm3':joint,'plain_cup_sample_gaps':gaps,
        'scope':'Contact area inferred from0.1mm rigid overtravel volume. Pressure assumes an arbitrary static30N pull. No impact, fatigue, layer adhesion, snap insertion force, failure load or physical life validation.'}
json.dump(report,open(O/'qc/stop_checks.json','w'),ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False),flush=True)
