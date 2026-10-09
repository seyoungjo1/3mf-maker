#!/usr/bin/env python3
"""파트별 출력 무게 추정(PLA 1.24 g/cm³): 층 단면으로 벽 2줄(0.84 mm)·바닥/윗면 1 mm 솔리드·인필 15 % 를 흉내낸다. ±20 % 추정치.
사용: python estimate_weight.py [--infill 0.15] [--walls 0.84]"""
import os, sys, argparse, pickle, numpy as np, trimesh
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.abspath(os.path.join(HERE,'..','..','..')); sys.path.insert(0, os.path.join(ROOT,'tools'))
from overhang import layer_poly
ap=argparse.ArgumentParser(); ap.add_argument('--infill',type=float,default=0.15); ap.add_argument('--walls',type=float,default=0.84); ap.add_argument('--layer',type=float,default=0.2); a=ap.parse_args()
RHO=1.24e-3
d=pickle.load(open(os.path.join(HERE,'..','models','parts_v1.pkl'),'rb')); rows=[]; tot_s=tot_e=0
for name,(m,slot,flip) in d['parts'].items():
    z0,z1=m.bounds[0,2],m.bounds[1,2]; zs=np.arange(z0+a.layer/2, z1, a.layer); vol_est=0.0; prev_in=None
    polys=[layer_poly(m,z) for z in zs]
    for i,p in enumerate(polys):
        if p.is_empty: continue
        inner=p.buffer(-a.walls); A=p.area; Ai=inner.area
        # 윗면/바닥 솔리드: 이 층의 안쪽 영역 중 위 1 mm 또는 아래 1 mm 안에서 빈 공간과 만나는 부분은 솔리드로 간주
        solid=inner; n=int(round(1.0/a.layer))
        cover=None
        for j in range(1,n+1):
            for q in (polys[i-j] if i-j>=0 else None, polys[i+j] if i+j<len(polys) else None):
                qq=q if (q is not None and not q.is_empty) else None
                solid_part = inner.difference(qq.buffer(-a.walls*0.5)) if qq is not None else inner
                cover = solid_part if cover is None else cover.union(solid_part)
        As=cover.area if cover is not None else 0.0
        vol_est += a.layer*((A-Ai) + As + a.infill*max(Ai-As,0))
    vs=abs(m.volume); rows.append((name, vs/1000, vs*RHO, vol_est*RHO)); tot_s+=vs*RHO; tot_e+=vol_est*RHO
print('| 파트 | 부피 cm³ | 통짜 g | 추정 g (벽 2줄·상하 1 mm·인필 %d %%) |'%round(a.infill*100)); print('|---|---|---|---|')
for n,v,ws,we in rows: print(f'| {n} | {v:.1f} | {ws:.0f} | {we:.0f} |')
print(f'| **합계** | | **{tot_s:.0f}** | **{tot_e:.0f}** |')
