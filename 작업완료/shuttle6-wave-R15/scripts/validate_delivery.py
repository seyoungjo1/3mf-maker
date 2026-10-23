"""Validate real 3MF exports and recheck documentation against completed geometry reports."""
from pathlib import Path
import json,sys
P=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(P.parent.parent/'tools'))
import mm
cfg=json.load(open(P/'pipeline_final.json'));rep=json.load(open(P/'qc/final_R15/report.json'))
assert not rep['warn'] and rep['stages']['assembly']['warnings']==0
assert len(rep['qc'])==7 and all(v['ok'] for v in rep['bambu'].values())
files=[str(P/cfg['bambu']['combined']['out'])]+[str(P/f.replace('.3mf','_bambu.3mf')) for f in cfg['plates']]
r=mm.run('check3mf',files=files,bambu_geometry=True)
json.dump(r,open(P/'qc/strict_R15.json','w'),ensure_ascii=False,indent=1)
assert all(v['warnings']==0 for v in r.values()),r
c=mm.run('checklist',config=str(P/'pipeline_final.json'),skill_read=True);assert c['ok'],c
json.dump(c,open(P/'qc/final_checklist_R15.json','w'),ensure_ascii=False,indent=1)
json.dump({'ok':True,'validation':'Actual completed geometry/assembly/plate reports plus standard check3mf and checklist tools. Documentation title fixed without changing mesh arrays.','source_report':'qc/final_R15/report.json','checklist':c,'strict_files':len(r)},open(P/'qc/delivery_R15.json','w'),ensure_ascii=False,indent=1)
print(json.dumps({'strict_files':len(r),'checklist':c['line']},ensure_ascii=False))
