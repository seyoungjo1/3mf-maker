"""공포 띠(초록) — 처마 밑 경사면의 안쪽 부분(쐐기). 스캔 단면: 처마 밑선은 평방 바깥 모서리(z0)에서 처마 끝(z0+h)까지 곧게 올라간다.
띠 = 그 경사선 위·평방 위의 쐐기(바깥 폭 OUT), 윗면 평평(z0+h, 처마밑이 얹힘). 포 단위 = 경사면 아래로 0.8 돌출한 세로 줄(피치 BRACKET_PITCH).
출력: 뒤집어서(윗면이 베드) → 경사면·포 줄이 위를 본다(서포트 없음)."""
import numpy as np
from geo import B, U, D, I, HULL, segbox, centers
import params as P
OUT=8.0
def _rect(w,d,z): return [[sx*w/2,sy*d/2,z] for sx in(-1,1) for sy in(-1,1)]
def under_wedge(ring_out, eave, z0, z1):
    """평방 바깥(z0) → 처마 끝(z1) 경사선 위, z1 까지의 쐐기(볼록)"""
    (w,d),(EX,EY)=ring_out,eave
    return HULL(_rect(w,d,z0)+_rect(EX,EY,z1)+_rect(w,d,z1))
def band(ring_out, rim_out, z0, h, eave, clr=P.CLR):
    w,d=ring_out; EX,EY=eave; z1=z0+h
    wedge=under_wedge(ring_out, eave, z0, z1)
    g=U([I(wedge, B(w+2*OUT, d+2*OUT, h+2, 0,0, z0-1)), B(w, d, h, 0,0, z0)])
    g=D(g, B(rim_out[0]+2*clr, rim_out[1]+2*clr, h+2, 0,0, z0-1))
    # 포 단위: 경사면을 따라 바깥으로 뻗는 줄(폭 2.4, 0.8 돌출), 모서리 근처 제외
    sx_=(EX/2-w/2); sy_=(EY/2-d/2); ribs=[]
    for x in centers(-w/2+4, w/2-4, P.BRACKET_PITCH):
        for s in (-1,1):
            a=(x, s*d/2, z0); b=(x, s*(d/2+OUT), z0+h*OUT/sy_); ribs.append(segbox(a,b,2.4,1.6))
    for y in centers(-d/2+4, d/2-4, P.BRACKET_PITCH):
        for s in (-1,1):
            a=(s*w/2, y, z0); b=(s*(w/2+OUT), y, z0+h*OUT/sx_); ribs.append(segbox(a,b,2.4,1.6))
    ribs=I(U(ribs), B(w+2*OUT-0.01, d+2*OUT-0.01, h+2, 0,0, z0-0.8))
    ribs=D(ribs, B(w-0.01, d-0.01, h+3, 0,0, z0-1.5))
    return U([g, ribs]), None
