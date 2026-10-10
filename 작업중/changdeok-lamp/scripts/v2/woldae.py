"""월대(회색) 3단: 단마다 장대석 줄눈(층당 ≤0.115 V 홈), 정면 계단 = 가운데 답도(경사판+테두리·마름모 부조) + 좌우 계단 + 소맷돌 4개(머리돌).
조립 좌표: 맨 윗단 윗면 z=0, 건물 중심 (0,0), 정면 -y. 위로 갈수록 좁아지거나 수직(오버행 0)."""
import numpy as np, trimesh
from geo import B, CYL, U, D, HULL
import params as P
def _course_groove(w, d, cy, z0):
    lo=HULL([[sx*w/2, cy+sy*d/2, z0] for sx in(-1,1) for sy in(-1,1)]+[[sx*(w/2-0.4), cy+sy*(d/2-0.4), z0+0.15] for sx in(-1,1) for sy in(-1,1)])
    hi=HULL([[sx*(w/2-0.4), cy+sy*(d/2-0.4), z0+0.15] for sx in(-1,1) for sy in(-1,1)]+[[sx*w/2, cy+sy*d/2, z0+0.85] for sx in(-1,1) for sy in(-1,1)])
    return D(B(w+2, d+2, 0.85, 0, cy, z0), U([lo,hi]))
def _flight(xc, width, n, rise, tread, y_front, z0):
    depth=n*tread   # i 번째 단: y_front+i*tread ~ 뒤끝, 높이 z0+i*rise ~ z0+(i+1)*rise (위 단일수록 뒤에서 시작)
    return U([B(width, depth-i*tread, rise+(0.01 if i<n-1 else 0), xc, y_front+(i*tread+depth)/2, z0+i*rise) for i in range(n)])
def _stair(y_front, z0, h, n, tread=2.4, w_flight=17.0, w_ramp=11.0, w_stone=2.6):
    depth=n*tread; rise=h/n
    xr=w_ramp/2; xs1=xr+w_stone; xf=xs1+w_flight; xs2=xf+w_stone
    notch=B(2*xs2, depth+0.01, h+1, 0, y_front+depth/2-0.005, z0+0.6)
    parts=[]
    for sx in (-1,1): parts.append(_flight(sx*(xs1+w_flight/2), w_flight, n, rise, tread, y_front, z0))
    ramp=HULL([[sx*xr, y_front, z0] for sx in(-1,1)]+[[sx*xr, y_front+depth, z0] for sx in(-1,1)]+[[sx*xr, y_front+depth, z0+h] for sx in(-1,1)]+[[sx*xr, y_front+0.6, z0+0.6] for sx in(-1,1)])
    parts.append(ramp)
    slope=np.arctan2(h, depth); nrm=np.array([0,-np.sin(slope),np.cos(slope)])
    def on_ramp(x0,x1,t0,t1,th=0.6):
        pts=[]
        for x in (x0,x1):
            for t in (t0,t1):
                p=np.array([x, y_front+depth*t, z0+h*t]); pts+= [p-nrm*0.3, p+nrm*th]
        return HULL(pts)
    parts+= [on_ramp(-xr+0.6,-xr+1.6,0.12,0.98), on_ramp(xr-1.6,xr-0.6,0.12,0.98)]
    if h>5:
        for t in (0.3,0.65):
            c=np.array([0, y_front+depth*t, z0+h*t]); u=np.array([1,0,0]); v=np.array([0,np.cos(slope),np.sin(slope)])
            q=[c+2.6*u, c-2.6*u, c+depth*0.12*v, c-depth*0.12*v]; parts.append(HULL([p-nrm*0.3 for p in q]+[p+nrm*0.6 for p in q]))
    for xc in (-xs2+w_stone/2, -xr-w_stone/2, xr+w_stone/2, xs2-w_stone/2):
        hw=w_stone/2; ht=min(h, rise*1.5+1.0)
        parts.append(HULL([[xc-hw,y_front+1.2,z0],[xc+hw,y_front+1.2,z0],[xc-hw,y_front+depth,z0],[xc+hw,y_front+depth,z0],
                           [xc-hw,y_front+depth,z0+h+1.0],[xc+hw,y_front+depth,z0+h+1.0],[xc-hw,y_front+1.2,z0+ht],[xc+hw,y_front+1.2,z0+ht]]))
        parts.append(B(w_stone, 2.4, ht+0.6, xc, y_front+1.2, z0))
    return notch, U(parts)
TIERS=None
def platform(floor_wd, clr=P.CLR):
    global TIERS
    T3=(P.PLAT_UP[0], P.PLAT_UP[1]/2, -P.PLAT_UP[1]/2, 3.5)
    T2=(T3[0]+14, T3[1]+7, T3[2]-22, 8.0)
    T1=(T2[0]+14, T2[1]+7, T2[2]-26, 11.0)
    z1=-(T1[3]+T2[3]+T3[3]); z2=z1+T1[3]; z3=z2+T2[3]
    tiers=[(T1,z1),(T2,z2),(T3,z3)]; TIERS=tiers
    plat=U([B(t[0], t[1]-t[2], t[3]+(0.01 if i<2 else 0), 0, (t[1]+t[2])/2, z) for i,(t,z) in enumerate(tiers)])
    cuts=[]
    for (t,z) in tiers:
        n=max(1,int(round(t[3]/3.0))); hh=t[3]/n
        for k in range(1,n): cuts.append(_course_groove(t[0], t[1]-t[2], (t[1]+t[2])/2, z+k*hh-0.425))
    if cuts: plat=D(plat, U(cuts))
    notches=[]; solids=[]
    for (t,z),n,tr in zip(tiers,(8,6,3),(2.4,2.4,2.0)):
        nt,so=_stair(t[2], z, t[3], n, tread=tr); notches.append(nt); solids.append(so)
    plat=D(plat, U(notches)); plat=U([plat]+solids)
    z_pf=z1+3.0
    plat=D(plat, CYL(P.LED_D+2*P.LED_CLR, 100, 0,0, z_pf))
    plat=D(plat, B(P.CABLE_W, T1[1], P.CABLE_H, 0, T1[1]/2, z_pf))
    plat=D(plat, B(floor_wd[0]+2*clr, floor_wd[1]+2*clr, 10, 0,0, -1.0))
    return plat
