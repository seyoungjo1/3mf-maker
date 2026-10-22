"""Restore the exact axial cap mating plane after exterior-only QEM simplification."""
from pathlib import Path
import pickle,sys,json,numpy as np,trimesh as tm
p=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(p/'scripts'));from build import P,box,print_transform
sys.path.insert(0,str(p.parent.parent/'tools'));from efc import pre_expand_first_layer
nom=pickle.load(open(p/'parts_nominal.pkl','rb'));pr=pickle.load(open(p/'parts.pkl','rb'));old=nom['shell_upper']
before=old.bounds.tolist();top=P['BODY_L']-P['BODY_SPLIT_Z']
nom['shell_upper']=tm.boolean.intersection([old,box(-50,-50,-1,50,50,top)],engine='manifold');assert nom['shell_upper'].is_volume
m=nom['shell_upper'].copy();m.apply_transform(print_transform('shell_upper',m));pr['shell_upper']=pre_expand_first_layer(m)
nom['shell_upper'].export(p/'models/shell_upper_nominal.stl');pr['shell_upper'].export(p/'models/shell_upper_print.stl')
pickle.dump(nom,open(p/'parts_nominal.pkl','wb'));pickle.dump(pr,open(p/'parts.pkl','wb'));pickle.dump({'shell_upper':pr['shell_upper']},open(p/'models/shell_upper_qc.pkl','wb'))
up=nom['shell_upper'].copy();up.apply_translation([0,0,P['BODY_SPLIT_Z']]);pickle.dump({'shell':tm.util.concatenate([nom['shell_lower'],up])},open(p/'assembled_shell.pkl','wb'))
d=json.load(open(p/'dimensions.json'));d['print_dimensions_mm']['shell_upper']=(pr['shell_upper'].bounds[1]-pr['shell_upper'].bounds[0]).tolist();json.dump(d,open(p/'dimensions.json','w'),ensure_ascii=False,indent=2)
json.dump({'before_bounds_mm':before,'after_bounds_mm':nom['shell_upper'].bounds.tolist(),'max_axial_trim_mm':before[1][2]-top,'reason':'Eliminate0.000107mm QEM overshoot into the cap contact plane; printed outer pattern and collar dimensions retained.'},open(p/'qc/upper_lip_plane.json','w'),ensure_ascii=False,indent=1)
