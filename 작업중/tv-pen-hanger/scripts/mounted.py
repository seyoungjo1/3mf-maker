"""설치 상태(걸림) 파트를 설치 좌표로 놓아 pickle 로 저장 — `mm section` 단면 그림의 입력(실측 근거).
사용: python scripts/mounted.py  → qc/current/mounted.pkl {이름: trimesh}"""
import os, sys, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE); sys.path.insert(0, HERE)
import assembly
os.chdir(PROJ); parts = pickle.load(open('parts_nominal.pkl', 'rb')); asm = assembly.define(parts); allp = dict(parts); allp.update(asm['extra'])
out = {}
for n, M in asm['states']['걸림'].items():
    m = allp[n].copy(); m.apply_transform(np.asarray(M, float)); out[n] = m
os.makedirs('qc/current', exist_ok=True); pickle.dump(out, open('qc/current/mounted.pkl', 'wb')); print('mounted.pkl', list(out))
