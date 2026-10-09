"""벽 판(2색, 눕혀 출력): 흰 바탕 0.6(빛 통과) + 갈색 부조(기둥 반원·창방·문선·창살·머름).
로컬 좌표: x = 벽 길이, y = 높이(0 = 벽 바닥), z = 안쪽면 0 → 바깥쪽 부조(+). 출력 방향 그대로(z 위).
"""
import numpy as np, trimesh
from shapely.geometry import box as sbox, LineString, Polygon
from shapely.ops import unary_union
from shapely.affinity import rotate
from geo import B, CYL, U, D, I, EXT
import params as P
BASE=P.WALL_BASE
def _lattice_vertical(x0,y0,x1,y1,pitch=2.0,w=0.8,rails=(0.25,0.5,0.75),rail_w=0.8):
    """띠살: 세로살 + 가로살(비율 위치). 창 개구(x0,y0)-(x1,y1) 안."""
    shapes=[]
    xs=np.arange(x0+pitch, x1-w/2, pitch)
    for x in xs: shapes.append(sbox(x-w/2,y0,x+w/2,y1))
    for f in rails:
        y=y0+(y1-y0)*f; shapes.append(sbox(x0,y-rail_w/2,x1,y+rail_w/2))
    return unary_union(shapes)
def _lattice_diag(x0,y0,x1,y1,pitch=2.4,w=0.8):
    """빗살: ±45° 격자, 개구 안으로 자름"""
    win=sbox(x0,y0,x1,y1); cx,cy=(x0+x1)/2,(y0+y1)/2; L=max(x1-x0,y1-y0)*2
    shapes=[]
    for ang in (45,-45):
        for k in np.arange(-L, L, pitch):
            seg=sbox(cx-L, cy+k-w/2, cx+L, cy+k+w/2); shapes.append(rotate(seg, ang, origin=(cx,cy)))
    return unary_union(shapes).intersection(win)
def wall(length, height, col_xs, col_d, beam_t, doors_per_bay=4, zone=None, kind='lower'):
    """zone: dict(sill=(y0,y1), door=(y0,y1), transom=(y0,y1), beam=(y0,y1)) — 높이 구간. 반환 (white_mesh, brown_mesh) 로컬 좌표."""
    z=zone; white=B(length, height, BASE, length/2, height/2, 0)
    brown=[]
    frame_w=1.0
    # 기둥: 반원(지름 col_d) — 바탕 바깥쪽(z ≥ BASE)만
    for x in col_xs:
        c=CYL(col_d, z['beam'][0], x, 0, 0, sec=40); c.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0]))   # 축을 y 방향으로
        c.apply_translation([0,0,BASE]); c=I(c, B(length+10, height+10, col_d, length/2, height/2, BASE)); brown.append(c)
    # 창방(위 가로대)
    y0,y1=z['beam']; brown.append(B(length, y1-y0, 2.0, length/2, (y0+y1)/2, BASE))
    # 칸마다: 머름(궁판) / 문(띠살) / 교창(빗살) / 인방
    bays=list(zip(col_xs[:-1], col_xs[1:]))
    rel_frames=[]; rel_lat=[]; rel_panel=[]
    for a,b in bays:
        lo,hi=a+col_d/2-0.3, b-col_d/2+0.3                      # 기둥 안으로 0.3 겹침
        if 'sill' in z:
            s0,s1=z['sill']; rel_panel.append(sbox(lo,s0,hi,s1))                       # 궁판 바탕(0.8)
            n=doors_per_bay; w=(hi-lo)/n
            for k in range(n+1): rel_frames.append(sbox(lo+k*w-frame_w/2, s0, lo+k*w+frame_w/2, s1))   # 궁판 세로 테
            rel_frames.append(sbox(lo, s1-1.2, hi, s1))                                  # 머름 가로대
        if 'door' in z:
            d0,d1=z['door']; n=doors_per_bay; w=(hi-lo)/n
            rel_frames.append(sbox(lo,d0,hi,d0+frame_w)); rel_frames.append(sbox(lo,d1-frame_w,hi,d1))
            for k in range(n+1): rel_frames.append(sbox(lo+k*w-frame_w/2, d0, lo+k*w+frame_w/2, d1))
            for k in range(n): rel_lat.append(_lattice_vertical(lo+k*w+frame_w/2, d0+frame_w, lo+(k+1)*w-frame_w/2, d1-frame_w))
        if 'transom' in z:
            t0,t1=z['transom']; rel_frames.append(sbox(lo,t0,hi,t0+frame_w)); rel_frames.append(sbox(lo,t1-frame_w,hi,t1))
            if kind=='upper':
                n=2; w=(hi-lo)/n
                for k in range(n+1): rel_frames.append(sbox(lo+k*w-frame_w/2, t0, lo+k*w+frame_w/2, t1))
                for k in range(n): rel_lat.append(_lattice_diag(lo+k*w+frame_w/2, t0+frame_w, lo+(k+1)*w-frame_w/2, t1-frame_w))
            else:
                rel_lat.append(_lattice_diag(lo+frame_w, t0+frame_w, hi-frame_w, t1-frame_w))
        if 'panel' in z:                                                                # 상층 판벽
            p0,p1=z['panel']; rel_panel.append(sbox(lo,p0,hi,p1))
            for k in range(1,4): xx=lo+(hi-lo)*k/4; rel_frames.append(sbox(xx-frame_w/2,p0,xx+frame_w/2,p1))
    if rel_panel: brown.append(EXT(unary_union(rel_panel), 0.8, BASE))
    if rel_lat: brown.append(EXT(unary_union(rel_lat), 0.6, BASE))
    if rel_frames: brown.append(EXT(unary_union(rel_frames), 1.0, BASE))
    # 인방(창 위~창방 아래 띠)
    if 'lintel' in z:
        l0,l1=z['lintel']; brown.append(B(length, l1-l0, 1.0, length/2, (l0+l1)/2, BASE))
    return white, U(brown)
def lower_zone():
    H=P.Z_LOWER_WALL_TOP
    return dict(sill=(0.0,6.7), door=(6.7,24.0), transom=(24.0,29.3), lintel=(29.3,H), beam=(H,H+P.LOWER_BEAM))
def upper_zone():
    H=11.0
    return dict(panel=(0.0,3.0), transom=(3.0,H), beam=(H,H+P.LOWER_BEAM))
def lower_walls():
    """4벽: 로컬 메시 + 월드 변환. 반환 dict name -> (white, brown, M4x4)"""
    K=P.K; bx=np.cumsum([0]+P.BAYS_X)*K; by=np.cumsum([0]+P.BAYS_Y)*K
    Lx=P.SPAN_X+P.COL_D; Ly=P.SPAN_Y-2*BASE
    zone=lower_zone(); H=P.Z_LOWER_WALL_TOP+P.LOWER_BEAM
    out={}
    wf,bf=wall(Lx,H,[P.COL_D/2+x for x in bx],P.COL_D,P.LOWER_BEAM,4,zone,'lower')
    wb,bb=wall(Lx,H,[P.COL_D/2+x for x in bx],P.COL_D,P.LOWER_BEAM,4,zone,'lower')
    ws,bs=wall(Ly,H,[x-BASE for x in by[1:-1]],P.COL_D,P.LOWER_BEAM,3,zone,'lower')
    ws2,bs2=wall(Ly,H,[x-BASE for x in by[1:-1]],P.COL_D,P.LOWER_BEAM,3,zone,'lower')
    out['wall_front']=(wf,bf,'front'); out['wall_back']=(wb,bb,'back'); out['wall_left']=(ws,bs,'left'); out['wall_right']=(ws2,bs2,'right')
    return out, Lx, Ly, H
def upper_walls():
    K=P.K; ux0=-P.USPAN_X/2; n=5; ubays=np.linspace(0,P.USPAN_X,6)       # 상층 정면 5칸 균등(실측 없음, 추정)
    uby=np.linspace(0,P.USPAN_Y,4)                                        # 측면 3칸
    Lx=P.USPAN_X+P.UCOL_D; Ly=P.USPAN_Y-2*BASE; zone=upper_zone(); H=11.0+P.LOWER_BEAM
    out={}
    wf,bf=wall(Lx,H,[P.UCOL_D/2+x for x in ubays],P.UCOL_D,P.LOWER_BEAM,2,zone,'upper')
    wb,bb=wall(Lx,H,[P.UCOL_D/2+x for x in ubays],P.UCOL_D,P.LOWER_BEAM,2,zone,'upper')
    ws,bs=wall(Ly,H,[x-BASE for x in uby[1:-1]],P.UCOL_D,P.LOWER_BEAM,2,zone,'upper')
    ws2,bs2=wall(Ly,H,[x-BASE for x in uby[1:-1]],P.UCOL_D,P.LOWER_BEAM,2,zone,'upper')
    out['uwall_front']=(wf,bf,'front'); out['uwall_back']=(wb,bb,'back'); out['uwall_left']=(ws,bs,'left'); out['uwall_right']=(ws2,bs2,'right')
    return out, Lx, Ly, H
def stand_matrix(side, L, span_x, span_y, z_bottom):
    """로컬(x 길이, y 높이, z 바깥) → 월드. 바탕판 바깥면이 기둥 중심선 사각형 위에 놓임."""
    M=np.eye(4)
    if side=='front':   M[:3,:3]=[[1,0,0],[0,0,-1],[0,1,0]]; M[:3,3]=[-L/2, -span_y/2+BASE, z_bottom]
    elif side=='back':  M[:3,:3]=[[-1,0,0],[0,0,1],[0,1,0]]; M[:3,3]=[ L/2,  span_y/2-BASE, z_bottom]
    elif side=='left':  M[:3,:3]=[[0,0,-1],[1,0,0],[0,1,0]]; M[:3,3]=[-span_x/2+BASE, -L/2, z_bottom]
    elif side=='right': M[:3,:3]=[[0,0,1],[-1,0,0],[0,1,0]]; M[:3,3]=[ span_x/2-BASE,  L/2, z_bottom]
    return M
if __name__=='__main__':
    import os; out,Lx,Ly,H=lower_walls(); os.makedirs('../../models/v2_test',exist_ok=True)
    for n,(w,b,s) in out.items():
        print(n, 'white', w.is_volume, 'brown', b.is_volume, len(b.split()), len(b.faces), np.round(b.bounds[1]-b.bounds[0],1).tolist())
    w,b,_=out['wall_front']; w.export('../../models/v2_test/wall_front_white.stl'); b.export('../../models/v2_test/wall_front_brown.stl')
    uo,_,_,_=upper_walls(); w,b,_=uo['uwall_front']; print('upper', b.is_volume, len(b.split()), len(b.faces)); w.export('../../models/v2_test/uwall_front_white.stl'); b.export('../../models/v2_test/uwall_front_brown.stl')
