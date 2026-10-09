#!/usr/bin/env python3
from pathlib import Path
import json
import shutil
import sys
ROOT=Path(__file__).resolve().parents[3];PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import render_preview as renderer
renderer.CHROME=shutil.which('chromium') or '/opt/pw-browsers/chromium'
qc=PROJECT/'qc'
colors={'base':'#37474f','lid':'#37474f','logo':'#ffb300','handle':'#37474f','latch':'#37474f'}
colors.update({f'nameplate_{r}_{c}_{s}':('#d7ddd7' if s%2 else '#90b7ba')
               for r in [1,2] for c in [1,2,3] for s in range(1,9)})
renderer.render(renderer.load([str(qc/'upright48.3mf')]),str(qc/'upright48'),colors,
                frames=24,status='완료 — 6칸 × 8개 = 48개 세워 수납 · U자 받침 곡률 유지')
states=json.loads((qc/'states.json').read_text())
renderer.render(renderer.load([str(qc/'assembly48.3mf')]),str(qc/'assembly48'),colors,
                states,36,status='완료 — 본체 171.3 × 150.0 × 29.9 mm · 48개 세워 수납\n⚠ 클립은 기존 형상, 렌더에서 분리 표시')
print('PNG views and GIFs written to',qc)
