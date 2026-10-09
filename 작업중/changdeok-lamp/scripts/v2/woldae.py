"""월대(회색): 2단 + 장대석 줄눈 + 정면 앞치마(답도 + 좌우 계단 + 소맷돌) + LED 포켓(위에서) + 전선 터널 + 바닥판 자리. 조립 좌표: 윗면 z=0."""
import numpy as np, trimesh
from geo import B, CYL, U, D, HULL
import params as P
def platform(floor_wd, clr=P.CLR):
    W1,D1,H1=P.PLAT_LO; W2,D2,H2=P.PLAT_UP; A=P.APRON_Y
    z_lo=-(H1+H2); z_up=-H2
    plat=U([B(W1, D1+A, H1, 0, -A/2, z_lo), B(W2, D2, H2, 0, 0, z_up)])
    cuts=[]                                                   # 장대석 줄눈: 수평 홈 0.6×0.5, 피치 3.3
    for z in np.arange(z_lo+3.3, z_up-0.4, 3.3): cuts.append(D(B(W1+2, D1+A+2, 0.6, 0, -A/2, z), B(W1-1.0, D1+A-1.0, 1, 0, -A/2, z-0.2)))
    for z in np.arange(z_up+1.75, -0.6, 3.3): cuts.append(D(B(W2+2, D2+2, 0.6, 0, 0, z), B(W2-1.0, D2-1.0, 1, 0, 0, z-0.2)))
    plat=D(plat, U(cuts))
    yf=-(D1/2+A)                                              # 앞치마 앞면
    def flight(xc, width, n, rise, tread, y_front, z0):
        return U([B(width, (n-i)*tread, rise, xc, y_front+((n-i)*tread)/2, z0+i*rise) for i in range(n)])
    n1=int(round(H1/P.STEP_RISE)); r1=H1/n1; t1=(A-2.0)/n1
    steps=[flight(sx*17.0, 20.0, n1, r1, t1, yf, z_lo) for sx in (-1,1)]                   # 하단 좌우 계단
    ramp=HULL([[sx*6.0, yf+0.4, z_lo] for sx in(-1,1)]+[[sx*6.0, yf+(A-2.0), z_lo] for sx in(-1,1)]+[[sx*6.0, yf+(A-2.0), z_up] for sx in(-1,1)]+[[sx*6.0, yf+0.4, z_lo+0.4] for sx in(-1,1)])   # 답도(경사판)
    stones=[]
    for xc in (-29.0, -5.0, 5.0, 29.0):                                                      # 소맷돌: 계단 옆 경사 블록
        stones.append(HULL([[xc-1,yf,z_lo],[xc+1,yf,z_lo],[xc-1,yf+(A-2.0)+2,z_lo],[xc+1,yf+(A-2.0)+2,z_lo],[xc-1,yf+(A-2.0)+2,z_up+1.5],[xc+1,yf+(A-2.0)+2,z_up+1.5],[xc-1,yf+1.5,z_lo+2.0],[xc+1,yf+1.5,z_lo+2.0]]))
    n2=max(2,int(round(H2/1.2))); r2=H2/n2; t2=1.6
    up_steps=[flight(sx*17.0, 20.0, n2, r2, t2, -D2/2-n2*t2, z_up) for sx in (-1,1)]        # 상단 계단
    plat=U([plat, ramp]+steps+stones+up_steps)
    z_pf=z_lo+3.0
    plat=D(plat, CYL(P.LED_D+2*P.LED_CLR, 100, 0,0, z_pf))                                   # LED 포켓(위에서)
    plat=D(plat, B(P.CABLE_W, D2, P.CABLE_H, 0, D2/2, z_pf))                                  # 전선 터널(뒤)
    plat=D(plat, B(floor_wd[0]+2*clr, floor_wd[1]+2*clr, 10, 0,0, -1.0))                     # 바닥판 자리(1 mm)
    return plat
