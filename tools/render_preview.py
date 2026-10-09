#!/usr/bin/env python3
"""3d-print 열쇠고리 프로그램의 미리보기(three.js, 어두운 배경, 격자 베드, flatShading)를 헤드리스로 재현해
PNG 5장(기본 iso/상부 top/측면 side/밑면 bottom/정면 저각도 front)과 회전 GIF 를 만든다.
사용: python tools/render_preview.py <file.3mf | a.stl b.stl ...> --out <dir> [--colors name=#hex,...] [--states states.json] [--frames 36]
  states.json: {"분리": {"lid": [0,0,30]}, "조립": {"lid": [16개 행우선 4x4 행렬]}}  (파트별 평행이동 [dx,dy,dz] 또는 4x4 행렬)  → 상태별 PNG + GIF 에 상태 순환(키캡의 분리/조립-폄/조립-누름과 같은 방식)
"""
import os, sys, json, argparse, threading, http.server, socketserver, functools, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from load3mf import load_parts
import trimesh
CHROME = '/opt/pw-browsers/chromium'
PALETTE = ['#37474f', '#ffb300', '#78909c', '#7ccb8b', '#e57373', '#ba68c8', '#4dd0e1', '#a1887f']

HTML = r'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;background:#1a1d21;overflow:hidden}#viewer{width:__W__px;height:__H__px}
#status{position:absolute;left:12px;bottom:10px;color:#c8cdd3;font:13px/1.5 sans-serif;white-space:pre;background:#1b1e23cc;border:1px solid #3c4043;border-radius:8px;padding:6px 10px}
#label{position:absolute;right:12px;top:10px;color:#e8eaed;font:13px sans-serif;background:#23272ecc;border:1px solid #3c4043;border-radius:6px;padding:5px 10px}
</style></head><body><div id="viewer"></div><div id="status"></div><div id="label"></div>
<script type="importmap">{"imports":{"three":"/viewer/three.module.js"}}</script>
<script type="module">
import * as THREE from 'three'; import { OrbitControls } from '/viewer/OrbitControls.js';
const DATA = await (await fetch('/data.json')).json();
const viewer=document.getElementById('viewer'); const scene=new THREE.Scene(); scene.background=new THREE.Color(0x1a1d21);
const camera=new THREE.PerspectiveCamera(45,__W__/__H__,0.1,4000); const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setSize(__W__,__H__); renderer.setPixelRatio(1); viewer.appendChild(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff,0x444455,1.1));
const dir=new THREE.DirectionalLight(0xffffff,1.2); dir.position.set(-40,-60,90); scene.add(dir);
const dirUp=new THREE.DirectionalLight(0xffffff,0.55); dirUp.position.set(40,60,-90); scene.add(dirUp);
const bedSize=DATA.bed||256; const grid=new THREE.GridHelper(bedSize,bedSize/10,0x3c4043,0x2a2e33); grid.rotation.x=Math.PI/2; grid.position.set(bedSize/2,bedSize/2,0); scene.add(grid);
const bedMat=new THREE.MeshStandardMaterial({color:0x23282e,roughness:0.85,metalness:0.1});
const bed=new THREE.Mesh(new THREE.BoxGeometry(bedSize,bedSize,2),bedMat); bed.position.set(bedSize/2,bedSize/2,-1.05); scene.add(bed);
const meshes={}; const box=new THREE.Box3();
for(const p of DATA.parts){ const g=new THREE.BufferGeometry(); g.setAttribute('position',new THREE.Float32BufferAttribute(p.positions,3)); g.setIndex(p.indices); g.computeVertexNormals();
  const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:p.color,roughness:0.55,metalness:0.05,flatShading:true})); m.userData.base=new THREE.Vector3(0,0,0); scene.add(m); meshes[p.name]=m; box.expandByObject(m); }
camera.up.set(0,0,1); let c=new THREE.Vector3(), s=100;
function fit(){ const bb=new THREE.Box3(); for(const m of Object.values(meshes)){ m.updateMatrixWorld(true); bb.expandByObject(m); } c=bb.getCenter(new THREE.Vector3()); s=bb.getSize(new THREE.Vector3()).length(); }
window.setView=function(mode,azDeg){ fit(); controls.target.copy(c); grid.visible=mode!=='bottom'; bed.visible=mode!=='bottom';
  if(mode==='top') camera.position.set(c.x,c.y-s*0.001,c.z+s*1.3);
  else if(mode==='side') camera.position.set(c.x,c.y-s*1.3,c.z+s*0.03);
  else if(mode==='bottom') camera.position.set(c.x,c.y-s*0.001,c.z-s*1.3);
  else if(mode==='front') camera.position.set(c.x+s*0.25,c.y-s*1.15,c.z+s*0.22);
  else { const a=(azDeg===undefined?0:azDeg)*Math.PI/180; const r=s*0.9; camera.position.set(c.x+r*Math.sin(a),c.y-r*Math.cos(a),c.z+s*0.8); }
  camera.lookAt(c); controls.update(); renderer.render(scene,camera); };
window.setState=function(name){ const st=(DATA.states||{})[name]||{}; for(const [n,m] of Object.entries(meshes)){ const d=st[n]; m.matrixAutoUpdate=false; if(Array.isArray(d)&&d.length===16){ m.matrix.set(...d); } else { const t=d||[0,0,0]; m.matrix.makeTranslation(t[0],t[1],t[2]); } } const lb=document.getElementById('label'); lb.textContent=name||''; lb.style.display=name?'block':'none'; };
document.getElementById('status').textContent=DATA.status||'';
window.setState(DATA.firstState||''); window.setView('iso',0); window.READY=true;
</script></body></html>'''

def mesh_json(m, color, name):
    V = np.asarray(m.vertices, np.float32); F = np.asarray(m.faces, np.uint32)
    return {'name': name, 'color': color, 'positions': [round(float(v), 3) for v in V.ravel()], 'indices': [int(i) for i in F.ravel()]}

def load(paths):
    parts = {}
    for p in paths:
        if p.lower().endswith('.3mf'):
            parts.update(load_parts(p))
        else: parts[os.path.splitext(os.path.basename(p))[0]] = trimesh.load(p, force='mesh')
    return parts

def render(parts, out, colors=None, states=None, frames=36, size=(1200, 900), gif_size=(640, 480), status=None, bed=256):
    os.makedirs(out, exist_ok=True); colors = colors or {}
    data = {'bed': bed, 'parts': [mesh_json(m, colors.get(n, PALETTE[i % len(PALETTE)]), n) for i, (n, m) in enumerate(parts.items())], 'states': states or {},
            'firstState': next(iter(states)) if states else '', 'status': status or ''}
    json.dump(data, open(os.path.join(out, 'data.json'), 'w'))
    for suffix, (w, h) in (('', size), ('_gif', gif_size)):
        open(os.path.join(out, f'index{suffix}.html'), 'w', encoding='utf-8').write(HTML.replace('__W__', str(w)).replace('__H__', str(h)))
    # 정적 서버 (viewer/ 와 out/ 을 함께 서빙)
    class H(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            if path.startswith('/viewer/'): return os.path.join(HERE, 'viewer', path[8:])
            return os.path.join(out, path.lstrip('/'))
        def log_message(self, *a): pass
    srv = socketserver.TCPServer(('127.0.0.1', 0), H); port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
    from playwright.sync_api import sync_playwright
    from PIL import Image
    import io
    pngs = {}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        pg = b.new_page(viewport={'width': size[0], 'height': size[1]}); pg.goto(f'http://127.0.0.1:{port}/index.html'); pg.wait_for_function('window.READY===true', timeout=120000)
        state_names = list(states) if states else ['']
        for st in state_names:
            pg.evaluate(f'window.setState({json.dumps(st)})')
            for v in ('iso', 'top', 'side', 'bottom', 'front'):
                pg.evaluate(f'window.setView({json.dumps(v)},0)'); fn = f'view_{v}' + (f'_{st}' if st else '') + '.png'
                pg.screenshot(path=os.path.join(out, fn)); pngs[fn] = fn
        pg.close()
        pg = b.new_page(viewport={'width': gif_size[0], 'height': gif_size[1]}); pg.goto(f'http://127.0.0.1:{port}/index_gif.html'); pg.wait_for_function('window.READY===true', timeout=120000)
        imgs = []
        per = max(1, frames // len(state_names))
        for st in state_names:
            pg.evaluate(f'window.setState({json.dumps(st)})')
            for k in range(per):
                pg.evaluate(f'window.setView("iso",{360.0 * k / per})'); imgs.append(Image.open(io.BytesIO(pg.screenshot())).convert('RGB').quantize(colors=128, method=Image.Quantize.MEDIANCUT))
        b.close()
    srv.shutdown()
    imgs[0].save(os.path.join(out, 'turntable.gif'), save_all=True, append_images=imgs[1:], duration=int(4000 / max(1, len(imgs))), loop=0, optimize=True)
    return pngs

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('files', nargs='+'); ap.add_argument('--out', required=True); ap.add_argument('--colors', default='')
    ap.add_argument('--states'); ap.add_argument('--frames', type=int, default=36); ap.add_argument('--status', default=''); ap.add_argument('--bed', type=int, default=256)
    a = ap.parse_args(); parts = load(a.files)
    colors = dict(kv.split('=') for kv in a.colors.split(',') if '=' in kv)
    states = json.load(open(a.states)) if a.states else None
    size = [sum(m.bounds[1][i] for m in parts.values()) for i in range(3)]
    allb = np.array([m.bounds for m in parts.values()]); mn, mx = allb[:, 0].min(0), allb[:, 1].max(0)
    status = a.status or f'완료 — 모델 크기 {mx[0]-mn[0]:.1f} × {mx[1]-mn[1]:.1f} × {mx[2]-mn[2]:.1f} mm · 파트 {len(parts)}개: ' + ', '.join(parts)
    print(render(parts, a.out, colors, states, a.frames, status=status, bed=a.bed)); print('gif:', os.path.join(a.out, 'turntable.gif'))
