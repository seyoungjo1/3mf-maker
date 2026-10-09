#!/usr/bin/env python3
"""창덕궁 인정전 모티브 LED 램프 — 매개변수 생성기 (v1)
비례: 인정전 점군 스캔 실루엣(refs/scan_*.jpg)에서 추출. 조명: Bambu LED Lamp Kit 001 (Ø59×18 퍽) — 월대 윗면 포켓에 위에서 넣고 하층 바닥판이 덮는다(랜턴 샘플 방식).
파트 = 색: 1 회색(월대) / 2 갈색(몸체·창살) / 3 흰색(발광 갓·처마 흰 띠) / 4 초록(공포 띠) / 5 기와색(지붕).
출력 방향: 월대·몸체·갓·지붕 = 정방향, 공포 띠 = 뒤집어(넓은 면 바닥).
오버행 규칙(층당 ≤0.115, 한쪽 지지 금지): 모든 면은 수직이거나 위로 좁아지거나, 넓어져도 층당 ≤0.07(인방 사다리꼴). 브리지(양콁 지지)는 ≤ 3.3 mm.
  - 몸체 단면(바깥면에서 안쪽으로 o): 기둥 Ø6 중심 o=3 / 문지방 o 0~5 / 창살 깊이 o 2~5 / 인방 아래 o 2~5 → 위 o 0~6.3 (6 mm 높이) / 테두리 o 3~5.7 (인방 위에 완전히 얹힘)
  - 띠 안쪽 벽 o=2.7(테두리와 0.3), 지붕 홈 o 2.7~6.0(테두리 양쪽 0.3), 지붕 가운데 개구는 홈 안쪽 섬 벽 2.0 안쪽.
사용: python build_lamp.py  → ../models/*.stl(조립 좌표), ../models/print/*.stl(출력 방향, 바닥 z=0, 첫 층 +0.15 EFC 선반영), parts_v1.pkl
"""
import os, sys, pickle, numpy as np, trimesh
from trimesh.creation import box, cylinder
from trimesh.transformations import rotation_matrix as R, translation_matrix as T
HERE=os.path.dirname(os.path.abspath(__file__)); MODELS=os.path.join(HERE,'..','models')
U=lambda ms: trimesh.boolean.union([m for m in ms if m is not None], engine='manifold')
D=lambda a,b: a.difference(b, engine='manifold')
def B(sx,sy,sz,cx=0,cy=0,z0=0):           # 바닥 z0 에서 시작하는 상자
    b=box(extents=[sx,sy,sz]); b.apply_translation([cx,cy,z0+sz/2]); return b
def CYL(d,h,cx=0,cy=0,z0=0,sec=96):
    c=cylinder(radius=d/2,height=h,sections=sec); c.apply_translation([cx,cy,z0+h/2]); return c
def frustum(w0,d0,z0,w1,d1,z1):          # 직사각 → 직사각 로프트(볼록)
    pts=[]
    for w,d,z in [(w0,d0,z0),(w1,d1,z1)]: pts+= [[sx*w/2,sy*d/2,z] for sx in (-1,1) for sy in (-1,1)]
    return trimesh.convex.convex_hull(np.array(pts))
def ring(w,d,h,z0,wall): return D(B(w,d,h,0,0,z0), B(w-2*wall,d-2*wall,h+2,0,0,z0-1))

P=dict(                                    # ---- 치수표 (mm) ----
    W=160, Dp=124, t1=12, t2=11, inset2=7, inset2_front=14,   # 월대 1단 160×124×12, 2단 (146×103, 앞 14 뒤 7 들여쓰기)×11 → 윗면 z 23. 앞 14 = 2단 계단(5×2.4=12) 자리
    led_d=59, led_h=18, led_clr=0.5, light_d=50, cable_w=6, cable_h=5,   # LED 퍽 Ø59×18 → 포켓 Ø60(위에서), 전선 터널 6×5(뒤로)
    lb_w=103, lb_d=70, lb_h=26, floor_t=3, col_d=6, sill=2.4, sill_wall=5.0, lintel=6, lintel_top_in=6.3,
    lat_in=2.0, lat_depth=3.0, slat=1.4, slat_pitch=3.4, rail=1.4, mullion=1.6, rim_wall=2.7, rim_h=7.5,
    screen_t=0.8, clr=0.3,
    band_h=5, band_out=7.5,                           # 공포 띠: 높이 5, 바깥으로 7.5 (3단)
    lr_eave_w=140, lr_eave_d=104, lr_plate=4, lr_rise=14, trim_w=2,
    ub_w=95, ub_d=61, ub_h=16, ub_plate=4, lip_h=1.8, lip_wall=1.6, top_out=3, island_wall=2.0,
    ur_eave_w=128, ur_eave_d=93, ur_plate=4, ur_rise=32, gable_z=14, ridge_len=85, ridge_w=4, ridge_h=3, chwidu=6,
)
def build(P=P):
    parts={}   # name -> (mesh in assembled coords, color_slot, print_flip)
    clr=P['clr']; cd=P['col_d']; st=P['screen_t']
    # ---------------- 1. 월대 (회색) ----------------
    W,Dp,t1,t2=P['W'],P['Dp'],P['t1'],P['t2']; W2,D2=W-2*P['inset2'],Dp-P['inset2']-P['inset2_front']; cy2=(P['inset2_front']-P['inset2'])/2; zp=t1+t2
    plat=U([B(W,Dp,t1), B(W2,D2,t2,0,cy2,t1)])
    def stairs(n,step_h,tier_front_y,z0,width=36,tread=2.4):   # 정면 계단: 위로 갈수록 안으로(오버행 0)
        return U([B(width,(n-i)*tread,step_h,0,tier_front_y-((n-i)*tread)/2,z0+i*step_h) for i in range(n)])
    plat=U([plat, stairs(6,t1/6,-Dp/2,0), stairs(5,t2/5,cy2-D2/2,t1)])          # 1단 6×2.0(앞으로 14.4 돌출), 2단 5×2.2 (1단 윗면 안, 앞 모서리에서 2 mm 여유)
    pocket_h=P['led_h']+0.5; z_pf=zp-1.0-pocket_h                                   # 포켓 바닥 z 3.5 (= 월대 밑판 두께)
    plat=D(plat, CYL(P['led_d']+2*P['led_clr'], pocket_h+2, 0,0,z_pf))              # LED 포켓(위에서 넣음)
    plat=D(plat, B(P['cable_w'], Dp/2+2, P['cable_h'], 0, (Dp/2+2)/2, z_pf))        # 전선 터널(뒤쪽, 천장 브리지 6)
    plat=D(plat, B(P['lb_w']+2*clr, P['lb_d']+2*clr, 1.2, 0,0, zp-1.0))             # 하층 바닥판 자리(0.3 여유, 1 mm 깊이)
    parts['platform']=(plat,1,False)
    # ---------------- 몸체 공통 ----------------
    def body(w,d,z0,h,plate_t,plate_hole,ncol_x,ncol_y):
        """바닥판(z0, 두께 plate_t, 구멍 plate_hole) + 기둥 + 문지방 + 창살 + 사다리꼴 인방 + 테두리. 반환 (mesh, z_lintel_bottom, z_top)"""
        plate=B(w,d,plate_t,0,0,z0)
        if plate_hole: plate=D(plate, plate_hole)
        xs=np.linspace(-w/2+cd/2, w/2-cd/2, ncol_x); ys=np.linspace(-d/2+cd/2, d/2-cd/2, ncol_y)
        z_top=z0+plate_t+h; cols=[CYL(cd,h,x,y,z0+plate_t-0.01,sec=32) for x in xs for y in (ys[0],ys[-1])]+[CYL(cd,h,x,y,z0+plate_t-0.01,sec=32) for y in ys[1:-1] for x in (xs[0],xs[-1])]
        z_sill=z0+plate_t; z_lat0=z_sill+P['sill']; z_lint=z_top-P['lintel']
        sill=ring(w,d,P['sill'],z_sill,P['sill_wall'])
        li,lo_=P['lat_in'],P['lat_in']+P['lat_depth']                                   # 창살 o 2~5
        s=(P['lintel_top_in']-lo_)/P['lintel']                                            # 인방 안쪽 면 기울기(mm/mm)
        lintel=D(frustum(w-2*li,d-2*li,z_lint, w,d,z_top),                                # 바깥면: 아래 o=2 → 위 o=0 (층당 0.067)
                 frustum(w-2*lo_+2*s,d-2*lo_+2*s,z_lint-1, w-2*P['lintel_top_in']-2*s,d-2*P['lintel_top_in']-2*s,z_top+1))  # 안쪽면: 아래 o=5 → 위 o=6.3 (층당 0.043)
        rim=ring(w-6, d-6, P['rim_h'], z_top-0.5, P['rim_wall'])                          # 테두리 o 3~5.7, 인방 윗면(o 0~6.3) 위
        def lattice_wall(axis, fixed, centers, z0, z1):
            out=[]; hgt=z1-z0; dep=P['lat_depth']
            mk=(lambda c,wd,hz,zz: B(wd,dep,hz,c,fixed,zz)) if axis=='x' else (lambda c,wd,hz,zz: B(dep,wd,hz,fixed,c,zz))
            for a,b in zip(centers[:-1],centers[1:]):
                lo,hi=a+cd/2, b-cd/2; mid=(lo+hi)/2                                      # 보이는 칸
                out.append(mk(mid,P['mullion'],hgt+0.4,z0-0.2))                            # 가운데 멀리언
                half=(hi-lo-P['mullion'])/2; n=max(2,int(round(half/P['slat_pitch']))); gap=(half-(n-1)*P['slat'])/n
                for k in range(1,n):                                                       # 세로살: 칸 반쪽마다 균등(틈 ≈ gap)
                    off=k*gap+(k-1)*P['slat']+P['slat']/2
                    out.append(mk(lo+off,P['slat'],hgt+0.4,z0-0.2)); out.append(mk(hi-off,P['slat'],hgt+0.4,z0-0.2))
                for f in (1/3,2/3): out.append(mk((a+b)/2,(b-a)-2*2.2,P['rail'],z0+hgt*f-P['rail']/2))   # 가로살 2단, 기둥 안으로 0.8 들어감
            return out
        fy=d/2-(li+P['lat_depth']/2); fx=w/2-(li+P['lat_depth']/2)
        walls=[lattice_wall('x',-fy,xs,z_lat0,z_lint), lattice_wall('x',fy,xs,z_lat0,z_lint), lattice_wall('y',-fx,ys,z_lat0,z_lint), lattice_wall('y',fx,ys,z_lat0,z_lint)]
        m=U([plate]+cols+[sill,lintel,rim])
        for wl in walls: m=U([m]+wl)
        gaps=[]
        return m, z_lint, z_top, z_lat0
    # ---------------- 2. 하층 몸체 (갈색) + 발광 갓(흰색) ----------------
    lw,ld,lh,ft=P['lb_w'],P['lb_d'],P['lb_h'],P['floor_t']; zb=zp-1.0                   # 바닥판은 월대 홈(1 mm) 안에
    lower_body,z_lint1,z_band1,z_lat1=body(lw,ld,zb,lh,ft, CYL(P['light_d'],ft+2,0,0,zb-1), 6,5)
    parts['lower_body']=(lower_body,2,False)
    sw,sd=lw-12-2*clr, ld-12-2*clr                                                        # 갓 바깥면: 기둥 안쪽 접선(o=6)에서 0.3
    parts['lower_screen']=(ring(sw,sd,(z_lint1-0.3)-(zb+ft),zb+ft,st),3,False)   # 바닥판 위에 세움(면접촉), 인방 아래 0.3
    # ---------------- 3. 하층 공포 띠 (초록, 뒤집어 출력) ----------------
    def band(w,d,z0):
        h=P['band_h']; o=P['band_out']; inner_w,inner_d=w-6+2*clr,d-6+2*clr               # 안쪽 벽 o=2.7 → 테두리(o=3)와 0.3
        steps=[B(w+2*o*k/3, d+2*o*k/3, h/3+(0.01 if k<2 else 0), 0,0, z0+h*k/3) for k in range(3)]
        return D(U(steps), B(inner_w,inner_d,h+2,0,0,z0-1))
    lower_band=band(lw,ld,z_band1); parts['lower_band']=(lower_band,4,True)
    # ---------------- 4. 하층 지붕 (기와) + 처마 흰 띠 ----------------
    z_lr=z_band1+P['band_h']; ew,ed,pt,rise=P['lr_eave_w'],P['lr_eave_d'],P['lr_plate'],P['lr_rise']
    ubw,ubd=P['ub_w'],P['ub_d']; rw=P['rim_wall']; iw=P['island_wall']
    op_w,op_d=lw-12-2*iw, ld-12-2*iw                                                      # 가운데 개구(빛 통로) = 홈 안쪽(o=6) 섬 벽 2.0 안쪽
    tw=P['trim_w']; top_w,top_d=ubw+2*P['top_out'],ubd+2*P['top_out']
    lroof=U([B(ew-2*tw,ed-2*tw,pt,0,0,z_lr), frustum(ew-2*tw,ed-2*tw,z_lr+pt-0.01, top_w,top_d,z_lr+pt+rise)])
    lroof=D(lroof, B(op_w,op_d,100,0,0,z_lr-1))
    lroof=D(lroof, D(B(lw-6+2*clr,ld-6+2*clr,2.8,0,0,z_lr-0.5), B(lw-12,ld-12,5,0,0,z_lr-1)))   # 테두리 홈 o 2.7~6.0, 천장 z+2.3(브리지 3.3)
    lw_=P['lip_wall']; lroof=U([lroof, ring(ubw+2*clr+2*lw_, ubd+2*clr+2*lw_, P['lip_h'], z_lr+pt+rise-0.01, lw_)])   # 상층 밑판을 바깥에서 잡는 턱
    parts['lower_roof']=(lroof,5,False)
    parts['lower_roof_trim']=(ring(ew,ed,pt,z_lr,tw),3,False)                                 # 처마 끝 흰 띠(같은 오브젝트의 흰색 파트)
    # ---------------- 5. 상층 몸체 (갈색) + 갓 ----------------
    z_ub=z_lr+pt+rise; up_t=P['ub_plate']; uh=P['ub_h']
    upper_body,z_lint2,z_band2,z_lat2=body(ubw,ubd,z_ub,uh,up_t, B(op_w-2*clr-7,op_d-2*clr-7,10,0,0,z_ub-5), 6,4)   # 빛 구멍 79.4×46.4
    parts['upper_body']=(upper_body,2,False)
    usw,usd=ubw-12-2*clr, ubd-12-2*clr
    parts['upper_screen']=(ring(usw,usd,(z_lint2-0.3)-(z_ub+up_t),z_ub+up_t,st),3,False)
    # ---------------- 6. 상층 공포 띠 ----------------
    parts['upper_band']=(band(ubw,ubd,z_band2),4,True)
    # ---------------- 7. 상층 팔작지붕 (기와) + 흰 띠 + 용마루·취두 ----------------
    z_ur=z_band2+P['band_h']; ew2,ed2,pt2,rise2=P['ur_eave_w'],P['ur_eave_d'],P['ur_plate'],P['ur_rise']
    gz=P['gable_z']; rl=P['ridge_len']; z_top=z_ur+pt2+rise2
    slope=rise2/((ed2-2*tw)/2)                                    # 앞뒤 경사 (처마→용마루)
    gd=(ed2-2*tw)-2*gz/slope                                      # 합각 밑변 깊이
    pts=[[sx*(ew2-2*tw)/2, sy*(ed2-2*tw)/2, z_ur+pt2-0.01] for sx in(-1,1) for sy in(-1,1)]
    pts+=[[sx*rl/2, sy*gd/2, z_ur+pt2+gz] for sx in(-1,1) for sy in(-1,1)]
    pts+=[[sx*rl/2, 0, z_top] for sx in (-1,1)]
    uroof=U([B(ew2-2*tw,ed2-2*tw,pt2,0,0,z_ur), trimesh.convex.convex_hull(np.array(pts))])
    sink=P['ridge_w']*slope/2+0.3                                  # 능선 폭이 ridge_w 가 되는 깊이
    ridge=B(rl,P['ridge_w'],P['ridge_h']+sink,0,0,z_top-sink)
    chwidu=[B(P['ridge_w'],P['ridge_w'],P['chwidu']+sink,sx*(rl/2-P['ridge_w']/2),0,z_top-sink) for sx in(-1,1)]
    uroof=U([uroof,ridge]+chwidu)
    uroof=D(uroof, D(B(ubw-6+2*clr,ubd-6+2*clr,2.8,0,0,z_ur-0.5), B(ubw-12,ubd-12,5,0,0,z_ur-1)))   # 테두리 홈 o 2.7~6.0
    parts['upper_roof']=(uroof,5,False)
    parts['upper_roof_trim']=(ring(ew2,ed2,pt2,z_ur,tw),3,False)
    info=dict(z_platform=zp, z_pocket_floor=z_pf, opening=(op_w,op_d), z_lower_body=zb, z_lower_window=(z_lat1,z_lint1), z_band1=z_band1, z_lower_roof=z_lr,
              z_upper_body=z_ub, z_upper_window=(z_lat2,z_lint2), z_band2=z_band2, z_upper_roof=z_ur, z_top=z_top+P['ridge_h'], gable_depth=gd, slope_deg=float(np.degrees(np.arctan(slope))))
    return parts, info
if __name__=='__main__':
    parts,info=build(); os.makedirs(MODELS,exist_ok=True)
    print('높이표',{k:(round(v,2) if not isinstance(v,tuple) else tuple(round(x,2) for x in v)) for k,v in info.items()})
    for n,(m,slot,flip) in parts.items():
        print(f'{n:18s} slot{slot} flip={flip} is_volume={m.is_volume} bodies={len(m.split())} faces={len(m.faces):,} size={np.round(m.bounds[1]-m.bounds[0],1).tolist()}')
        m.export(os.path.join(MODELS,f'{n}.stl'))
    pickle.dump({'parts':{n:(m,s,f) for n,(m,s,f) in parts.items()},'info':info,'P':P}, open(os.path.join(MODELS,'parts_v1.pkl'),'wb'))
    sys.path.insert(0, os.path.join(HERE,'..','..','..','tools')); from efc import pre_expand_first_layer, pre_expand_first_layer_group
    PR=os.path.join(MODELS,'print'); os.makedirs(PR,exist_ok=True)                     # 출력 방향: 띠는 뒤집고, 바닥 z=0, 첫 층 +0.15(EFC 0.15 선반영)
    pr={}
    for n,(m,slot,flip) in parts.items():
        q=m.copy()
        if flip: q.apply_transform(R(np.pi,[1,0,0]))
        q.apply_translation([0,0,-q.bounds[0,2]]); pr[n]=q
    for grp in (('lower_roof','lower_roof_trim'),('upper_roof','upper_roof_trim')):          # 지붕+흰 띠: 한 덩어리로 바깥만
        ex=pre_expand_first_layer_group([pr[g] for g in grp], 0.15)
        for g,q in zip(grp,ex): pr[g]=q
    for n,q in pr.items():
        if 'roof' not in n: q=pre_expand_first_layer(q, 0.15)
        q.export(os.path.join(PR,f'{n}.stl'))
    print('saved', MODELS)
