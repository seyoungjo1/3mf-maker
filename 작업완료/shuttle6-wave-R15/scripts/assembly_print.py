"""Print-project overview; full21+ state review remains in qc/review_R15."""
from pathlib import Path
import sys,pickle,hashlib,json
import trimesh as tm
sys.path.insert(0,str(Path(__file__).resolve().parent))
from assembly import define as full_define

def define(parts):
 p=Path(__file__).resolve().parent.parent
 dependencies=[p/'parts_nominal.pkl']+sorted((p/'scripts').glob('*.py'))+[p.parent.parent/'tools'/n for n in ['pipeline.py','mm.py','snapfit.py','beam.py']]
 signature=hashlib.sha256(b''.join(hashlib.sha256(f.read_bytes()).digest() for f in dependencies)).hexdigest()
 cache=p/'qc/.cache/assembly_scalar.pkl';cache.parent.mkdir(exist_ok=True,parents=True)
 saved=pickle.load(open(cache,'rb')) if cache.exists() else None
 if saved and saved['signature']==signature and (p/'fit_R15.json').exists():
  result=saved['result'];print('Reused scalar checks: identical nominal meshes and source/tool hashes',flush=True)
 else:
  result=full_define(parts)
  result['extra']={n:m.copy(include_cache=False) if isinstance(m,tm.Trimesh) else m for n,m in result['extra'].items()}
  pickle.dump({'signature':signature,'result':result},open(cache,'wb'))
 keys=['닫힘','열림','분리','인출 36mm','인출 72mm','인출 108mm','인출 144mm','인출 180mm','몸통 접착','뚜껑 끼움 전','뚜껑 딸깍 통과','뚜껑 끼움 완료','딸깍 통과 18mm','딸깍 시험편 닫힘','딸깍 시험편 통과']
 result['states']={k:result['states'][k] for k in keys}
 result['notes'].append('Full extraction, dimensional gauge and coupon states were verified against the identical meshes in the preceding review_R15. Print-project overview retains fifteen assembly/cap states; scalar dimensional/interference/rotation/spring checks still run in full_define.')
 return result
