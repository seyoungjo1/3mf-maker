"""Package only the final passed split-body revision, with no previous geometry."""
from pathlib import Path
import json,shutil,hashlib,zipfile
P=Path(__file__).resolve().parent.parent
c=json.load(open(P/'qc/final_checklist_R9.json'));assert c['ok'],c
strict=json.load(open(P/'qc/strict_R9.json'));assert all(v['warnings']==0 for v in strict.values())
cfg=json.load(open(P/'pipeline_final.json'))
out=P/'deliverables_R9';out.mkdir(exist_ok=True)
main=P/cfg['bambu']['combined']['out'];shutil.copy2(main,out/main.name)
for folder in ['individual_plates','STL','preview']:(out/folder).mkdir(exist_ok=True)
for pl in cfg['plates']:
 f=P/pl.replace('.3mf','_bambu.3mf');shutil.copy2(f,out/'individual_plates'/f.name)
for f in (P/'models').glob('*_print.stl'):shutil.copy2(f,out/'STL'/f.name)
for f in (P/'preview_R9').glob('*'):
 if f.suffix in ['.png','.gif']:shutil.copy2(f,out/'preview'/f.name)
for f in (P/'preview_cone_R9').glob('*'):
 if f.suffix in ['.png','.gif']:shutil.copy2(f,out/'preview'/('cone_'+f.name))
for f in [P/'drawings/Shuttle6_C_도면_R9.pdf',P/'drawings/03_tip_detail_R9.png',P/'drawings/04_full_curve_R9.png',P/'dimensions.json',P/'fit_R9.json',P/'profile_settings_R9.json',P/'qc/strict_R9.json',P/'qc/final_checklist_R9.json']:
 shutil.copy2(f,out/f.name)
shutil.copy2(P/'qc/final_R9/REPORT.md',out/'QC_REPORT.md')
test=P/'AS/tool_selftest_R9_original.json';assert json.load(open(test))['ok'];shutil.copy2(test,out/'tool_selftest.json')
guide=f'''{c['line']}

{c['legend']}

# 셔틀콕 C안 R9 — 몸통만 두 조각 접착

주 파일: {main.name}. Bambu Studio에서 프로젝트로 엽니다. 기존 R8 파일을 덮어쓰지 않는 새 수정본입니다.

01 플레이트에 몸통 바닥쪽(접착 턱 포함, 높이131.5mm)과 몸통 입구쪽(높이121.5mm)이 함께 있습니다. 둘을 출력해 붙입니다. 턱은10mm 겹치며 반경 틈0.30mm입니다. 접착제는 턱 바깥쪽에 소량만 바르고 내부 슬라이드 면으로 흘리지 마세요. 둥근 사각형의 면과 문양 방향을 맞춰 끝까지 넣은 뒤 접착제를 경화시킵니다.

02 갈색 받침과 뚜껑은 분할하지 않은 일체형입니다. 큰 뚜껑을 바닥에 놓고 세웁니다. 출력 높이는249.8mm이며 닫힌 제품은86×86×253mm입니다. 03·04는 잠금부 시험편이고05는9.8mm높이의 콘끝 시험편입니다. 먼저 출력해 끼움·누름 해제·걸림과30도 곡면·4mm 브리지의 출력 상태를 확인하세요.

본체 모서리R30·옆면R100, 뚜껑R32·R102와 겹반원 문양을 유지했습니다. 받침 외경75.4 / 본체 내경76, 측정 반경 틈0.30mm. 콘은 입구45도(베드 기준)에서 시작하자마자 곡률이 생겨 끝30도까지 연속으로 완만해집니다. 직선 구간은 없습니다. 폭4.000mm에서 곡면을 끝내고 브리지로 닫습니다. 콘 바깥 빈 공간을 채우고 내부 인필15%를 유지합니다. 천장 두께는1.25mm입니다. 닫힌 길이253mm·받침 출력높이249.8mm를 유지합니다.

수납 검사는 깃털지름68·코르크지름28·총길이85·적층피치28로 만든 가정 외피6개(전체225mm)와 그 바깥1.5mm 여유 외피로 했습니다. 앞 뚜껑에 의도적으로 얹히는 면만 여유 외피를 잘랐습니다. 이 결과는 특정 브랜드 실측이나 모든 셔틀콕 수납 보장이 아닙니다. 실제 셔틀콕과 실물 출력은 확인 전입니다.

P1S0.4 / PLA / 0.2층 / 첫층0.2 / EFC0.15 선반영 / 벽4 / 상하5 / gyroid15% / 외측 브림10mm. 외벽40·내벽60·인필80·윗면30·브리지20·이동120mm/s. 기본 가속도1500·외벽600·내벽1000mm/s². 이 값은 전역 저속 설정이며 높이별 감속 modifier는 넣지 않았습니다. 실제 템플릿의 자료형과 적용 값은 profile_settings_R9.json에 기록했습니다.

서포트: 원뿔 끝과 지붕형 잠금창은 짧은 브리지로 설계했고 bridge_no_support=1입니다. enable_support=1·tree(auto)·작은 오버행 제거 해제 설정은 걸쇠의 수평 걸림턱z30과 슬롯 닫힘 끝z45.5 아래 작은 서포트를 만들기 위한 것입니다. 수정 콘은 층별 검사상 최대 브리지4.4mm이며, 받침 전체 한쪽 돌출 합계19.5mm² 중 약4.5mm²가 콘의 작은 국부 돌출입니다. 완전 무서포트 성공은 보장하지 않습니다. 슬라이싱 미리보기에서 걸쇠 밑과 사면의 지지 배치를 확인하세요. 05시험편은 끝9.8mm만 검사하며 입구부터 전체 사면을 시험하지는 않습니다. 지지 흔적은 슬라이드 면에서 제거합니다. 실제 Bambu Studio GUI·G-code·출력시간은 이 환경에서 확인하지 않았습니다.

스프링은30.5×3×8mm·누름1.5mm이며 뿌리 아래3.5mm를 남겼습니다. 선형 보 근사에서 뿌리 유연계수Q1~1.5에 따라 팁 힘6.3~9.4N, 삽입4.8~7.2N, 공칭 뿌리 응력16.0~23.9MPa입니다. 모멘트는 뿌리 굽힘모멘트이며 비틀어 여는 토크나 정격 파손 강도가 아닙니다. 응력 집중·적층 접착·접착제 강도·반복 내구는 실물 시험 전입니다. 걸쇠를 누르고 직선으로 당겨 엽니다.

일반 플레이트 원본은 lib3mf strict 경고0·베드·충돌 검사를 통과했습니다. 전달 Bambu 프로젝트 원본은 템플릿 구조·설정·메시 왕복 검사, 원본 좌표로 만든 표준 3MF Core 검사용 사본은 strict 경고0입니다. Bambu 원본의 전용 메타데이터를 lib3mf strict가 직접 읽지 못하는 오류는 strict_R9.json에 별도로 남겼습니다. 전달 원본을 고쳐서 통과시킨 결과가 아닙니다.

표준 도구 전체 selftest는 PASS입니다. Skill 도구에 해당 로컬 스킬이 등록되지 않아 문서를 직접 읽어 적용했으며, 자동 체크리스트의 첫 두 항목은 세션 확인 항목으로 ? 표시가 남습니다.
'''
(out/'출력_접착_안내.md').write_text(guide)
manifest={f.relative_to(out).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.suffix!='.zip' and f.name!='SHA256.json'}
(out/'SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=1))
archive=out/'Shuttle6_C_R9_몸통접착_출력자료.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(out.rglob('*')):
  if f.is_file() and f!=archive:z.write(f,f.relative_to(out))
assert zipfile.ZipFile(archive).testzip() is None
print(json.dumps({'3mf':str(out/main.name),'zip':str(archive),'checklist':c['line']},ensure_ascii=False,indent=1))
