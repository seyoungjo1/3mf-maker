#!/usr/bin/env python3
"""objs_v2.pkl → 출력 방향 STL(models/v2/print), 렌더 색 문자열(qc/v2_colors.txt), 조립/분리 상태(qc/states_v2.json)."""
import os, sys, json, pickle, numpy as np, trimesh
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import assemble as A
sys.path.insert(0,os.path.join(HERE,'..','..','..','..','tools')); from efc import pre_expand_first_layer
ROOT=os.path.join(HERE,'..','..'); MD=os.path.join(ROOT,'models','v2')
objs=pickle.load(open(os.path.join(MD,'objs_v2.pkl'),'rb'))['objs']
os.makedirs(os.path.join(MD,'print'),exist_ok=True)
HEX={'gray':'#9e9e9e','brown':'#6d4c41','white':'#f5f5f5','green':'#2e7d32','tile':'#263238'}
cols={}; lift={}
order=['platform','L_floor','wall','L_diffuser','L_ring','L_band','L_roof_soffit','L_roof_eave_white','L_roof_tile','L_roof_hip','U_floor','uwall','U_diffuser','U_ring','U_band','U_roof_soffit','U_roof_eave_white','U_roof_tile','U_roof_gable','U_roof_hip','U_roof_desc','U_roof_ridge']
def grp(n):
    for k in sorted(order,key=len,reverse=True):
        if n.startswith(k): return order.index(k)
    return 0
for o in objs:
    pm=trimesh.util.concatenate([q for q,_,_ in A.printed(o)])
    pe=pre_expand_first_layer(pm, 0.15, 0.2)                                    # EFC 선반영: 첫 층 +0.15 (사용자 프로파일 코끼리발 보정 0.15)
    if not pe.is_volume: print('EFC 실패', o['name'])
    bs=[b for b in pe.split(only_watertight=False) if abs(b.volume)>1.0]          # 유니온이 남긴 부피 0 퇴화 조각 제거
    if len(bs)==1: pe=bs[0]
    pe.export(os.path.join(MD,'print',o['name']+'.stl'))
    for m,c,n in o['parts']: cols[n]=HEX[c]; lift[n]=grp(n)*9.0
sepv={n:[0,0,lift[n]] for n in cols}
for g,sx in (('U_roof_gableL',-1),('U_roof_gableR',1)):
    if g in sepv: sepv[g]=[sx*30.0,0,lift.get('U_roof_tile',0)]          # 합각 널: 옆 포켓 → 옆으로 분리
json.dump({'조립':{n:[0,0,0] for n in cols},'분리':sepv}, open(os.path.join(ROOT,'qc','states_v2.json'),'w'), ensure_ascii=False)
open(os.path.join(ROOT,'qc','v2_colors.txt'),'w').write(','.join(f'{n}={c}' for n,c in cols.items()))
print('exported', len(objs))
