#!/usr/bin/env python3
"""3mf-maker API 에이전트 — 어느 대화방·API·GitHub Actions 에서 요청하든 같은 지침과 같은 도구로만 일하게 하는 실행기.

  지침: CLAUDE.md + .claude/skills/3d-print-3mf/SKILL.md + references 전부(studies 포함)를 시스템 프롬프트로 넣는다(프롬프트 캐시).
  도구: 표준 프로그램 tools/mm.py 의 명령 전부(mm_*) + 저장소 안 파일 읽기/쓰기/목록(쓰기는 작업중/·작업완료/·sample/·스킬 references 만).
  게이트: 모델이 끝내려 할 때 프로젝트 체크리스트(mm checklist)를 코드로 판정한다. 통과하지 못하면 끝내지 못하고
          실패 항목을 되돌려 받아 계속 고친다(최대 --gate-retries 번). 최종 출력 맨 앞에 체크리스트 줄을 코드가 붙인다.

사용:
  python tools/mm_agent.py "요청" [--project 이름] [--effort medium] [--max-turns 80]
  python tools/mm_agent.py --serve --port 8766          → POST /agent {"prompt": "...", "project": "이름"}
  파이썬: import mm_agent; mm_agent.run_agent("요청", project="이름")
환경변수 ANTHROPIC_API_KEY 필요. 모델 claude-opus-5-5(사고는 항상 적응형), 스트리밍, 서버 측 거절 대체(fallbacks "default").
"""
import os, sys, json, glob, time, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import mm

MODEL = 'claude-opus-5-5'
BETAS = ['server-side-fallback-2026-07-01']           # fallbacks="default" 짝 헤더
SKILL = os.path.join(ROOT, '.claude', 'skills', '3d-print-3mf')
WRITE_OK = ('작업중/', '작업완료/', 'sample/', '.claude/skills/3d-print-3mf/references/')
NO_TOOL = {'serve'}                                    # 에이전트 안에서 쓰지 않는 명령
MAX_RESULT = 20000                                     # 도구 결과 글자 상한(컨텍스트 보호)


def guidance_files():
    fs = [os.path.join(ROOT, 'CLAUDE.md'), os.path.join(SKILL, 'SKILL.md')]
    fs += sorted(glob.glob(os.path.join(SKILL, 'references', '*.md'))) + sorted(glob.glob(os.path.join(SKILL, 'references', 'studies', '*.md')))
    return [f for f in fs if os.path.exists(f)]


def system_prompt(project=None):
    head = ('너는 3mf-maker 저장소의 3D 프린팅 설계 에이전트다. 사용자는 Bambu Lab P1S·PLA 로 출력한다. 답변은 한국어 존댓말.\n'
            '아래 CLAUDE.md 와 스킬 문서(SKILL.md + references 전부)가 이 저장소의 절대 규칙이다. 이 문서들은 이미 읽힌 상태로 주어졌다.\n'
            '작업은 반드시 도구로만 한다: 새 도면은 mm_new 로 틀을 만들고, scripts/build.py·assembly.py·README 치수표를 write_file 로 고친 뒤 '
            'mm_make 로 빌드→QC→3MF→조립→렌더/GIF→REPORT→Bambu 프로젝트 3MF→체크리스트를 돌린다. ok=false 면 결과를 내지 말고 설계로 돌아간다.\n'
            '결합 치수는 상대 파트를 mm_section·mm_assemble 로 실측해 근거를 README 치수표 출처 칸에 적는다. 결합 치수를 바꾸거나 설계 방향을 고르는 일은 '
            '스스로 정하지 말고 최종 답변에 안(실측 그림 경로 포함)과 질문으로 남긴다.\n'
            '렌더 PNG 를 read_file 로 볼 수는 없으니 REPORT.md 의 수치와 체크리스트로 판단하고, 사용자가 눈으로 볼 GIF·PNG 경로를 보고에 적는다.\n'
            '끝낼 때는 결론 한 줄 → QC 표 → 조립 검증 수치 → 렌더/GIF 경로 → 만든 파일(특히 *_bambu.3mf)과 슬라이서에서 할 일 → 다음 한 걸음 순서로 보고한다.')
    if project:
        pd = project if '/' in project else f'작업중/{project}'
        head += f'\n이번 작업 프로젝트: {pd}/ (config: {pd}/pipeline.json, 없으면 가장 최근 pipeline_*.json)'
    docs = '\n\n'.join(f'===== {os.path.relpath(f, ROOT)} =====\n' + open(f, encoding='utf-8').read() for f in guidance_files())
    return [{'type': 'text', 'text': head}, {'type': 'text', 'text': docs, 'cache_control': {'type': 'ephemeral'}}]


# ---------------------------------------------------------------- 도구
FILE_TOOLS = [
    {'name': 'read_file', 'description': '저장소 안 텍스트 파일 읽기(경로는 저장소 기준). 큰 파일은 offset/limit 줄 단위.',
     'input_schema': {'type': 'object', 'properties': {'path': {'type': 'string'}, 'offset': {'type': 'integer'}, 'limit': {'type': 'integer'}}, 'required': ['path'], 'additionalProperties': False}},
    {'name': 'write_file', 'description': '파일 쓰기(전체 덮어쓰기). 허용 위치: ' + ', '.join(WRITE_OK),
     'input_schema': {'type': 'object', 'properties': {'path': {'type': 'string'}, 'content': {'type': 'string'}}, 'required': ['path', 'content'], 'additionalProperties': False}},
    {'name': 'list_dir', 'description': '저장소 안 폴더 목록(glob 패턴 가능, 예 "작업중/*/pipeline*.json")',
     'input_schema': {'type': 'object', 'properties': {'pattern': {'type': 'string'}}, 'required': ['pattern'], 'additionalProperties': False}},
]


def tools():
    ts = [t for t in mm.schema()['tools'] if t['name'].removeprefix('mm_') not in NO_TOOL] + FILE_TOOLS
    return [{**t, 'eager_input_streaming': True} for t in ts]   # 스트리밍 + 클라이언트 도구 → 입력은 우리가 검증한다


_PY = {'string': str, 'number': (int, float), 'integer': int, 'boolean': bool, 'array': list, 'object': dict}


def validate(schema, args):
    """도구 입력 검증(eager 스트리밍은 서버가 검증하지 않음): dict·필수 키·키 이름·기본 타입. 문제 목록을 돌려준다."""
    if not isinstance(args, dict): return ['입력이 객체가 아님']
    props, errs = schema.get('properties', {}), []
    for k in schema.get('required', []):
        if k not in args: errs.append(f'필수 인자 {k} 없음')
    for k, v in args.items():
        if k not in props: errs.append(f'모르는 인자 {k}'); continue
        t = props[k].get('type')
        if v is None and 'default' in props[k]: continue
        if t in _PY and (not isinstance(v, _PY[t]) or (t in ('number', 'integer') and isinstance(v, bool))): errs.append(f'{k}: {t} 아님')
        elif t == 'array' and props[k].get('items', {}).get('type') in _PY and not all(isinstance(x, _PY[props[k]['items']['type']]) for x in v):
            errs.append(f"{k}: 원소가 {props[k]['items']['type']} 아님")
    return errs


def _safe(path, write=False):
    p = os.path.realpath(os.path.join(ROOT, path)); rel = os.path.relpath(p, ROOT).replace(os.sep, '/')
    if rel.startswith('..') or os.path.isabs(rel): raise PermissionError(f'저장소 밖 경로: {path}')
    if write and not rel.startswith(WRITE_OK): raise PermissionError(f'쓰기 금지 위치: {rel} (허용 {WRITE_OK})')
    return p, rel


def call_tool(name, args):
    if name == 'read_file':
        p, _ = _safe(args['path']); lines = open(p, encoding='utf-8', errors='replace').read().splitlines()
        o = args.get('offset') or 0; n = args.get('limit') or 400
        return {'path': args['path'], 'lines': len(lines), 'text': '\n'.join(f'{i + 1}\t{l}' for i, l in enumerate(lines[o:o + n], o))}
    if name == 'write_file':
        p, rel = _safe(args['path'], write=True); os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w', encoding='utf-8').write(args['content']); return {'written': rel, 'bytes': len(args['content'].encode())}
    if name == 'list_dir':
        pat = args['pattern'].rstrip('/'); pat = pat if any(c in pat for c in '*?[') else pat + '/*'; _safe(pat.split('*')[0] or '.')
        return {'matches': sorted(os.path.relpath(f, ROOT) for f in glob.glob(os.path.join(ROOT, pat)))[:300]}
    cmd = name.removeprefix('mm_')
    if cmd == 'checklist' or cmd == 'make': args = {**args, 'skill_read': True}    # 지침 전부를 시스템 프롬프트로 넣었으므로 에이전트 실행에선 보증된다
    cwd = os.getcwd(); os.chdir(ROOT)
    try: return mm.run(cmd, **args)
    finally: os.chdir(cwd)


def run_tool_block(block, schemas):
    sch = schemas.get(block.name)
    if sch is None: return {'type': 'tool_result', 'tool_use_id': block.id, 'is_error': True, 'content': f'모르는 도구 {block.name}'}
    errs = validate(sch, block.input)
    if errs:   # 잘린/깨진 입력: 실행하지 않고 원문과 함께 돌려줘 다시 보내게 한다
        return {'type': 'tool_result', 'tool_use_id': block.id, 'is_error': True, 'content': json.dumps({'INVALID_INPUT': errs, 'received': json.dumps(block.input, ensure_ascii=False, default=str)}, ensure_ascii=False)}
    try: res = call_tool(block.name, block.input); err = isinstance(res, dict) and 'error' in res and len(res) <= 2
    except Exception as e: res, err = {'error': f'{type(e).__name__}: {e}'}, True
    txt = json.dumps(res, ensure_ascii=False, default=str)
    if len(txt) > MAX_RESULT: txt = txt[:MAX_RESULT] + f'… (잘림, 전체 {len(txt)}자 — 필요한 부분은 read_file 로 REPORT.md 등을 볼 것)'
    return {'type': 'tool_result', 'tool_use_id': block.id, 'content': txt, **({'is_error': True} if err else {})}


# ---------------------------------------------------------------- 게이트
def projects_touched(messages, project):
    ps = {project if '/' in project else '작업중/' + project} if project else set()
    for m in messages:
        if m['role'] != 'assistant': continue
        for b in m['content']:
            if getattr(b, 'type', None) == 'tool_use' and isinstance(b.input, dict):
                if b.name == 'mm_new' and isinstance(b.input.get('name'), str): ps.add('작업중/' + b.input['name'])
                for v in b.input.values():
                    if isinstance(v, str) and v.startswith(('작업중/', '작업완료/')): ps.add('/'.join(v.split('/')[:2]))
    return sorted(p for p in ps if p and _configs(p))


def _configs(p):
    """프로젝트 폴더(작업중/x 또는 작업완료/x)의 게이트 config: pipeline.json, 없으면 가장 최근 pipeline_*.json"""
    d = os.path.join(ROOT, p)
    if os.path.exists(os.path.join(d, 'pipeline.json')): return [os.path.join(d, 'pipeline.json')]
    c = sorted(glob.glob(os.path.join(d, 'pipeline_*.json')), key=os.path.getmtime); return c[-1:]


def gate(projects):
    res = {p: mm.run('checklist', config=_configs(p)[0], skill_read=True) for p in projects}
    return all(r['ok'] for r in res.values()), res


# ---------------------------------------------------------------- 루프
def _stream_once(client, kw, echo):
    with client.beta.messages.stream(**kw) as stream:
        for ev in stream:
            if echo and getattr(ev, 'type', '') == 'text': print(ev.text, end='', flush=True)
        return stream.get_final_message()


def run_agent(prompt, project=None, effort='medium', max_turns=80, gate_retries=3, client=None, echo=True, log_path=None, max_tokens=32000):
    if client is None:
        import anthropic; client = anthropic.Anthropic()
    ts = tools(); schemas = {t['name']: t['input_schema'] for t in ts}
    messages = [{'role': 'user', 'content': prompt}]; sys_p = system_prompt(project)
    kw = dict(model=MODEL, max_tokens=max_tokens, system=sys_p, tools=ts, betas=BETAS, fallbacks='default',
              thinking={'type': 'adaptive'}, output_config={'effort': effort})
    turns = json_retries = gates = 0; final = None; stop = None; t0 = time.time(); gate_res = {}
    while turns < max_turns:
        turns += 1
        try: resp = _stream_once(client, {**kw, 'messages': messages}, echo); json_retries = 0
        except ValueError:                       # SDK 가 파싱 못 한 도구 입력 JSON — tool_use_id 가 없으니 같은 턴을 다시 요청(최대 2번)
            json_retries += 1
            if json_retries > 2: raise
            continue
        stop = resp.stop_reason; messages.append({'role': 'assistant', 'content': resp.content})
        if stop == 'refusal': final = '요청이 거절되어 중단했습니다(stop_reason=refusal). 도구는 실행하지 않았습니다.'; break
        if stop == 'pause_turn': continue
        uses = [b for b in resp.content if b.type == 'tool_use']
        if uses and stop == 'max_tokens':        # 잘린 도구 입력은 실행하지 않는다
            messages.append({'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': b.id, 'is_error': True, 'content': '출력 한도에서 입력이 잘림 — 더 작게 나눠 다시 호출할 것'} for b in uses]}); continue
        if uses:
            messages.append({'role': 'user', 'content': [run_tool_block(b, schemas) for b in uses]}); continue
        text = '\n'.join(b.text for b in resp.content if b.type == 'text')
        projs = projects_touched(messages, project)
        if projs:
            ok, gate_res = gate(projs)
            if not ok and gates < gate_retries:
                gates += 1
                fails = {p: [f"{i['label']}: {i['note']}" for i in r['items'] if i['pass'] not in (True, 'N/A', None)] for p, r in gate_res.items()}
                messages.append({'role': 'user', 'content': '[게이트] 체크리스트가 통과하지 않아 아직 끝낼 수 없습니다. 실패 항목을 고치고 mm_make 를 다시 돌리세요.\n' + json.dumps(fails, ensure_ascii=False, indent=1)})
                continue
        final = text; break
    else:
        final = f'최대 턴 {max_turns} 도달 — 중단했습니다.'
    lines = [f"체크리스트({p}): {r['line']}" for p, r in gate_res.items()]
    passed = all(r['ok'] for r in gate_res.values()) if gate_res else None
    if gate_res and not passed: lines.append('⚠ 체크리스트 미통과 — 이 결과물은 보내지 않습니다.')
    out = {'ok': passed is not False and stop != 'refusal', 'final': '\n'.join(lines + ['', final or '']), 'checklist': gate_res, 'turns': turns,
           'stop_reason': stop, 'seconds': round(time.time() - t0), 'projects': list(gate_res)}
    if log_path:
        os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
        tr = [{'role': m['role'], 'content': m['content'] if isinstance(m['content'], str) else [getattr(b, 'model_dump', lambda: b)() for b in m['content']]} for m in messages]
        json.dump({**out, 'prompt': prompt, 'transcript': tr}, open(log_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
    return out


def serve(port=8766):
    import http.server
    class H(http.server.BaseHTTPRequestHandler):
        def _send(self, code, obj):
            b = json.dumps(obj, ensure_ascii=False, default=str).encode(); self.send_response(code); self.send_header('Content-Type', 'application/json; charset=utf-8'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
        def do_POST(self):
            if self.path != '/agent': return self._send(404, {'error': 'POST /agent {"prompt": "...", "project": "이름", "effort": "medium"}'})
            try:
                body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
                self._send(200, run_agent(body['prompt'], body.get('project'), body.get('effort', 'medium'), echo=False))
            except Exception as e: self._send(500, {'error': f'{type(e).__name__}: {e}'})
        def log_message(self, *a): pass
    print(f'mm agent: http://127.0.0.1:{port}/agent', flush=True); http.server.ThreadingHTTPServer(('127.0.0.1', port), H).serve_forever()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0]); ap.add_argument('prompt', nargs='?'); ap.add_argument('--project')
    ap.add_argument('--effort', default='medium', choices=['low', 'medium', 'high', 'xhigh', 'max']); ap.add_argument('--max-turns', type=int, default=80)
    ap.add_argument('--log'); ap.add_argument('--out-json'); ap.add_argument('--serve', action='store_true'); ap.add_argument('--port', type=int, default=8766)
    a = ap.parse_args()
    if a.serve: return serve(a.port)
    if not a.prompt: ap.error('요청(prompt)이 필요합니다')
    r = run_agent(a.prompt, a.project, a.effort, a.max_turns, log_path=a.log)
    print('\n\n' + r['final'])
    if a.out_json: json.dump(r, open(a.out_json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
    return 0 if r['ok'] else 1


if __name__ == '__main__': sys.exit(main())
