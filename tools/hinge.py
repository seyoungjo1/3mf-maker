#!/usr/bin/env python3
"""핀 경첩 생성기 — 두 잎(leaf) + 너클, M3 핀/볼트 구멍, 눕혀 출력(핀 축이 베드와 평행).
규칙(스터디 2026-10): 구멍 = 핀 + 0.3, 너클 벽 ≥ 1.6, 너클 사이 축방향 틈 0.3, 잎 ≥ 2.4, 너클 밑은 평평하게(D형: 반폭 0.866r 블록 → 윗쪽 원통 오버행 ≤ 30°),
상대 너클 자리는 잎을 파냄(노치 반폭 = sqrt((블록모서리반경+0.3)² − (r−잎두께)²) → 0~180° 회전 간섭 0). 사용: python hinge.py --pin 3.0 --length 40 --knuckles 5 --out A.stl B.stl
"""
import argparse, numpy as np, trimesh
from trimesh.creation import box, cylinder
from trimesh.transformations import rotation_matrix as R
def make_hinge(pin=3.0, length=40.0, knuckles=5, leaf=20.0, thick=2.4, wall=1.8, gap=0.3, hole_extra=0.3, screw=3.4):
    hole=pin+hole_extra; kr=(hole+2*wall)/2; seg=(length-(knuckles-1)*gap)/knuckles; hw=0.866*kr
    Rb=np.hypot(hw,kr)                                   # 너클 블록 바닥 모서리의 축 기준 반경(회전 포락선)
    notch_hw=float(np.sqrt((Rb+gap)**2-max(kr-thick,0)**2))   # 상대 잎 노치 반폭: 블록 모서리가 회전해도 잎에 안 닿게
    segs=[(k*(seg+gap), k*(seg+gap)+seg, 'A' if k%2==0 else 'B') for k in range(knuckles)]
    out={}
    for side,sign in [('A',1),('B',-1)]:
        pieces=[]
        lf=box(extents=[length,leaf,thick]); lf.apply_translation([length/2, sign*(leaf/2+hw-0.5), thick/2]); pieces.append(lf)   # 잎: 너클 블록과 0.5 겹침
        for x0,x1,s in segs:
            if s!=side: continue
            c=cylinder(radius=kr,height=x1-x0,sections=64); c.apply_transform(R(np.pi/2,[0,1,0])); c.apply_translation([(x0+x1)/2,0,kr])
            b=box(extents=[x1-x0,2*hw,kr]); b.apply_translation([(x0+x1)/2,0,kr/2]); pieces+= [c,b]
        body=trimesh.boolean.union(pieces,engine='manifold')
        # 노치: 상대 너클 자리 (x 범위 ± gap, y 는 축에서 kr+gap 까지)
        for x0,x1,s in segs:
            if s==side: continue
            n=box(extents=[x1-x0+2*gap, 2*notch_hw, 3*kr]); n.apply_translation([(x0+x1)/2,0,kr]); body=body.difference(n,engine='manifold')
        h=cylinder(radius=hole/2,height=length+2,sections=48); h.apply_transform(R(np.pi/2,[0,1,0])); h.apply_translation([length/2,0,kr]); body=body.difference(h,engine='manifold')
        for xs in [length*0.25,length*0.75]:
            s_=cylinder(radius=screw/2,height=thick+2,sections=32); s_.apply_translation([xs, sign*(hw+leaf*0.55), thick/2]); body=body.difference(s_,engine='manifold')
        out[side]=body
    return out, dict(pin=pin,hole=hole,knuckle_r=kr,segment=round(seg,3),gap=gap,leaf=leaf,thick=thick,wall=wall,notch_half_width=round(notch_hw,3),axis=('x', 0.0, kr))
def sweep(parts, info, angles=range(0,-181,-15)):
    """B 잎을 핀 축 둘레로 회전(음의 각 = 잎이 위로 올라가는 열림 방향)시키며 A 와의 교집합 부피"""
    A=parts['A']; res=[]; ax=np.array([0,0,info['axis'][2]])
    for a in angles:
        Bm=parts['B'].copy(); M=trimesh.transformations.translation_matrix(ax)@R(np.radians(a),[1,0,0])@trimesh.transformations.translation_matrix(-ax); Bm.apply_transform(M)
        try: iv=A.intersection(Bm,engine='manifold'); v=abs(iv.volume) if iv.is_volume else 0.0
        except Exception: v=-1
        res.append((a,round(v,3)))
    return res
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--pin',type=float,default=3.0); ap.add_argument('--length',type=float,default=40); ap.add_argument('--knuckles',type=int,default=5)
    ap.add_argument('--leaf',type=float,default=20); ap.add_argument('--thick',type=float,default=2.4); ap.add_argument('--out',nargs=2,required=True); ap.add_argument('--sweep',action='store_true')
    a=ap.parse_args(); parts,info=make_hinge(a.pin,a.length,a.knuckles,a.leaf,a.thick)
    for (side,m),fn in zip(parts.items(),a.out): m.export(fn); print(side,fn,'is_volume',m.is_volume,'bodies',len(m.split()),'faces',len(m.faces))
    print(info)
    if a.sweep: print('회전 스윕(B 열림 0~180°) 교집합 mm³:',[(abs(a),v) for a,v in sweep(parts,info)])
