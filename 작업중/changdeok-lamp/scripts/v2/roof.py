"""지붕 모듈(분리형) — 부품마다 한 색, 바닥면 평평, 끼워서 조립.
  soffit  처마밑(갈색): z0~z0+S. 바깥면 = 서까래 두 줄(겹처마), 밑면 = 서까래 홈. 밑면 모서리가 들림(앙곡). **뒤집어 출력**(윗면 평평 → 베드).
  ring    흰 처마선 테(흰색): z0+S~z0+S+LT, 바깥 RING_BAND 폭의 평판 테. 바깥 1 mm 만 보인다. 납작하게 출력.
  tile    기와(검정): 밑면 평평(z_w). 골·막새·취두, 앙곡(윗면만 들림)·지붕면 오목 곡. 마루 자리 홈·합각 포켓. 처마가 아래로 출력.
  pieces  흰 마루(추녀마루·용마루·내림마루): 기와 홈에 끼움(FIT/면). 옆으로 눕혀 출력. 갈색 합각 널: 포켓에 끼움, 납작하게 출력.
  정렬: 처마밑·흰 테·기와를 관통하는 Ø2.0 구멍 4개(변 가운데) + 1.75 필라멘트 핀.
반환: list of dict(name, mesh(조립 좌표), color, print=('flip'|'asis'|('lay', u)))."""
import numpy as np, trimesh
from shapely.geometry import Polygon
from geo import B, CYL, U, D, I, HULL, EXT, segbox, centers
import params as P
DEBUG=False
def _prism(poly_xy, z0=-10, z1=300): return EXT(Polygon(poly_xy), z1-z0, z0)
def _refine_warp(m, f, edge):
    import manifold3d as mf
    mm=mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices,np.float32), tri_verts=np.asarray(m.faces,np.uint32)))
    mm=mm.refine_to_length(edge).warp_batch(lambda v: f(np.array(v,float)))
    g=mm.to_mesh(); return trimesh.Trimesh(np.asarray(g.vert_properties)[:,:3], np.asarray(g.tri_verts), process=False)
def _bar(pts, u, w, h):
    """중심선 점들(N,3)을 따라가는 각재 — 단면 사각형 4점을 이어 붙인 스윕(불리언 없음 → 구조적으로 닫힘, 퇴화 모서리 없음).
    u = 단면 가로 방향(수평 단위벡터, 모든 단면 공통)."""
    pts=np.asarray(pts,float); u=np.asarray(u,float); V=[]
    s0=(pts@u).min()                                    # −u 쪽 옆면을 한 평면(u·p = s0 − w/2)에 맞춤 → 눕혀 출력할 때 바닥 전면 접지
    for i in range(len(pts)):
        t=pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]; t/=np.linalg.norm(t); v=np.cross(u,t); v/=np.linalg.norm(v)
        if v[2]<0: v=-v
        p=pts[i]; pin=p-u*((p@u)-s0)                     # 이 단면의 −u 면 기준점(평면 위)
        V+= [pin-u*w/2-v*h/2, p+u*w/2-v*h/2, p+u*w/2+v*h/2, pin-u*w/2+v*h/2]
    n=len(pts); F=[]
    for i in range(n-1):
        a=4*i; b=4*(i+1)
        for k in range(4):
            k2=(k+1)%4; F+= [[a+k, b+k, b+k2], [a+k, b+k2, a+k2]]
    F+= [[0,2,1],[0,3,2]]; L=4*(n-1); F+= [[L,L+1,L+2],[L,L+2,L+3]]
    m=trimesh.Trimesh(np.array(V),np.array(F),process=False)
    trimesh.repair.fix_normals(m)                       # 면 방향 통일(바깥 향함)
    return m
def roof(EX, EY, z0, kind, top=None, light_hole=None, groove=None, lip=None, gable=None, prefix='R_', under=None):
    S=P.SOFFIT_T; LT=P.LINE_T; TB=P.TILE_BASE; clr=P.CLR; pitch=P.TOOTH_PITCH
    z_s=z0+S; z_w=z_s+LT; z_t=z_w+TB
    hx,hy=EX/2,EY/2
    xs_e=centers(-EX/2+1.2, EX/2-1.2, pitch); ys_e=centers(-EY/2+1.2, EY/2-1.2, pitch)   # 서까래·수키와 공통 자리
    # ======================= 처마밑(갈색) =======================
    soffit=B(EX,EY,S,0,0,z0)
    if under:                                                                  # 처마밑 경사 쐐기: 평방 바깥(z_rt) → 처마 끝(z0), 공포 띠 바깥만
        uw,ud,z_rt,bw,bd=under
        rect=lambda w,d,z: [[sx*w/2,sy*d/2,z] for sx in(-1,1) for sy in(-1,1)]
        wedge=HULL(rect(uw,ud,z_rt)+rect(EX,EY,z0)+rect(uw,ud,z0+0.01)+rect(EX,EY,z0+0.01))
        soffit=U([soffit, D(wedge, B(bw+2*clr, bd+2*clr, 100, 0,0, z_rt-1))])
        # 서까래 홈: 경사면을 따라 띠 바깥 → 처마 끝(1.0 폭, 0.8 깊이)
        kx=(z0-z_rt)/((EX-uw)/2); ky=(z0-z_rt)/((EY-ud)/2); gro=[]
        for x in [c for c in xs_e if abs(c)<bw/2-3]:                               # 서까래 홈은 마구리와 같은 자리(같은 피치)
            for s in (-1,1): gro.append(segbox((x, s*(bd/2+clr+1.0), z_rt+(bd/2+clr+1.0-ud/2)*ky), (x, s*(EY/2-2.0), z0-2.0*ky), 1.0, 1.6))
        for y in [c for c in ys_e if abs(c)<bd/2-3]:
            for s in (-1,1): gro.append(segbox((s*(bw/2+clr+1.0), y, z_rt+(bw/2+clr+1.0-uw/2)*kx), (s*(EX/2-2.0), y, z0-2.0*kx), 1.0, 1.6))
        # 선자연(창경궁 SKP 평면): 모서리 구간 서까래는 공포 띠 모서리에서 부채꼴로 퍼져 처마 끝에 닿는다
        zsurf=lambda x,y: min(z0, max(z_rt+ky*(abs(y)-ud/2), z_rt+kx*(abs(x)-uw/2)))
        for sx in (-1,1):
            for sy in (-1,1):
                c0=np.array([sx*(bw/2+clr+1.5), sy*(bd/2+clr+1.5)])
                ends=[(x, sy*(EY/2-2.0)) for x in xs_e if bw/2-3<=abs(x)<=EX/2-3.0 and np.sign(x)==sx]+[(sx*(EX/2-2.0), y) for y in ys_e if bd/2-3<=abs(y)<=EY/2-3.0 and np.sign(y)==sy]
                for e in ends:
                    d=np.array(e)-c0; L=np.linalg.norm(d)
                    if L<4: continue
                    p0=c0+d*(1.0/L); p1=np.array(e)
                    gro.append(segbox((p0[0],p0[1],zsurf(*p0)), (p1[0],p1[1],zsurf(*p1)), 1.0, 1.6))
        soffit=D(soffit, U(gro))
    # 추녀 끝: 처마 모서리에서 대각으로 1.8 돌출하는 세로 각재(윗면 = 처마밑 윗면 = 출력 베드)
    for sx in (-1,1):
        for sy in (-1,1):
            dg=np.array([sx*hx, sy*hy]); dn=dg/np.linalg.norm(dg)
            pa=dg-dn*8.0; pb=dg+dn*P.CHUNYEO_OUT
            soffit=U([soffit, segbox((pa[0],pa[1],z0+1.0+(S-1.0)/2), (pb[0],pb[1],z0+1.0+(S-1.0)/2), P.CHUNYEO_W, S-1.0)])
    def rafter_end(c, n, zc):                                               # 둥근 서까래 마구리(SKP 처마 정면): 처마 면 c 에서 n 방향으로 0.6 돌출
        r=P.RAFTER_D/2; a=np.linspace(0,2*np.pi,16,endpoint=False); t=np.array([-n[1],n[0],0.0]); pts=[]
        for dep,dz in ((-0.4,P.RAFTER_RAMP/2),(P.RAFTER_OUT,-P.RAFTER_RAMP/2)):   # 안쪽 원은 위로, 바깥 원은 아래로 → 윗면 경사(뒤집어 출력 시 층당 ≤0.11)
            for q in a: pts.append(np.array(c)+n*dep+t*r*np.cos(q)+np.array([0,0,zc+dz+r*np.sin(q)]))
        return HULL(pts)
    zc_r=z0+0.4+P.RAFTER_D/2+P.RAFTER_RAMP/2                                   # 마구리 바깥 원 아래끝 z0+0.4, 안쪽 원 위끝 z0+4.4 (< 처마밑 두께 5)
    ends=[]
    for x in xs_e:
        if abs(x)>EX/2-2.5: continue
        for s in (-1,1): ends.append(rafter_end((x, s*EY/2, 0.0), np.array([0.0,s,0.0]), zc_r))
    for y in ys_e:
        if abs(y)>EY/2-2.5: continue
        for s in (-1,1): ends.append(rafter_end((s*EX/2, y, 0.0), np.array([s,0.0,0.0]), zc_r))
    soffit=U([soffit]+ends)
    # ======================= 흰 처마선 테 =======================
    ring=D(B(EX,EY,LT-0.3,0,0,z_s+0.15), B(EX-2*P.RING_BAND, EY-2*P.RING_BAND, LT+2, 0,0, z_s-1))   # 흰 테 0.7: 위아래 0.15 틈(휜 곡면 분할 차이 ≤0.1 흡수)
    # ======================= 기와 몸체(검정) =======================
    if kind=='lower':
        TX,TY,z_top=top
        hull=HULL([[sx*(EX/2-1.0),sy*(EY/2-1.0),z_t] for sx in(-1,1) for sy in(-1,1)]+[[sx*TX/2,sy*TY/2,z_top] for sx in(-1,1) for sy in(-1,1)])
        body=U([B(EX,EY,TB+0.2,0,0,z_w), hull])
        planes={'f':[(-EX/2,-EY/2),(EX/2,-EY/2),(TX/2,-TY/2),(-TX/2,-TY/2)], 'b':[(-EX/2,EY/2),(EX/2,EY/2),(TX/2,TY/2),(-TX/2,TY/2)],
                'l':[(-EX/2,-EY/2),(-EX/2,EY/2),(-TX/2,TY/2),(-TX/2,-TY/2)], 'r':[(EX/2,-EY/2),(EX/2,EY/2),(TX/2,TY/2),(TX/2,-TY/2)]}
        slope_f=np.arctan2(z_top-z_t, (EY-TY)/2); slope_s=np.arctan2(z_top-z_t, (EX-TX)/2)
        HIP=(TX/2, TY/2, z_top); top_f=(TY/2, z_top); top_s=(TX/2, z_top); z_peak=z_top; sag=P.SAG_LOWER
    else:
        RL,GZ,z_ridge=gable; slope_f=np.arctan2(z_ridge-z_t, EY/2); GD=EY-2*GZ/np.tan(slope_f)
        hip_part=HULL([[sx*(EX/2-1.0),sy*(EY/2-1.0),z_t] for sx in(-1,1) for sy in(-1,1)]+[[sx*RL/2,sy*GD/2,z_t+GZ] for sx in(-1,1) for sy in(-1,1)])
        gable_part=HULL([[sx*RL/2,sy*GD/2,z_t+GZ-0.01] for sx in(-1,1) for sy in(-1,1)]+[[sx*RL/2,0,z_ridge] for sx in(-1,1)])
        body=U([B(EX,EY,TB+0.2,0,0,z_w), hip_part, gable_part])
        planes={'f':[(-EX/2,-EY/2),(EX/2,-EY/2),(RL/2,-GD/2),(RL/2,0),(-RL/2,0),(-RL/2,-GD/2)], 'b':[(-EX/2,EY/2),(EX/2,EY/2),(RL/2,GD/2),(RL/2,0),(-RL/2,0),(-RL/2,GD/2)],
                'l':[(-EX/2,-EY/2),(-EX/2,EY/2),(-RL/2,GD/2),(-RL/2,-GD/2)], 'r':[(EX/2,-EY/2),(EX/2,EY/2),(RL/2,GD/2),(RL/2,-GD/2)]}
        slope_s=np.arctan2(GZ, (EX-RL)/2); top_f=(0.0, z_ridge); top_s=(RL/2, z_t+GZ)
        HIP=(RL/2, GD/2, z_t+GZ); z_peak=z_ridge; sag=P.SAG_UPPER
    hips=[((sx*(EX/2-1.0),sy*(EY/2-1.0),z_t),(sx*HIP[0],sy*HIP[1],HIP[2])) for sx in(-1,1) for sy in(-1,1)]
    # 기와 골 + 막새
    ribs=[]
    for side,poly in planes.items():
        prism=_prism(poly, z0-5, 400); rs=[]; ms=[]
        if side in ('f','b'):
            sy=-1 if side=='f' else 1
            for x in xs_e:
                p0=(x, sy*(EY/2-1.0), z_t)
                if abs(x)<=HIP[0]: p1=(x, sy*top_f[0], top_f[1]+0.4)
                else:
                    s=(EX/2-abs(x))/(EX/2-HIP[0]); p1=(x, sy*(EY/2-s*(EY/2-HIP[1])), z_t+s*(HIP[2]-z_t)+0.4)
                    if s<0.08: continue
                rs.append(segbox(p0,p1,P.RIB_W,2*P.RIB_H)); c=CYL(P.MAKSAE_D,1.0,0,0,0,sec=20); c.apply_transform(trimesh.transformations.rotation_matrix(-sy*(np.pi/2-slope_f),[1,0,0])); c.apply_translation([x, sy*(EY/2-1.5), z_t+0.7]); ms.append(c)
        else:
            sx=-1 if side=='l' else 1
            for y in ys_e:
                p0=(sx*(EX/2-1.0), y, z_t)
                if abs(y)<=HIP[1]: p1=(sx*top_s[0], y, top_s[1]+0.4)
                else:
                    s=(EY/2-abs(y))/(EY/2-HIP[1]); p1=(sx*(EX/2-s*(EX/2-HIP[0])), y, z_t+s*(HIP[2]-z_t)+0.4)
                    if s<0.08: continue
                rs.append(segbox(p0,p1,P.RIB_W,2*P.RIB_H)); c=CYL(P.MAKSAE_D,1.0,0,0,0,sec=20); c.apply_transform(trimesh.transformations.rotation_matrix(sx*(np.pi/2-slope_s),[0,1,0])); c.apply_translation([sx*(EX/2-1.5), y, z_t+0.7]); ms.append(c)
        ribs.append(I(U(rs+ms), prism))
    ribs_u=D(U(ribs), B(EX+10,EY+10,20,0,0,z_t-20))
    body=U([body, ribs_u])
    if kind=='upper':
        # 취두(정면 스캔: 용마루 위 ≈4.8 솟은 기둥 + 안쪽으로 굽은 머리). 바깥 끝 u=0, 안쪽 +u. 머리 밑면 경사 2.8/1.6=1.75(층당 0.114)
        prof=[(0,-4.0),(5.0,-4.0),(5.0,7.0),(6.6,9.8),(6.9,10.4),(6.5,11.0),(5.5,11.4),(3.5,11.5),(1.5,11.3),(0.3,10.8),(0,10.2)]   # 둥근 머리
        chw=[]
        for sx in (-1,1):
            pl=Polygon([(sx*(RL/2-u), z_ridge+zz) for u,zz in prof]).buffer(0)
            m=EXT(pl, 4.0, 0); m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0])); m.apply_translation([0, 2.0, 0]); chw.append(m)
        body=U([body]+chw)
    if light_hole: body=D(body, B(light_hole[0],light_hole[1],500,0,0,z0-1)); soffit=D(soffit, B(light_hole[0],light_hole[1],500,0,0,z0-1))
    if groove:
        gw,gd,gwall,gdep=groove; soffit=D(soffit, D(B(gw,gd,gdep,0,0,z0-0.5), B(gw-2*gwall,gd-2*gwall,gdep+2,0,0,z0-1)))
    if lip:
        lw,ld,lwall,lh=lip; body=U([body, D(B(lw,ld,lh,0,0,top[2]-0.01), B(lw-2*lwall,ld-2*lwall,lh+2,0,0,top[2]-1))])
    # ======================= 앙곡·오목 곡 =======================
    TXh,TYh=(top[0]/2,top[1]/2) if kind=='lower' else (None,None)
    def wcorner(x,y):
        w=(np.abs(x)/hx)**3*(np.abs(y)/hy)**3
        if TXh is not None: w=w*np.clip(np.maximum(np.abs(x)-TXh, np.abs(y)-TYh)/8.0, 0, 1)
        return w
    bw_,bd_=(under[3],under[4]) if under else (EX-40,EY-40)
    def plan(v):                         # 안허리곡: 변 전체가 U자(가운데 0 → 모서리 비율×반길이, 지수 2.7), 공포 띠 안쪽은 그대로(끼움 유지)
        x,y=v[:,0].copy(),v[:,1].copy(); m=np.clip(np.maximum(np.abs(x)-bw_/2, np.abs(y)-bd_/2)/6.0, 0, 1)
        if TXh is not None: m=m*np.clip(np.maximum(np.abs(x)-TXh, np.abs(y)-TYh)/8.0, 0, 1)
        Ax,Ay,pp=P.PLAN_CURVE_RATIO*hy, P.PLAN_CURVE_RATIO*hx, P.PLAN_CURVE_P      # 옆변은 옆변 반길이, 앞변은 앞변 반길이 비율
        v[:,0]=x+np.sign(x)*Ax*(np.abs(x)/hx)**2*np.clip(np.abs(y)/hy,0,1)**pp*m
        v[:,1]=y+np.sign(y)*Ay*(np.abs(y)/hy)**2*np.clip(np.abs(x)/hx,0,1)**pp*m
        return v
    RB=P.RING_BAND
    def Lf(x,y):                         # 처마선 들림: 변 반길이 55 % 부터 모서리 3.0 (두 변 곱 → 모서리에서만)
        f=lambda t: np.clip((t-P.RISE_T0)/(1-P.RISE_T0),0,1)**2
        w=P.EAVE_RISE*f(np.abs(x)/hx)*f(np.abs(y)/hy)
        if TXh is not None: w=w*np.clip(np.maximum(np.abs(x)-TXh, np.abs(y)-TYh)/8.0, 0, 1)   # 하층 지붕 윗면(상층 받침)은 평평
        return w
    def ramp(x,y):                       # 흰 테 띠(바깥 10) 안에서 1, 안쪽 6 mm 에 걸쳐 0 — 기와 밑면이 띠 위에서만 들림
        return np.clip((np.maximum(np.abs(x)-(hx-RB), np.abs(y)-(hy-RB))+6.0)/6.0, 0, 1)
    def f_tile(v):                       # 기와: 처마 띠는 통째로 Lf 만큼(밑면 포함), 안쪽은 밑면 그대로·윗면만 + 오목 곡 + 안허리곡
        x,y,z=v[:,0].copy(),v[:,1].copy(),v[:,2].copy(); blend=np.clip((z-z_w)/TB,0,1); t=np.clip((z-z_t)/(z_peak-z_t),0,1); rp=ramp(x,y)
        v[:,2]=z+Lf(x,y)*(rp+(1-rp)*blend)-sag*np.sin(np.pi*t); return plan(v)
    def f_ring(v):                       # 흰 테(조립): 들린 처마밑 위로 Lf 만큼 휨. 출력은 평평한 판(두께 1.0, 휨 변형률 ≈0.25 %)
        v[:,2]=v[:,2]+Lf(v[:,0],v[:,1]); return plan(v)
    def f_soffit(v):                     # 처마밑: 처마 띠는 통째로 Lf 만큼 들림(윗면 포함 — 정방향 출력, 밑면 서포트) + 밑면 추가 들림 + 안허리곡
        x,y,z=v[:,0].copy(),v[:,1].copy(),v[:,2].copy(); k=np.clip(1-(z-z0)/S,0,1)
        v[:,2]=z+P.SOFFIT_RISE*wcorner(x,y)*k+Lf(x,y)*ramp(x,y); return plan(v)
    body=_refine_warp(body, f_tile, P.WARP_EDGE)
    soffit=_refine_warp(soffit, f_soffit, P.WARP_EDGE)
    ring_print=_refine_warp(ring, plan, P.WARP_EDGE)
    ring=_refine_warp(ring, f_ring, 3.0)
    # (갈색 쐐기는 쓰지 않음: 사용자 결정 — 처마밑 자체를 들어 올리고 정방향 출력)
    # ======================= 흰 마루 부품 + 홈 =======================
    pieces=[]; grooves=[]
    def warped_line(a, b, n=14):
        pts=np.array([np.array(a)+(np.array(b)-np.array(a))*s for s in np.linspace(0,1,n)],float); return f_tile(pts.copy())
    def add_bar(name, a, b, w, h, dz=0.0):
        pts=warped_line(a,b); pts[:,2]+=dz
        d=np.array(b,float)-np.array(a,float); d[2]=0; d/=np.linalg.norm(d); u=np.array([-d[1],d[0],0.0])
        bar=_bar(pts,u,w,h); cut=_bar(pts,u,w+2*P.FIT,h+2*P.FIT)
        pieces.append(dict(name=name, mesh=bar, color='white', print=('lay',-u))); grooves.append(cut)      # 평면으로 맞춘 −u 면이 베드
    k=0
    for (a,b) in hips:                                                        # 추녀마루: 모서리 1.5 안 ~ 위 끝 3 전
        a=np.array(a); b=np.array(b); L_=np.linalg.norm(b-a); a2=a+(b-a)*(1.5/L_); b2=b-(b-a)*(3.0/L_)
        k+=1; add_bar(f'{prefix}hip{k}', a2, b2, 3.0, 3.0, dz=1.2)          # 밑면이 기와 밑(흰 테 위)보다 0.3 위 — 처마 띠가 들려도 흰 테와 안 겹침
    gable_plates=[]
    if kind=='upper':
        xr=RL/2-5.2; xq=np.linspace(-xr,xr,41); lift=P.RIDGE_RISE*(xq/P.RIDGE_RISE_AT)**2      # 용마루 흰 양성: 밑면 평평, 윗면이 양 끝으로 휨(정면 스캔 2.2·(x/56)²)
        rpoly=Polygon(list(zip(xq, z_ridge+3.5+lift))+[(xr, z_ridge-2.5), (-xr, z_ridge-2.5)])
        def xz_plate(pl, w):
            m=EXT(pl, w, 0); m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0])); m.apply_translation([0, w/2, 0]); return m
        pieces.append(dict(name=f'{prefix}ridge', mesh=xz_plate(rpoly, 4.0), color='white', print=('lay',np.array([0,1.0,0]))))
        grooves.append(xz_plate(rpoly.buffer(P.FIT, join_style=2), 4.0+2*P.FIT))
        k=0
        for sx in (-1,1):
            for sy in (-1,1):
                a=(sx*RL/2, sy*3.5, z_ridge-3.5*(z_ridge-z_t-GZ)/(GD/2)); b=(sx*RL/2, sy*(GD/2-2.5), z_t+GZ+2.5*(z_ridge-z_t-GZ)/(GD/2))
                k+=1; add_bar(f'{prefix}desc{k}', a, b, 3.0, 3.0)
            # 합각 널(갈색, 따로 출력해 끼움): 내림마루 아래 삼각형, 두께 2.0(1.2 를 기와 포켓에 끼움)
            ys=np.linspace(-(GD/2-4.5), GD/2-4.5, 15); zs_top=z_ridge-(np.abs(ys)/(GD/2))*(z_ridge-z_t-GZ)-3.2
            edge=f_tile(np.column_stack([np.full_like(ys,sx*RL/2), ys, zs_top]))[:,2]
            zb=f_tile(np.array([[sx*RL/2, 0, z_t+GZ+1.8]]))[0,2]                 # 기와 골 끝(+1.0) 위로
            poly=Polygon([(ys[0],zb)]+list(zip(ys,edge))+[(ys[-1],zb)]).buffer(0)
            def plate(pl, th, x_in):
                m=EXT(pl, th, 0); m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0])); m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,0,1]))
                m.apply_translation([x_in,0,0]); return m
            th=P.GABLE_T; gi=P.GABLE_IN                                            # 두께 2.0 중 1.2 를 포켓에 끼움(바깥 0.8 보임)
            pl=plate(poly, th, sx*RL/2-gi if sx>0 else -RL/2-(th-gi))
            pk=plate(poly.buffer(P.FIT), gi+0.01, sx*RL/2-gi if sx>0 else -RL/2-0.01)
            pieces.append(dict(name=f'{prefix}gable{"R" if sx>0 else "L"}', mesh=pl, color='brown', print=('lay',np.array([1.0,0,0]))))
            grooves.append(pk)
    body=D(body, U(grooves))
    # ======================= 정렬 핀 구멍(변 가운데 4개) =======================
    holes=[]
    for (x,y) in ((0,-(EY/2-P.RING_BAND/2)),(0,EY/2-P.RING_BAND/2),(-(EX/2-P.RING_BAND/2),0),(EX/2-P.RING_BAND/2,0)):
        holes.append(CYL(P.DOWEL_D, P.DOWEL_DEPTH+LT+P.DOWEL_DEPTH, x, y, z_s-P.DOWEL_DEPTH, sec=24))
    hm=U(holes); soffit=D(soffit,hm); ring=D(ring,hm); body=D(body,hm)
    def clean(m):
        bs=[b for b in m.split() if abs(b.volume)>1.0]
        return bs[0] if len(bs)==1 else (trimesh.util.concatenate(bs) if bs else m)
    ring_print=D(ring_print,hm)
    out=[dict(name=f'{prefix}soffit', mesh=soffit, color='brown', print='asis'),
         dict(name=f'{prefix}eave_white', mesh=ring, color='white', print='asis', print_mesh=ring_print),
         dict(name=f'{prefix}tile', mesh=clean(body), color='tile', print='asis')]+pieces

    return out
