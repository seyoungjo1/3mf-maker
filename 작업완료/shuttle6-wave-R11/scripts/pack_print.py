"""Package passed R11 output, actual preview GIFs and measured assembly records."""
from pathlib import Path
import json,shutil,hashlib,zipfile
P=Path(__file__).resolve().parent.parent
c=json.load(open(P/'qc/final_checklist_R11.json'));assert c['ok'],c
strict=json.load(open(P/'qc/strict_R11.json'));assert all(v['warnings']==0 for v in strict.values())
cfg=json.load(open(P/'pipeline_final.json'));out=P/'deliverables_R11';out.mkdir(exist_ok=True)
main=P/cfg['bambu']['combined']['out'];shutil.copy2(main,out/main.name)
for folder in ['individual_plates','STL','preview','GIF']:(out/folder).mkdir(exist_ok=True)
for pl in cfg['plates']:
 f=P/pl.replace('.3mf','_bambu.3mf');shutil.copy2(f,out/'individual_plates'/f.name)
for f in (P/'models').glob('*_print.stl'):shutil.copy2(f,out/'STL'/f.name)
for f in (P/'preview_R11').glob('*'):
 if f.suffix in ['.png','.gif']:shutil.copy2(f,out/'preview'/f.name)
for f in (P/'preview_joint_R11').glob('*'):
 if f.suffix in ['.png','.gif']:shutil.copy2(f,out/'preview'/('joint_'+f.name))
for f in (P/'qc/final_R11').rglob('*.gif'):
 shutil.copy2(f,out/'GIF'/f'{f.parent.name}.gif')
for f in (P/'drawings').glob('*'):
 if f.suffix in ['.png','.pdf']:shutil.copy2(f,out/f.name)
for rel in ['AS/개정_기록.md','AS/render_inspection_R11.png','dimensions.json','fit_R11.json','profile_settings_R11.json','qc/strict_R11.json','qc/final_checklist_R11.json']:
 shutil.copy2(P/rel,out/Path(rel).name)
shutil.copy2(P/'qc/final_R11/REPORT.md',out/'QC_REPORT.md')
(out/'출력_조립_안내.md').write_text(f'''{c['line']}

# 셔틀콕 R11 — 공칭64mm 열린 내관 / 눕힘 출력 / 별도 뚜껑 / 둥근 딸깍

주 파일은 {main.name}입니다. P1S0.4·PLA·0.2층·EFC0.15 선반영·외측브림10·벽4·인필15% 설정을 포함합니다. 실제 Bambu Studio GUI·G-code·실물 출력은 아직 확인하지 않았습니다.

01 몸통 두 조각은 세워 출력하고 접착 턱14mm·한쪽 틈0.15mm·턱 벽2.2mm를 맞춰 붙입니다. 본체 폭78.2mm·내경69.8mm입니다. 45° 위치의 폭8mm 돌출 키를 대응 홈에 맞춰 넣고 어깨턱이 맞닿게 합니다. 키가 접착 중 회전을 제한합니다. 접착제는 외부 턱에만 소량 사용하고 내부 통로에 흘리지 않습니다.

02 긴 내관은 바닥 평면을 베드로 하여 대각선으로 눕혀 출력합니다. 모델에 출력 자세가 반영돼 있습니다. 부품 높이는 약32.69mm, 대각선 외곽은 약222.74×222.74mm로 브림10mm를 포함해 P1S256 베드 안에 들어갑니다. 바닥 접지 평면 폭은 약23mm이며 바닥 두께2.6mm입니다. 바닥 양옆 둥근 전이부와 작은 돌기 아래는 트리서포트 대상입니다. 콘은 위로 열린 방향이며 완전 무서포트 파일은 아닙니다. 서포트가 슬라이드 면에서 튀어나오지 않게 제거하세요.

03 앞 뚜껑은 따로 평평한 앞면을 바닥으로 출력합니다. 내관 앞의 U형 혀를 뚜껑 뒤 소켓에 끝까지 끼웁니다. 끼움 길이6mm·한쪽 틈0.20mm이며, 내부의 짧은 고정턱2개가 뚜껑만 빠지는 것을 막는 구조입니다. 긴 누름 클립은 없습니다. 실제 조립력·유지력은 출력 시험 전입니다.

04·05는 외관/내관 딸깍 시험편입니다. 먼저 두 시험편을 출력해 둥근 돌기와 홈의 당김 느낌을 확인하세요. 내관 바깥 두 돌기는 반경1.6mm, 외관 안쪽 홈은 반경1.85mm입니다. 누름 버튼 없이 밀고 당기는 둥근 디텐트 방식이며, 공칭 약0.4mm의 탄성 통과 겹침이 있습니다. 실제 힘이나 피로 수명은 계산·측정하지 않았습니다. 영상의 돌기 압축은 간섭 확인용 운동학 표현이며 재료 해석이 아닙니다.

06은 콘끝 시험편입니다. 입구45도부터 곡률이 시작돼 끝30도·폭4mm로 이어지는 기존 형상 원리를 유지했습니다. 이번에는 내관을 눕혀 출력하므로 이 각도를 출력 베드 오버행 각도로 읽지 마세요.

수납 공간은 사용자가 지정한 공칭Ø64mm 열린 반원입니다. 내관 아래를 평평하게 하므로 완전한 원형 구멍이 아닙니다. 깃털은 유연하고 윗면이 열려 있으며, 강체 플라스틱Ø68mm 원통처럼 넣을 수 없다고 단정하지 않습니다. 검증용64mm 게이지와 가정6개 적층225mm는 치수 확인용이며 실물 깃털의 압축·복원·브랜드 수납 검증은 아닙니다.

표준 플레이트 원본과 Bambu 원본 좌표를 표준Core로 만든 형상 검사용 사본은 strict 경고0입니다. Bambu 전용 메타데이터를 lib3mf가 원본 strict로 읽지 못하는 오류는 strict_R11.json에 기록했습니다. 원본 프로젝트는 템플릿 구조·설정·형상 왕복 검사를 별도로 통과했습니다.
''')
manifest={f.relative_to(out).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.suffix!='.zip' and f.name!='SHA256.json'}
(out/'SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=1))
archive=out/'Shuttle6_C_R11_ID64_눕힘내관_별도뚜껑_출력자료.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(out.rglob('*')):
  if f.is_file() and f!=archive:z.write(f,f.relative_to(out))
assert zipfile.ZipFile(archive).testzip() is None
print(json.dumps({'3mf':str(out/main.name),'zip':str(archive),'checklist':c['line']},ensure_ascii=False,indent=1))
