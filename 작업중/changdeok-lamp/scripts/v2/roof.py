"""지붕 모듈: 서까래 끝(흰 빗)·연함 띠·평고대(흰 선)·기와 골·막새·마루·취두·앙곡 모서리·합각(상층)·소핏 서까래 홈.
조립 좌표(처마판 바닥 = z0). 출력 방향 = 그대로(처마 아래). 파트: tile(기와색), soffit(갈색), white(흰), red(합각, 상층만)."""
import numpy as np, trimesh
from shapely.geometry import Polygon
from geo import B, CYL, U, D, I, HULL, EXT, segbox, centers
import params as P
DEBUG=False
def _prism(poly_xy, z0=-10, z1=300): return EXT(Polygon(poly_xy), z1-z0, z0)
def roof(EX, EY, z0, kind, top=None, light_hole=None, groove=None, lip=None, rise=None, gable=None):
    """kind 'lower': top=(TX,TY,z_top) 사다리꼴 지붕(가운데 평탄면). kind 'upper': gable=(ridge_len, gz, z_ridge).
    light_hole=(w,d) 가운데 관통, groove=(outer_w,outer_d,wall+clr,depth) 하부 림 홈, lip=(w,d,wall,h) 평탄면 위 턱."""
    S=P.SOFFIT_T; LT=P.LINE_T; z_line=z0+S; z_t=z_line+LT              # 기와 시작 높이
    # ---- 소핏(갈색): 판 − 바깥 1.0 띠(z0..z0+1.0, 서까래 끝 자리) ----
    soffit=B(EX,EY,S,0,0,z0)
    soffit=D(soffit, D(B(EX+1,EY+1,S+1.0,0,0,z0-0.5), B(EX-2,EY-2,S+3,0,0,z0-1)))   # 바깥 1.0 띠 전체 비움: 흰 서까래 끝 + 흰 띠 자리
    # 소핏 바닥 서까래 홈(1.0 폭·0.8 깊이, 변마다 안쪽 25 mm, 모서리 사각은 대각)
    gro=[]; L=25.0; pitch=P.TOOTH_PITCH
    for x in centers(-EX/2+L, EX/2-L, pitch): gro.append(B(1.0, L, 0.8, x, -EY/2+1.5+L/2, z0-0.1)); gro.append(B(1.0, L, 0.8, x, EY/2-1.5-L/2, z0-0.1))
    for y in centers(-EY/2+L, EY/2-L, pitch): gro.append(B(L, 1.0, 0.8, -EX/2+1.5+L/2, y, z0-0.1)); gro.append(B(L, 1.0, 0.8, EX/2-1.5-L/2, y, z0-0.1))
    gro_m=U(gro); gro_m=I(gro_m, B(EX-2.6,EY-2.6,3,0,0,z0-1))   # 바깥 띠는 건드리지 않음
    soffit=D(soffit, gro_m)
    # ---- 흰색: 서까래 끝 빗(1.0 각, 피치) + 평고대 선(바깥 1.0 띠, z_line..z_t) ----
    teeth=[]
    for x in centers(-EX/2+1.0, EX/2-1.0, pitch): teeth.append(B(P.TOOTH,1.0,P.TOOTH,x,-EY/2+0.5,z0)); teeth.append(B(P.TOOTH,1.0,P.TOOTH,x,EY/2-0.5,z0))
    for y in centers(-EY/2+2.5, EY/2-2.5, pitch): teeth.append(B(1.0,P.TOOTH,P.TOOTH,-EX/2+0.5,y,z0)); teeth.append(B(1.0,P.TOOTH,P.TOOTH,EX/2-0.5,y,z0))
    white=U(teeth+[D(B(EX,EY,z_t-(z0+P.TOOTH),0,0,z0+P.TOOTH), B(EX-2,EY-2,z_t-z0+2,0,0,z0-1))])   # 서까래 끝 빗 + 흰 띠(z0+1.0~z_t) 한 몸
    # ---- 기와 몸체(검정) ----
    if kind=='lower':
        TX,TY,z_top=top
        body=U([B(EX-2,EY-2,LT+0.2,0,0,z_line), HULL([[sx*(EX/2-1.0),sy*(EY/2-1.0),z_t] for sx in(-1,1) for sy in(-1,1)]+[[sx*TX/2,sy*TY/2,z_top] for sx in(-1,1) for sy in(-1,1)])])
        planes={'f':[(-EX/2,-EY/2),(EX/2,-EY/2),(TX/2,-TY/2),(-TX/2,-TY/2)], 'b':[(-EX/2,EY/2),(EX/2,EY/2),(TX/2,TY/2),(-TX/2,TY/2)],
                'l':[(-EX/2,-EY/2),(-EX/2,EY/2),(-TX/2,TY/2),(-TX/2,-TY/2)], 'r':[(EX/2,-EY/2),(EX/2,EY/2),(TX/2,TY/2),(TX/2,-TY/2)]}
        slope_f=np.arctan2(z_top-z_t, (EY-TY)/2); slope_s=np.arctan2(z_top-z_t, (EX-TX)/2)
        top_f=(TY/2, z_top); top_s=(TX/2, z_top); hips=[((sx*EX/2,sy*EY/2,z_t),(sx*TX/2,sy*TY/2,z_top)) for sx in(-1,1) for sy in(-1,1)]
    else:
        RL,GZ,z_ridge=gable; slope_f=np.arctan2(z_ridge-z_t, EY/2); GD=EY-2*GZ/np.tan(slope_f)
        pts=[[sx*(EX/2-1.0),sy*(EY/2-1.0),z_t] for sx in(-1,1) for sy in(-1,1)]+[[sx*RL/2,sy*GD/2,z_t+GZ] for sx in(-1,1) for sy in(-1,1)]+[[sx*RL/2,0,z_ridge] for sx in(-1,1)]
        body=U([B(EX-2,EY-2,LT+0.2,0,0,z_line), HULL(pts)])
        planes={'f':[(-EX/2,-EY/2),(EX/2,-EY/2),(RL/2,-GD/2),(RL/2,0),(-RL/2,0),(-RL/2,-GD/2)], 'b':[(-EX/2,EY/2),(EX/2,EY/2),(RL/2,GD/2),(RL/2,0),(-RL/2,0),(-RL/2,GD/2)],
                'l':[(-EX/2,-EY/2),(-EX/2,EY/2),(-RL/2,GD/2),(-RL/2,-GD/2)], 'r':[(EX/2,-EY/2),(EX/2,EY/2),(RL/2,GD/2),(RL/2,-GD/2)]}
        slope_s=np.arctan2(GZ, (EX-RL)/2); top_f=(0.0, z_ridge); top_s=(RL/2, z_t+GZ)
        hips=[((sx*EX/2,sy*EY/2,z_t),(sx*RL/2,sy*GD/2,z_t+GZ)) for sx in(-1,1) for sy in(-1,1)]
    # 앙곡: 모서리 쐐기(기와 시작 모서리를 CORNER_RISE 들어 올림)
    wedges=[]
    fx=P.CORNER_FRAC*EX/2; fy=P.CORNER_FRAC*EY/2
    for sx in(-1,1):
        for sy in(-1,1):
            cx,cy=sx*EX/2,sy*EY/2; h0,h1=[h for h in hips if h[0][0]==cx and h[0][1]==cy][0]
            hp=np.array(h0)+(np.array(h1)-np.array(h0))*0.35
            cx,cy=sx*(EX/2-1.0),sy*(EY/2-1.0)
            wedges.append(HULL([(cx-sx*fx,cy,z_t-0.3),(cx,cy,z_t-0.3),(cx,cy,z_t+P.CORNER_RISE),(cx,cy-sy*fy,z_t-0.3),hp-np.array([0,0,0.3]),(hp[0],hp[1],hp[2]+P.CORNER_RISE*0.3)]))
    body=U([body]+wedges)
    # 기와 골 + 막새: 면마다 경사 방향 각재, 면 프리즘으로 자름
    ribs=[]; mk=[]
    def rib_line(p0,p1):
        r=segbox(p0,p1,P.RIB_W,2*P.RIB_H); return r
    for side,poly in planes.items():
        prism=_prism(poly, z0-5, 400)
        rs=[]; ms=[]
        if side in ('f','b'):
            sy=-1 if side=='f' else 1
            for x in centers(-EX/2+1.2, EX/2-1.2, P.RIB_PITCH_MM):
                p0=(x, sy*(EY/2-1.0), z_t); p1=(x, sy*top_f[0], top_f[1]+0.4)
                rs.append(rib_line(p0,p1)); c=CYL(P.MAKSAE_D,1.0,0,0,0,sec=20); c.apply_transform(trimesh.transformations.rotation_matrix(-sy*(np.pi/2-slope_f),[1,0,0])); c.apply_translation([x, sy*(EY/2-1.5), z_t+0.7]); ms.append(c)
        else:
            sx=-1 if side=='l' else 1
            for y in centers(-EY/2+1.2, EY/2-1.2, P.RIB_PITCH_MM):
                p0=(sx*(EX/2-1.0), y, z_t); p1=(sx*top_s[0], y, top_s[1]+0.4)
                rs.append(rib_line(p0,p1)); c=CYL(P.MAKSAE_D,1.0,0,0,0,sec=20); c.apply_transform(trimesh.transformations.rotation_matrix(sx*(np.pi/2-slope_s),[0,1,0])); c.apply_translation([sx*(EX/2-1.5), y, z_t+0.7]); ms.append(c)
        rib_u=U(rs+ms); n0=len(rib_u.faces); rib_u=I(rib_u, prism); ribs.append(rib_u)
        if DEBUG: print('  plane',side,'ribs',len(rs),'maksae',len(ms),'union faces',n0,'clipped',len(rib_u.faces), rib_u.is_volume)
    ribs_u=U(ribs); n1=len(ribs_u.faces); ribs_u=D(ribs_u, B(EX+10,EY+10,20,0,0,z_t-20))   # 기와 시작 아래로 나온 골·막새 끝 제거
    n2=len(ribs_u.faces)
    if DEBUG: print('  ribs all', n1, 'after cut', n2, 'after clip', len(ribs_u.faces), 'body before', len(body.faces))
    body=U([body, ribs_u])
    if DEBUG: print('  body after ribs', len(body.faces), body.is_volume)
    # 마루: 추녀마루(힙)·용마루·내림마루 = 흰 양성(white ridge), 취두 = 기와색
    bars=[]; chwidu=[]
    for h0,h1 in hips:
        a_=np.array(h0,float); b_=np.array(h1,float); a_[2]+=P.CORNER_RISE*0.9; bars.append(segbox(a_,b_,3.0,3.0))
    red=None
    if kind=='upper':
        RL,GZ,z_ridge=gable
        bars.append(B(RL, 4.0, 5.0+4.0, 0,0, z_ridge-4.0))                               # 용마루 흰 양성(높이 5, 4 mm 가라앉힘)
        for sx in(-1,1):
            chwidu.append(B(5.0,5.0,11.0+4.0, sx*(RL/2-2.5), 0, z_ridge-4.0))             # 취두
            for sy in (-1,1): bars.append(segbox((sx*RL/2, 0, z_ridge), (sx*RL/2, sy*GD/2, z_t+GZ), 3.0, 3.0))   # 내림마루
            tri=[(sy*GD/2, z_t+GZ-1.0) for sy in (-1,1)]+[(0.0, z_ridge-1.0)]
            plate=EXT(Polygon(tri), 1.0, 0); plate.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0])); plate.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,0,1]))
            plate.apply_translation([sx*RL/2 + (0.0 if sx>0 else -1.0) , 0, 0])
            red=plate if red is None else U([red,plate])
    if chwidu: body=U([body]+chwidu)
    ridge_white=U(bars)
    if red is not None: ridge_white=D(ridge_white, red)          # 합각 널과 겹침 제거
    ridge_white=D(ridge_white, B(EX+20,EY+20,30,0,0,z_t-30))     # 기와 시작 아래 제거
    # 가운데 빛 구멍, 하부 홈, 평탄면 턱
    if light_hole: body=D(body, B(light_hole[0],light_hole[1],500,0,0,z0-1)); soffit=D(soffit, B(light_hole[0],light_hole[1],500,0,0,z0-1)); ridge_white=D(ridge_white, B(light_hole[0],light_hole[1],500,0,0,z0-1))
    if groove:
        gw,gd,gwall,gdep=groove; gcut=D(B(gw,gd,gdep,0,0,z0-0.5), B(gw-2*gwall,gd-2*gwall,gdep+2,0,0,z0-1)); body=D(body,gcut); soffit=D(soffit,gcut)
    if lip:
        lw,ld,lwall,lh=lip; body=U([body, D(B(lw,ld,lh,0,0,top[2]-0.01), B(lw-2*lwall,ld-2*lwall,lh+2,0,0,top[2]-1))])
    def clean(m):
        bs=[b for b in m.split() if abs(b.volume)>1.0]
        return bs[0] if len(bs)==1 else (trimesh.util.concatenate(bs) if bs else m)
    body=D(body, ridge_white)
    out={'tile':clean(body),'soffit':soffit,'white':white,'ridge':ridge_white}
    if red is not None: out['gable']=red
    # ---- 앙곡(모서리 들림) + 지붕면 오목 곡: 잘게 나눈 뒤 정점 z 변형. 바닥(z0~z0+1) 은 그대로 → 베드 안착 유지 ----
    hx,hy=EX/2,EY/2
    if kind=='lower': z_peak=top[2]; TXh,TYh=top[0]/2,top[1]/2; sag=P.SAG_LOWER
    else: z_peak=gable[2]; TXh=TYh=None; sag=P.SAG_UPPER
    def warp(m):
        v,f=trimesh.remesh.subdivide_to_size(m.vertices, m.faces, max_edge=P.WARP_EDGE, max_iter=12)
        x,y,z=v[:,0],v[:,1],v[:,2]
        w=(np.abs(x)/hx)**3*(np.abs(y)/hy)**3
        if TXh is not None: w=w*np.clip(np.maximum(np.abs(x)-TXh, np.abs(y)-TYh)/8.0, 0, 1)
        blend=np.clip((z-(z0+P.TOOTH))/(S-P.TOOTH), 0, 1)
        t=np.clip((z-z_t)/(z_peak-z_t), 0, 1)
        v=v.copy(); v[:,2]=z+P.EAVE_RISE*w*blend-sag*np.sin(np.pi*t)
        q=trimesh.Trimesh(v,f,process=False); q.merge_vertices(); return q
    out={k:warp(m) for k,m in out.items()}
    return out
