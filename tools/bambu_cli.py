#!/usr/bin/env python3
"""실제 Bambu Studio(명령줄)로 3MF 를 열고 슬라이스해서 '프로젝트로 열리는지' 검증한다. GitHub Actions(.github/workflows/bambu-verify.yml)에서 돈다.
  python tools/bambu_cli.py --download --files a_bambu.3mf b.3mf --out bambu_out [--summary $GITHUB_STEP_SUMMARY] [--expect-project a_bambu.3mf]
방법(Bambu Studio 위키 Command-Line-Usage): `bambu-studio --slice 0 --debug 2 --export-3mf out.3mf in.3mf` — 설정 파일을 주지 않으면 3MF 안의 설정으로 슬라이스한다.
판정: 종료 코드 0 + 결과 3MF 에 G-code + G-code 머리말 설정이 3MF 의 project_settings 와 일치(printer_model, elefant_foot_compensation, enable_support, filament_colour …).
Bambu Studio 실행 파일: 환경변수 BAMBU_STUDIO, 없으면 --download 로 GitHub 최신 릴리스의 리눅스 AppImage 를 받아 풀어 쓴다(GH_TOKEN 있으면 API 한도 여유)."""
import os, sys, json, re, glob, shutil, subprocess, zipfile, argparse, urllib.request, time
KEYS = ['printer_model', 'nozzle_diameter', 'layer_height', 'elefant_foot_compensation', 'enable_support', 'support_on_build_plate_only', 'support_type', 'filament_colour', 'filament_settings_id', 'curr_bed_type']
def _api(url):
    req = urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json', **({'Authorization': f'Bearer {os.environ["GH_TOKEN"]}'} if os.environ.get('GH_TOKEN') else {})})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())
def download(dest='bambu_app'):
    rel = _api('https://api.github.com/repos/bambulab/BambuStudio/releases/latest'); assets = rel.get('assets', [])
    pick = None
    for pat in [r'ubuntu.*24\.04.*\.AppImage$', r'linux.*24\.04.*\.AppImage$', r'ubuntu.*\.AppImage$', r'linux.*\.AppImage$', r'\.AppImage$']:
        c = [a for a in assets if re.search(pat, a['name'], re.I)]
        if c: pick = c[0]; break
    if not pick: raise SystemExit(f'AppImage 없음: {[a["name"] for a in assets]}')
    os.makedirs(dest, exist_ok=True); app = os.path.join(dest, pick['name'])
    print(f'다운로드 {rel["tag_name"]} {pick["name"]} ({pick["size"] // 1_000_000} MB)', flush=True)
    urllib.request.urlretrieve(pick['browser_download_url'], app); os.chmod(app, 0o755)
    subprocess.run([os.path.abspath(app), '--appimage-extract'], cwd=dest, check=True, stdout=subprocess.DEVNULL)
    return os.path.abspath(os.path.join(dest, 'squashfs-root', 'AppRun')), rel['tag_name'], pick['name']
def gcode_settings(gc):
    out = {}
    for k in KEYS:
        m = re.search(rf'^; {re.escape(k)} = (.*)$', gc, re.M)
        if m: out[k] = m.group(1).strip()
    return out
def project_settings(path):
    try: ps = json.loads(zipfile.ZipFile(path).read('Metadata/project_settings.config'))
    except Exception: return None
    return {k: (';'.join(ps[k]) if isinstance(ps.get(k), list) else ps.get(k)) for k in KEYS if k in ps}
def slice_one(exe, path, outdir, timeout=1200):
    os.makedirs(outdir, exist_ok=True); name = os.path.splitext(os.path.basename(path))[0]; out3 = os.path.join(os.path.abspath(outdir), f'{name}_sliced.3mf')
    cmd = ([shutil.which('xvfb-run'), '-a'] if shutil.which('xvfb-run') else []) + [exe, '--slice', '0', '--debug', '2', '--export-3mf', out3, os.path.abspath(path)]
    t = time.time(); p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    log = p.stdout + '\n' + p.stderr; open(os.path.join(outdir, f'{name}.log'), 'w').write(log)
    r = {'file': path, 'exit': p.returncode, 'seconds': round(time.time() - t), 'sliced_3mf': os.path.exists(out3)}
    gc = ''
    if r['sliced_3mf']:
        z = zipfile.ZipFile(out3); gn = [n for n in z.namelist() if n.endswith('.gcode')]; r['gcode_files'] = gn
        if gn: gc = z.read(gn[0]).decode('utf-8', 'ignore'); open(os.path.join(outdir, f'{name}.gcode'), 'w').write(gc)
    r['gcode_settings'] = gcode_settings(gc) if gc else {}
    want = project_settings(path); r['project_settings'] = want
    if want and r['gcode_settings']:
        norm = lambda v: re.sub(r'[\s,;]+', ';', str(v)).strip(';').lower()
        r['settings_match'] = {k: norm(want[k]) == norm(r['gcode_settings'].get(k, '')) for k in want if k in r['gcode_settings']}
    r['warn_lines'] = [l for l in log.splitlines() if re.search(r'not from bambu|load geometry|error|failed', l, re.I)][:12]
    r['ok'] = p.returncode == 0 and bool(gc) and (not want or all(r.get('settings_match', {}).values()))
    return r
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--files', nargs='+', required=True); ap.add_argument('--out', default='bambu_out'); ap.add_argument('--download', action='store_true')
    ap.add_argument('--summary'); ap.add_argument('--expect-project', nargs='*', default=None, help='프로젝트로 열려야 하는 파일(기본: 이름에 _bambu 가 들어간 것)')
    a = ap.parse_args(); files = [f for pat in a.files for f in sorted(glob.glob(pat))] or a.files
    exe = os.environ.get('BAMBU_STUDIO'); tag = asset = '(환경변수)'
    if not exe:
        if not a.download: raise SystemExit('BAMBU_STUDIO 환경변수 또는 --download 필요')
        exe, tag, asset = download()
    must = set(a.expect_project) if a.expect_project is not None else {f for f in files if '_bambu' in os.path.basename(f)}
    res = [slice_one(exe, f, a.out) for f in files]
    L = [f'## Bambu Studio 실제 열기·슬라이스 검증 ({tag}, {asset})', '', '| 파일 | 프로젝트여야 함 | 종료 코드 | G-code | 설정 일치(3MF→G-code) | 판정 |', '|---|---|---|---|---|---|']
    bad = []
    for r in res:
        m = r.get('settings_match', {}); mm = f"{sum(m.values())}/{len(m)}" if m else '-'
        need = r['file'] in must; verdict = '✓ 프로젝트로 슬라이스' if r['ok'] else ('⚠ 실패' if need else 'ℹ (비교용) ' + ('슬라이스됨' if r.get('gcode_files') else '실패'))
        if need and not r['ok']: bad.append(r['file'])
        L.append(f"| {os.path.basename(r['file'])} | {'예' if need else '아니오'} | {r['exit']} | {'있음' if r.get('gcode_files') else '없음'} | {mm} | {verdict} |")
    L += [''] + [f"- {os.path.basename(r['file'])}: G-code 설정 {r['gcode_settings']} / 경고 줄 {r['warn_lines'][:4]}" for r in res]
    txt = '\n'.join(L); print(txt); json.dump(res, open(os.path.join(a.out, 'result.json'), 'w'), ensure_ascii=False, indent=1)
    if a.summary: open(a.summary, 'a').write(txt + '\n')
    sys.exit(1 if bad else 0)
if __name__ == '__main__': main()
