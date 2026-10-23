from pathlib import Path
import pickle,json,sys
import numpy as np
from shapely.geometry import Polygon
p=Path(__file__).resolve().parent.parent;root=p.parent.parent
new=pickle.load(open(p/'assembled_shell.pkl','rb'))['shell'];old=pickle.load(open(root/'작업완료/shuttle6-wave-R13/assembled_shell.pkl','rb'))['shell']
def outside(m,z):
 sec=m.section(plane_origin=[0,0,z],plane_normal=[0,0,1]);return max([Polygon(q[:,:2]) for q in sec.discrete if len(q)>3],key=lambda q:q.area).exterior
records=[]
for z in [30.,210.,230.]:
 a,b=outside(new,z),outside(old,z);d=a.hausdorff_distance(b);assert d<.05,(z,d);records.append({'body_z_mm':z,'outer_outline_hausdorff_mm':d})
(p/'qc/exterior_R15.json').write_text(json.dumps({'ok':True,'reference':'R13 original C silhouette; no new outside reinforcement','plain_section_comparisons':records},ensure_ascii=False,indent=1));print(records)
