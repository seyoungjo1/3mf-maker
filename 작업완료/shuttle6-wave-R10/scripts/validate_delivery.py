"""Strict-check every delivered Bambu file using the standard mm API."""
from pathlib import Path
import json,sys
P=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(P.parent.parent/'tools'))
import mm
cfg=json.load(open(P/'pipeline_final.json'))
result=json.load(open(P/'qc/final_run_R10.json'))
assert result.get('ok'),result
files=[str(P/cfg['bambu']['combined']['out'])]+[str(P/f.replace('.3mf','_bambu.3mf')) for f in cfg['plates']]
r=mm.run('check3mf',files=files,bambu_geometry=True)
json.dump(r,open(P/'qc/strict_R10.json','w'),ensure_ascii=False,indent=1)
assert all(v['warnings']==0 for v in r.values()),r
c=mm.run('checklist',config=str(P/'pipeline_final.json'))
assert c['ok'],c
json.dump(c,open(P/'qc/final_checklist_R10.json','w'),ensure_ascii=False,indent=1)
print(json.dumps({'strict':r,'checklist':c['line']},ensure_ascii=False,indent=1))
