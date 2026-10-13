#!/usr/bin/env python3
"""NASA 우주 직물형 적층섬유 5×5 시험편(쿠폰) — 모양 확인·출력 시험용. `python tools/mm.py make 작업중/racket-grip-case/pipeline_coupon.json`
산출: parts_coupon_nominal.pkl / parts_coupon.pkl(첫 층 +0.15) / models/racket-grip-case_coupon.3mf"""
import os, sys, pickle
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE); ROOT = os.path.dirname(os.path.dirname(PROJ))
sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, HERE)
import numpy as np, trimesh, manifold3d as mf
from efc import pre_expand_first_layer
from generic3mf import write_generic_3mf
import nasa

NX = NY = 5

def to_tm(m):
    g = m.to_mesh(); return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)

def make_parts():
    a = nasa.N['a']; As, Bs = nasa.sheet(NX, NY, x0=a, y0=a)
    return {'coupon_A': to_tm(mf.Manifold.compose(As)), 'coupon_B': to_tm(mf.Manifold.compose(Bs))}

if __name__ == '__main__':
    os.chdir(PROJ); os.makedirs('models', exist_ok=True)
    nom = make_parts(); pickle.dump(nom, open('parts_coupon_nominal.pkl', 'wb'))
    pr = {k: pre_expand_first_layer(m) for k, m in nom.items()}; pickle.dump(pr, open('parts_coupon.pkl', 'wb'))
    sh = [10.0, 10.0, 0]
    write_generic_3mf('models/racket-grip-case_coupon.3mf', [{'name': 'coupon', 'parts': [(pr[k].copy().apply_translation(sh), '#37474f', k) for k in pr]}], 'racket-grip-case coupon')
    print('coupon ok', {k: [round(v, 2) for v in m.extents] for k, m in nom.items()})
