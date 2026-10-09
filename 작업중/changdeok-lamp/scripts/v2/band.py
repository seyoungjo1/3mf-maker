"""공포 띠(초록 계단 띠 + 갈색 포 단위 배열). 조립 좌표로 만들고 출력은 뒤집는다(넓은 단이 바닥).
ring_out: 평방 링 바깥 치수(w,d). 띠 바닥 단은 1.0 proud, 단마다 step 만큼 더 나감. 안쪽 개구 = 림 바깥 + 0.6."""
import numpy as np
from geo import B, U, D, RING, centers
import params as P
def band(ring_out, rim_out, z0, h, step=P.BAND_STEP, tiers=P.BAND_TIERS, unit_w=6.7, pitch=P.BRACKET_PITCH, clr=P.CLR):
    w,d=ring_out; th=h/tiers
    cores=[]
    for k in range(tiers):
        o=1.0+step*k; cores.append(B(w+2*o, d+2*o, th+(0.01 if k<tiers-1 else 0), 0,0, z0+th*k))
    green=U(cores); inner=B(rim_out[0]+2*clr, rim_out[1]+2*clr, h+2, 0,0, z0-1); green=D(green, inner)
    units=[]
    # 포 단위: 뒤(띠 안쪽 면에서 1.2 안)에서 앞(단 면 + 1.0)까지 계단형, 폭 unit_w
    def unit_x(xc, side):     # side: 'f'(-y) / 'b'(+y) 면에 있는 단위, x 중심 xc
        parts=[]
        for k in range(tiers):
            o=1.0+step*k+1.0; back=d/2+1.0-1.2-1.0   # 뒤쪽 끝: 바닥 단 면(d/2+1.0)에서 2.2 안
            y0=back; y1=d/2+o; cy=(y0+y1)/2*(1 if side=='b' else -1)
            parts.append(B(unit_w, y1-y0, th+(0.01 if k<tiers-1 else 0), xc, cy, z0+th*k))
        return U(parts)
    def unit_y(yc, side):
        parts=[]
        for k in range(tiers):
            o=1.0+step*k+1.0; back=w/2+1.0-2.2; x0=back; x1=w/2+o; cx=(x0+x1)/2*(1 if side=='r' else -1)
            parts.append(B(x1-x0, unit_w, th+(0.01 if k<tiers-1 else 0), cx, yc, z0+th*k))
        return U(parts)
    xs=centers(-w/2, w/2, pitch, margin=unit_w/2+1.0); ys=centers(-d/2, d/2, pitch, margin=unit_w/2+1.0)
    for x in xs: units.append(unit_x(x,'f')); units.append(unit_x(x,'b'))
    for y in ys: units.append(unit_y(y,'l')); units.append(unit_y(y,'r'))
    brown=U(units); green=D(green, brown)
    return green, brown
