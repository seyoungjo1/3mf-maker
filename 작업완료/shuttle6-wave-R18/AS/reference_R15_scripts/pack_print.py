"""Package only passed R15 files and genuine previews/reports."""
from pathlib import Path
import json,shutil,hashlib,zipfile
P=Path(__file__).resolve().parent.parent
c=json.load(open(P/'qc/final_checklist_R15.json'));assert c['ok'],c
strict=json.load(open(P/'qc/strict_R15.json'));assert all(v['warnings']==0 for v in strict.values())
shutil.copytree(P/'scripts',P/'AS/source',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
cfg=json.load(open(P/'pipeline_final.json'));out=P/'deliverables_R15';out.mkdir(exist_ok=True)
main=P/cfg['bambu']['combined']['out'];shutil.copy2(main,out/main.name)
for name in ['individual_plates','STL','preview','GIF','drawings','AS']: (out/name).mkdir(exist_ok=True)
for pl in cfg['plates']:
 f=P/pl.replace('.3mf','_bambu.3mf');shutil.copy2(f,out/'individual_plates'/f.name)
for f in (P/'models').glob('*_print.stl'):shutil.copy2(f,out/'STL'/f.name)
for folder in ['preview_R15','preview_details_R15','preview_rail_R15','preview_cap_R15','preview_joint_R15']:
 for f in (P/folder).glob('*'):
  if f.suffix in ['.png','.gif']:shutil.copy2(f,out/'preview'/(folder+'_'+f.name))
# Every generated GIF, including review/part/plate cycles, is included.
for f in P.rglob('*.gif'):
 if out in f.parents:continue
 shutil.copy2(f,out/'GIF'/('__'.join(f.relative_to(P).parts)))
for f in (P/'drawings').glob('*'):
 if f.suffix in ['.png','.pdf']:shutil.copy2(f,out/'drawings'/f.name)
for rel in ['요구사항_최종정리.md','설계검토_근거.md','dimensions.json','fit_R15.json','cap_snap_linear_R15.json','profile_settings_R15.json','qc/strict_R15.json','qc/final_checklist_R15.json','qc/exterior_R15.json']:
 shutil.copy2(P/rel,out/Path(rel).name)
shutil.copy2(P/'qc/final_R15/REPORT.md',out/'QC_REPORT.md')
for f in (P/'AS').rglob('*'):
 if f.is_file():
  target=out/'AS'/f.relative_to(P/'AS');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
(out/'출력_조립_안내.md').write_text((P/'출력_조립_안내.md').read_text())
manifest={f.relative_to(out).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.suffix!='.zip' and f.name!='SHA256.json'}
(out/'SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=1))
archive=out/'Shuttle6_C_R15_ID64_원형외관_좁은굽_원형뒤컵_강화6단_출력자료.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(out.rglob('*')):
  if f.is_file() and f!=archive:z.write(f,f.relative_to(out))
assert zipfile.ZipFile(archive).testzip() is None
print(json.dumps({'3mf':str(out/main.name),'zip':str(archive),'checklist':c['line']},ensure_ascii=False,indent=1))
