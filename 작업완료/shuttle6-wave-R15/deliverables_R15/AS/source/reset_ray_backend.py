"""Refresh mesh runtime acceleration; preserve every vertex and triangle byte."""
from pathlib import Path
import pickle,hashlib,trimesh as tm
p=Path(__file__).resolve().parent.parent
assert tm.ray.has_embree
for f in [p/'parts.pkl',p/'parts_nominal.pkl',p/'assembled_shell.pkl']+list((p/'models').glob('*_qc.pkl'))+list((p/'qc').glob('subset_*.pkl')):
 d=pickle.load(open(f,'rb'));out={}
 for n,m in d.items():
  old=hashlib.sha256(m.vertices.tobytes()+m.faces.tobytes()).hexdigest();q=m.copy(include_cache=False)
  assert old==hashlib.sha256(q.vertices.tobytes()+q.faces.tobytes()).hexdigest();out[n]=q
 pickle.dump(out,open(f,'wb'))
print('Embree runtime enabled; geometry arrays identical')
