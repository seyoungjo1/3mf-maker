"""새 도면 표준 틀(mm new)과 체크리스트 자동 판정(mm checklist).
어느 대화방·API·Actions 에서 시작하든 같은 폴더 구조·같은 게이트를 쓰게 하는 것이 목적이다.
  작업중/<이름>/README.md          체크리스트 + 설계 치수표(결합 치수는 상대 파트에서 측정) + 출력 조건·서포트 위치
  작업중/<이름>/scripts/build.py   2 모델링: make_parts() 만 고치면 된다. 공칭 pkl → EFC 선반영 pkl → 플레이트 3MF
  작업중/<이름>/scripts/assembly.py 4 조립 검증 정의: 상태·결합 쌍(contact/min_gap/region)·스윕(작동 GIF)
  작업중/<이름>/pipeline.json      mm make 가 build → pipeline → Bambu 프로젝트 3MF → checklist 순서로 돈다
"""
import os, json, re

CHECKLIST = [
    ('skill', 'Skill 호출'),
    ('read', 'SKILL.md+references 전부 읽음'),
    ('inputs', '올라온 파일은 sample/ 복사·단면 실측 그림·스터디 기록'),
    ('dims', '설계 치수표(결합 치수는 상대 파트에서 측정)'),
    ('qc', 'QC'),
    ('assembly', '조립 검증(실제 좌표에 놓은 교집합·간격·스윕)'),
    ('render', '렌더 5뷰+GIF 눈으로 확인'),
    ('efc', 'EFC 선반영·서포트 위치 명시'),
    ('strict', '3MF strict 0'),
    ('report', '보고'),
]

README = '''# {name}

{desc}

## 체크리스트 (작업 시작 전에 적고, 끝나면 `python tools/mm.py checklist 작업중/{name}/pipeline.json` 으로 자동 판정)
`[ ] Skill 호출 [ ] SKILL.md+references 전부 읽음 [ ] 올라온 파일은 sample/ 복사·단면 실측 그림·스터디 기록 [ ] 설계 치수표(결합 치수는 상대 파트에서 측정) [ ] QC [ ] 조립 검증(실제 좌표에 놓은 교집합·간격·스윕) [ ] 렌더 5뷰+GIF 눈으로 확인 [ ] EFC 선반영·서포트 위치 명시 [ ] 3MF strict 0 [ ] 보고`

## 설계 치수표
`scripts/build.py` 의 `P` 와 같게 유지한다. 결합 치수는 '출처'에 상대 파트에서 잰 근거(단면 그림 파일·측정 명령)를 적는다. 바꾸기 전에 사용자에게 묻는다.

| 이름 | 값 (mm) | 의미 | 출처 |
|---|---|---|---|
{rows}

## 출력 조건
- Bambu P1S · PLA · 층 0.2 · 노즐 0.4 · 코끼리발 보정 0.15 → 첫 층 +0.15 선반영(`tools/efc.py`, build.py 가 함)
- 서포트 위치: (오버행이 있으면 pipeline.json `support_zones` 에 파트·높이·면적을 적는다 — 없으면 '없음')

## 실행
```
python tools/mm.py make 작업중/{name}/pipeline.json      # 빌드 → QC → 3MF → 조립 → 렌더/GIF → REPORT.md → Bambu 프로젝트 3MF → 체크리스트
```
'''

BUILD = '''#!/usr/bin/env python3
"""{name} 빌드 — `python tools/mm.py make 작업중/{name}/pipeline.json` 이 이 스크립트를 프로젝트 폴더에서 실행한다.
스킬 순서: 1 설계 규칙 → 2 모델링(이 파일) → 3 QC → 4 조립 검증 → 5 렌더 → 6 3MF → 7 보고 (3~7 은 파이프라인이 한다).
산출: parts_nominal.pkl(공칭 — 조립 검증용), parts.pkl(첫 층 +0.15 선반영 — 출력 QC 용), models/{name}_A.3mf(플레이트)
틀은 '상자 + 경첩 뚜껑' 예시다. make_parts() 와 P 를 새 도면으로 바꾸고 README 치수표를 같이 고친다."""
import os, sys, pickle
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE); ROOT = os.path.dirname(os.path.dirname(PROJ))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import trimesh
from efc import pre_expand_first_layer
from generic3mf import write_generic_3mf

P = {params}     # 설계 치수표 (README.md 와 같게)
COLORS = {{'base': '#37474f', 'lid': '#ffb300'}}

def box(w, d, h, at=(0, 0, 0)):
    b = trimesh.creation.box(extents=[w, d, h]); b.apply_translation([at[0] + w / 2, at[1] + d / 2, at[2] + h / 2]); return b

def make_parts():
    """출력 방향(평평한 큰 면이 z=0) 공칭 파트 {{이름: trimesh}}. 새 도면은 여기만 바꾼다."""
    W, D, H, T, F = P['W'], P['D'], P['H'], P['WALL'], P['FLOOR']
    base = trimesh.boolean.difference([box(W, D, H), box(W - 2 * T, D - 2 * T, H, (T, T, F))], engine='manifold')
    lid = box(W, D, P['LID_T'])
    return {{'base': base, 'lid': lid}}

def plate(parts, gap=10.0):
    """플레이트 배치: x 방향으로 gap 간격, 베드(256×256) 안 원점 10 mm 부터."""
    objs, x = [], 10.0
    for n, m in parts.items():
        c = m.copy(); c.apply_translation([x - c.bounds[0][0], 10.0 - c.bounds[0][1], -c.bounds[0][2]]); x = c.bounds[1][0] + gap
        objs.append({{'name': n, 'parts': [(c, COLORS.get(n, '#37474f'), n)]}})
    return objs

if __name__ == '__main__':
    os.chdir(PROJ); os.makedirs('models', exist_ok=True)
    nominal = make_parts(); pickle.dump(nominal, open('parts_nominal.pkl', 'wb'))
    printed = {{n: pre_expand_first_layer(m) for n, m in nominal.items()}}; pickle.dump(printed, open('parts.pkl', 'wb'))
    write_generic_3mf('models/{name}_A.3mf', plate(printed), '{name}')
    print('build ok', {{n: [round(v, 2) for v in m.extents] for n, m in nominal.items()}})
'''

ASSEMBLY = '''"""{name} 조립 정의 — 파이프라인이 공칭 파트(parts_nominal.pkl)로 define(parts) 를 불러 검사한다.
states: 상태별 파트 4×4 행렬(조립 GIF 로 순환) · pairs: [a, b, {{"contact": True}} | {{"min_gap": 0.3, "region": [[x0,y0,z0],[x1,y1,z1]]}}]
sweeps: 회전 부품 각도 스윕(간섭 0 범위·작동 GIF). need 범위를 못 채우면 ⚠. 결합부 좌표는 상대 파트에서 측정한 값으로 넣는다."""
import numpy as np
from trimesh.transformations import rotation_matrix as R, translation_matrix as T

def define(parts):
    b = parts['base'].bounds; W, D, H = b[1] - b[0]; t = parts['lid'].extents[2]
    closed = T([0, D, H + t]) @ R(np.pi, [1, 0, 0])          # 뒤집어 출력한 뚜껑을 본체 윗면에 얹음(윗면 접촉)
    piv = [0, D, H + t]                                       # 뒤 모서리 경첩축(틀 예시). 축 -x 방향 회전 = 앞쪽이 위로 들림(+x 면 상자 안으로 돈다)
    return {{
        'states': {{'분리': {{'base': np.eye(4), 'lid': T([0, 0, 25]) @ closed}}, '조립-닫힘': {{'base': np.eye(4), 'lid': closed}}}},
        'pairs': [['base', 'lid', {{'contact': True}}]],
        'sweeps': [{{'name': '뚜껑 열기', 'part': 'lid', 'pivot': piv, 'axis': [-1, 0, 0], 'base': closed, 'angles': [0, 30, 60, 90, 120],
                    'against': ['base'], 'need': [0, 120]}}],
        'notes': ['틀 예시 — 실제 도면의 결합부로 바꿀 것'],
    }}
'''

DEFAULT_P = {'W': 40.0, 'D': 30.0, 'H': 15.0, 'WALL': 3.0, 'FLOOR': 3.0, 'LID_T': 2.0}
DEFAULT_MEANING = {'W': '본체 폭', 'D': '본체 깊이', 'H': '본체 높이', 'WALL': '벽 두께(≥1.2)', 'FLOOR': '바닥 두께', 'LID_T': '뚜껑 두께'}


def new_project(root, name, desc=''):
    if not re.fullmatch(r'[\w\-가-힣]+', name): raise ValueError(f'프로젝트 이름은 글자·숫자·_·- 만: {name!r}')
    proj = os.path.join(root, '작업중', name)
    if os.path.exists(proj): raise FileExistsError(f'이미 있음: {proj}')
    for d in ('scripts', 'models', 'figures', 'qc'): os.makedirs(os.path.join(proj, d))
    rows = '\n'.join(f'| {k} | {v} | {DEFAULT_MEANING[k]} | 틀 기본값 |' for k, v in DEFAULT_P.items())
    open(os.path.join(proj, 'README.md'), 'w', encoding='utf-8').write(README.format(name=name, desc=desc or '(설명)', rows=rows))
    open(os.path.join(proj, 'scripts', 'build.py'), 'w', encoding='utf-8').write(BUILD.format(name=name, params=json.dumps(DEFAULT_P)))
    open(os.path.join(proj, 'scripts', 'assembly.py'), 'w', encoding='utf-8').write(ASSEMBLY.format(name=name))
    cfg = {'name': f'{name} — {desc}' if desc else name, 'build': ['scripts/build.py'], 'out': 'qc/current', 'parts_pkl': 'parts.pkl',
           'assembly_parts_pkl': 'parts_nominal.pkl', 'plates': [f'models/{name}_A.3mf'], 'assembly': 'scripts/assembly.py',
           'colors': {'base': '#37474f', 'lid': '#ffb300'}, 'qc': {'efc': 0.15, 'max_bridge': 7, 'min_wall': 1.2, 'single_wall': []},
           'support_zones': [], 'accepted': [], 'min_gap': 0.3, 'frames': 24,
           'bambu': {'enabled': True, 'settings': {}}, 'inputs': []}
    json.dump(cfg, open(os.path.join(proj, 'pipeline.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return {'project': proj, 'files': sorted(os.path.relpath(os.path.join(dp, f), root) for dp, _, fs in os.walk(proj) for f in fs),
            'next': f'python tools/mm.py make 작업중/{name}/pipeline.json'}


def _dims_ok(readme):
    if not os.path.exists(readme): return False, 'README.md 없음'
    t = open(readme, encoding='utf-8').read(); m = re.search(r'## 설계 치수표\n(.*?)(\n## |\Z)', t, re.S)
    if not m: return False, "README 에 '## 설계 치수표' 없음"
    rows = [l for l in m.group(1).splitlines() if l.startswith('|') and not l.startswith('|---') and '이름' not in l]
    if len(rows) < 3: return False, f'치수 행 {len(rows)}개(<3)'
    bad = [r for r in rows if any(c.strip() in ('', 'TODO') for c in r.strip().strip('|').split('|'))]
    return (not bad), f'치수 {len(rows)}행' + (f', 빈칸/TODO {len(bad)}행' if bad else '')


def checklist(cfg_path, skill_read=False):
    """pipeline 결과(report.json 'stages')·산출물·README 로 체크리스트를 판정. skill/read 는 세션(또는 mm_agent)이 보증하는 항목."""
    cfg = json.load(open(cfg_path, encoding='utf-8')); base = os.path.dirname(os.path.abspath(cfg_path)); P = lambda p: os.path.join(base, p)
    root = os.path.dirname(os.path.dirname(base)); out = P(cfg['out']); rp = os.path.join(out, 'report.json')
    rep = json.load(open(rp, encoding='utf-8')) if os.path.exists(rp) else {}; st = rep.get('stages', {}); warn = rep.get('warn', [])
    R = {}
    R['skill'] = (True if skill_read else None, 'mm_agent 가 SKILL.md 를 시스템 프롬프트로 넣음' if skill_read else '세션이 보증(Skill 도구 호출)')
    R['read'] = (True if skill_read else None, 'mm_agent 가 references 전부를 넣음' if skill_read else '세션이 보증(references 전부 Read)')
    ins = cfg.get('inputs', [])
    if not ins: R['inputs'] = ('N/A', '올라온 파일 없음(pipeline.json inputs 비어 있음)')
    else:
        miss = [i['file'] for i in ins if not os.path.exists(os.path.join(root, 'sample', os.path.basename(i['file'])))]
        nosec = [i['file'] for i in ins if not i.get('sections') or not all(os.path.exists(P(s)) for s in i['sections'])]
        nostudy = [i['file'] for i in ins if not i.get('study') or not os.path.exists(os.path.join(root, i['study']))]
        R['inputs'] = (not (miss or nosec or nostudy), f'sample/ 없음 {miss} · 단면 그림 없음 {nosec} · 스터디 없음 {nostudy}' if (miss or nosec or nostudy) else f'{len(ins)}개 모두 sample/·단면·스터디 있음')
    R['dims'] = _dims_ok(P('README.md'))
    qc = st.get('qc', {}); qw = [w for w in warn if any(w.startswith(n + ':') for n in qc)]
    R['qc'] = (bool(qc) and not qw, f'파트 {len(qc)}개, QC 경고 {len(qw)}' if qc else 'QC 기록 없음 — mm make/pipeline 먼저')
    a = st.get('assembly')
    if not cfg.get('assembly'): R['assembly'] = ('N/A', '결합 파트 없음(assembly 미지정)')
    else: R['assembly'] = (bool(a) and a['warnings'] == 0, f"상태 {len(a['states'])}, 결합 쌍 {a['pairs']}, 스윕 {a['sweeps']}, 경고 {a['warnings']}" if a else '조립 기록 없음')
    rend = st.get('renders', {}); miss = []
    for d, kind in rend.items():
        dd = P(d); views = [f for f in os.listdir(dd) if f.startswith('view_') and f.endswith('.png')] if os.path.isdir(dd) else []
        if not os.path.exists(os.path.join(dd, 'turntable.gif')): miss.append(f'{d}/turntable.gif')
        if kind == 'plate' and len(views) < 5: miss.append(f'{d} 뷰 {len(views)}/5')
    need_motion = bool(a and a.get('sweeps'))
    if need_motion and 'motion' not in rend.values(): miss.append('작동 GIF(motion) 없음')
    look = [os.path.relpath(P(os.path.join(d, 'turntable.gif')), root) for d in rend]
    R['render'] = (bool(rend) and not miss, (f'없음: {miss}' if miss else f'GIF {len(rend)}개 생성') + ' — 눈으로 볼 파일: ' + ', '.join(look))
    e = st.get('efc', {}); zones = {z['part'] for z in st.get('support_zones', [])}
    over = [n for n, q in qc.items() if q.get('overhang_mm2', 0) > 0 and n not in zones]
    efc_ok = abs(e.get('qc_efc', 0) - 0.15) < 1e-6 and bool(e.get('nominal_pkl'))
    R['efc'] = (efc_ok and not over, ('EFC 0.15 선반영(공칭 pkl 분리)' if efc_ok else 'EFC 선반영 확인 불가(assembly_parts_pkl 로 공칭/출력 분리 필요)') +
                (f' · 서포트 위치 미기재 파트 {over}' if over else f" · 서포트 위치 {sorted(zones) or '없음(오버행 0)'}"))
    pls = st.get('plates', []); bad = [p['file'] for p in pls if p['strict_warnings'] or p['collisions'] or not p['in_bed']]
    bam = rep.get('bambu', {}); bbad = [k for k, v in bam.items() if not v.get('ok')]
    R['strict'] = (bool(pls) and not bad and not bbad, f'플레이트 {len(pls)}장 strict 0·충돌 0·베드 안' + (f' (문제 {bad})' if bad else '') +
                   (f" · Bambu 프로젝트 {len(bam)}장 구조 검증 {'ok' if not bbad else '실패 ' + str(bbad)}" if bam else ''))
    R['report'] = (os.path.exists(os.path.join(out, 'REPORT.md')) and not warn, f"REPORT.md · 경고 {len(warn)}")
    items = [{'key': k, 'label': lab, 'pass': R[k][0], 'note': R[k][1]} for k, lab in CHECKLIST]
    mark = lambda p: '[x]' if p is True else ('[-]' if p == 'N/A' else ('[?]' if p is None else '[ ]'))
    md = ' '.join(f"{mark(i['pass'])} {i['label']}" for i in items)
    ok = all(i['pass'] in (True, 'N/A') for i in items if i['key'] not in ('skill', 'read'))
    return {'ok': ok, 'line': md, 'items': items, 'legend': '[x] 통과 [ ] 실패 [-] 해당 없음 [?] 세션이 보증'}
