"""Package only passed R13 files and genuine previews/reports."""
from pathlib import Path
import json,shutil,hashlib,zipfile
P=Path(__file__).resolve().parent.parent
c=json.load(open(P/'qc/final_checklist_R13.json'));assert c['ok'],c
strict=json.load(open(P/'qc/strict_R13.json'));assert all(v['warnings']==0 for v in strict.values())
shutil.copytree(P/'scripts',P/'AS/source',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
cfg=json.load(open(P/'pipeline_final.json'));out=P/'deliverables_R13';out.mkdir(exist_ok=True)
main=P/cfg['bambu']['combined']['out'];shutil.copy2(main,out/main.name)
for name in ['individual_plates','STL','preview','GIF','drawings','AS']: (out/name).mkdir(exist_ok=True)
for pl in cfg['plates']:
 f=P/pl.replace('.3mf','_bambu.3mf');shutil.copy2(f,out/'individual_plates'/f.name)
for f in (P/'models').glob('*_print.stl'):shutil.copy2(f,out/'STL'/f.name)
for folder in ['preview_R13','preview_rail_R13','preview_cap_R13','preview_joint_R13']:
 for f in (P/folder).glob('*'):
  if f.suffix in ['.png','.gif']:shutil.copy2(f,out/'preview'/(folder+'_'+f.name))
# Every generated GIF, including review/part/plate cycles, is included.
for f in P.rglob('*.gif'):
 if out in f.parents:continue
 shutil.copy2(f,out/'GIF'/('__'.join(f.relative_to(P).parts)))
for f in (P/'drawings').glob('*'):
 if f.suffix in ['.png','.pdf']:shutil.copy2(f,out/'drawings'/f.name)
for rel in ['요구사항_최종정리.md','설계검토_근거.md','dimensions.json','fit_R13.json','cap_snap_linear_R13.json','profile_settings_R13.json','qc/strict_R13.json','qc/final_checklist_R13.json']:
 shutil.copy2(P/rel,out/Path(rel).name)
shutil.copy2(P/'qc/final_R13/REPORT.md',out/'QC_REPORT.md')
for f in (P/'AS').rglob('*'):
 if f.is_file():
  target=out/'AS'/f.relative_to(P/'AS');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
(out/'출력_조립_안내.md').write_text('# R13 출력·조립 안내\n\n01 외관 두 조각: 세워 출력 후 기존45° 키와 접착 턱14mm를 맞춰 접착합니다. 접착제가 내부 레일과 홈에 흘러들지 않도록 합니다.\n02 내관: 평평한 바닥으로 대각선 눕힘. 벽·바닥2.6mm, 공칭 수납64mm 유지. 바닥 양옆 곡면과 돌기 아래는 트리서포트 대상입니다.\n03 뚜껑: 앞면을 바닥으로 별도 출력. 반원4mm 포켓과30mm 사각 스냅 결합을 유지했습니다.\n04·05 시험편: 새 평면 레일과 돌기 한 쌍의 국부 끼움 확인용. 여섯 쌍 전체 저항은 본품으로 확인해야 합니다.\n06 콘끝 시험편: 기존45→30° 곡면과4mm 끝 부분.\n\n내관 바닥의 평평한 면을 외관 아래 평면에 맞춥니다. 약0.3mm 슬라이드 여유, 홈에 안착한 표면 여유0.2mm, 돌기가 넘어갈 때 반경 간섭0.15mm는 서로 다른 값입니다. 공차0으로 전체 면을 비비는 설계가 아닙니다. 양옆6행36mm 간격으로0/36/72/108/144/180mm 위치에서 안착합니다. 처음과 끝의 저항은 다를 수 있습니다.\n\n바닥 레일이 연속 회전을 제한하지만 내관 윗면이 열려 있으므로180° 뒤집어 재삽입하는 것은 배제하지 못합니다. 위아래를 맞춰 넣으세요. 몸통 접착 소켓 뒤에는4mm 안내 경사가 있고 국부적으로 평면 안내가 비워집니다.\n\n얇은 절개 혀를 추가하지 않고 낮고 넓은 솔리드 돌기를 기존 벽으로 받칩니다. 물리적인 인출력·소리·마모·반복 수명은 출력 전입니다. 렌더의 압축 표시는 간섭 확인용 운동학 모형이며 재료 해석이 아닙니다.\n\nP1S0.4·PLA·0.2층·벽4·15%gyroid·브림10·EFC0.15 선반영·느린 외벽 설정이 포함됩니다. 실제 Bambu Studio GUI·G-code·실물 출력 검증은 하지 않았습니다. 일반3MF와 Bambu 형상 검사용 사본은 strict0이며 Bambu 원본 전용 메타데이터는 별도 구조 검사를 거쳤습니다.\n')
manifest={f.relative_to(out).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.suffix!='.zip' and f.name!='SHA256.json'}
(out/'SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=1))
archive=out/'Shuttle6_C_R13_ID64_평면레일_6단딸깍_출력자료.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(out.rglob('*')):
  if f.is_file() and f!=archive:z.write(f,f.relative_to(out))
assert zipfile.ZipFile(archive).testzip() is None
print(json.dumps({'3mf':str(out/main.name),'zip':str(archive),'checklist':c['line']},ensure_ascii=False,indent=1))
