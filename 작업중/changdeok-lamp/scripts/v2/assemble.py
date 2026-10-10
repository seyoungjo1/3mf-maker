#!/usr/bin/env python3
"""인정전 램프 v2 조립: 모든 부재를 조립 좌표로 배치하고, 오브젝트(출력 단위)별 파트·색·출력 변환을 돌려준다.
좌표: 월대 윗면 z=0, 건물 중심 (0,0), 정면 = -y. 중심선(c) 기준 거리 d 로 부재 위치를 맞춘다(README 단면표)."""
import os, sys, pickle, numpy as np, trimesh
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from geo import B, CYL, U, D, RING, flip_x, drop
import params as P
from walls import lower_walls, upper_walls, stand_matrix
from band import band
from roof import roof
from woldae import platform
C={'gray':'#9e9e9e','brown':'#6d4c41','white':'#f5f5f5','green':'#2e7d32','tile':'#263238'}
ORDER=[C['white'],C['brown'],C['green'],C['tile'],C['gray']]
clr=P.CLR
def story(sx, sy, z_floor0, floor_hole, walls_fn, band_h, roof_kw, prefix):
    """한 층: 바닥판 + 벽 4 + 평방 링(아래 턱·위 림) + 공포 띠 + 지붕. 반환 objects(list), z_roof0, z_roof_top"""
    objs=[]
    # 바닥판(갈색): 중심선 바깥 4, 벽 안쪽 위치 턱
    fl=B(sx+8, sy+8, P.FLOOR_T, 0,0, z_floor0)
    fl=D(fl, floor_hole)
    zf=z_floor0+P.FLOOR_T
    lip_o=(sx-2*(P.WALL_BASE+clr), sy-2*(P.WALL_BASE+clr)); fl=U([fl, RING(lip_o[0], lip_o[1], P.LIP_H, zf-0.01, P.LIP_W)])
    objs.append(dict(name=f'{prefix}floor', parts=[(fl,'brown',f'{prefix}floor')], print='asis'))
    # 벽(흰 바탕 + 갈색 부조), 로컬 = 출력 방향
    ws,Lx,Ly,H=walls_fn()
    for n,(w,b,side) in ws.items():
        L=Lx if side in ('front','back') else Ly
        M=stand_matrix(side, L, sx, sy, zf)
        objs.append(dict(name=f'{n}', parts=[(b,'brown',f'{n}')], print='local', M=M))
    z_ring=zf+H-1.0                                   # 벽 윗머리 1.0 이 링 밑면 홈에 들어감
    # 안쪽 흰 발광 통(통짜 네모, 단일 벽 0.8, 세워서 출력): 바닥판 턱 안쪽, 링 아래 0.3
    din=P.WALL_BASE+clr+P.LIP_W+P.DIFFUSER_GAP
    dif=RING(sx-2*din, sy-2*din, (z_ring-0.3)-zf, zf, P.DIFFUSER_T)
    objs.append(dict(name=f'{prefix}diffuser', parts=[(dif,'white',f'{prefix}diffuser')], print='asis'))
    # 평방 링(갈색): 위 링 + 아래 턱(벽 안쪽) + 위 림
    ring=RING(sx+2*P.RING_W_OUT, sy+2*P.RING_W_OUT, P.RING_T, z_ring, P.RING_W_OUT+P.RING_W_IN)
    # 벽 윗머리 자리: 링 밑면 홈(벽 판 안쪽면 −0.3 ~ 창방 바깥면 +0.3, 깊이 1.0). 밑면이 베드에 닿는 방향(asis)으로 출력 → 홈 천장 브리지 4.1(양쪽 지지: 안쪽 턱 1.2, 바깥 턱 1.0)
    gin=P.WALL_BASE+clr; gout=P.COL_D/2+0.2                                   # 바깥: 기둥 반원(2.4)+0.2 — 정면벽 끝 기둥까지 홈 안에(이전 2.3 은 0.1 간섭)
    ring=D(ring, D(B(sx+2*gout, sy+2*gout, 1.0+0.5, 0,0, z_ring-0.5), B(sx-2*gin, sy-2*gin, 3, 0,0, z_ring-1)))
    z_band=z_ring+P.RING_T; rim_h=band_h+1.5
    rim=RING(sx+2*P.RIM_OUT, sy+2*P.RIM_OUT, rim_h+0.01, z_band-0.01, P.RIM_IN+P.RIM_OUT)
    objs.append(dict(name=f'{prefix}ring', parts=[(U([ring,rim]),'brown',f'{prefix}ring')], print='asis'))   # 링 밑면이 베드, 림이 위로
    # 공포 띠(초록 + 갈색 포): 뒤집어 출력
    eave=(roof_kw['EX'], roof_kw['EY'])
    g,_=band((sx+2*P.RING_W_OUT, sy+2*P.RING_W_OUT), (sx+2*P.RIM_OUT, sy+2*P.RIM_OUT), z_band, band_h, eave)
    objs.append(dict(name=f'{prefix}band', parts=[(g,'green',f'{prefix}band')], print='flip'))
    z_roof=z_band+band_h
    under=(sx+2*P.RING_W_OUT, sy+2*P.RING_W_OUT, z_band, sx+2*P.RING_W_OUT+2*8.0, sy+2*P.RING_W_OUT+2*8.0)   # 처마밑 경사: 평방 바깥(z_band) → 처마 끝(z_roof), 띠 바깥
    return objs, z_roof, under
def build():
    K=P.K; sx,sy=P.SPAN_X,P.SPAN_Y; usx,usy=P.USPAN_X,P.USPAN_Y
    z_t=P.SOFFIT_T+P.LINE_T+P.TILE_BASE
    TX,TY=usx+8+2*(clr+P.LIP_W)+2*1.0, usy+8+2*(clr+P.LIP_W)+2*1.0          # 하층 지붕 평탄면 = 상층 바닥판 + 턱 + 1
    lower_kw=dict(EX=P.EAVE_LX, EY=P.EAVE_LY, kind='lower', light_hole=(usx-12, usy-12),
                  lip=(usx+8+2*clr+2*P.LIP_W, usy+8+2*clr+2*P.LIP_W, P.LIP_W, 1.8))
    # 하층
    objs=[]
    z_lr0_guess=None
    lo_objs, z_lr, under_l = story(sx, sy, P.FLOOR_Z0, CYL(P.LIGHT_D if hasattr(P,'LIGHT_D') else 50, 10, 0,0, P.FLOOR_Z0-1), lower_walls, P.LOWER_BAND_H,
                          dict(lower_kw, top=(TX,TY,0)), 'L_')
    # top z 는 z_roof 를 알아야 하므로 지붕만 다시 생성
    z_top=z_lr+z_t+P.LOWER_ROOF_RISE
    rf_kw=dict(lower_kw, top=(TX,TY,z_top))
    lo_objs=[o for o in lo_objs if o['name']!='L_roof']
    groove=(sx+2*(P.RIM_OUT+clr), sy+2*(P.RIM_OUT+clr), P.RIM_IN+P.RIM_OUT+2*clr, 1.8+0.5)
    for pc in roof(**rf_kw, z0=z_lr, groove=groove, prefix='L_roof_', under=under_l): lo_objs.append(dict(name=pc['name'], parts=[(pc['mesh'],pc['color'],pc['name'])], print=pc['print'], **({'print_parts':[(pc['print_mesh'],pc['color'],pc['name'])]} if 'print_mesh' in pc else {})))
    objs+=lo_objs
    # 상층: 바닥판은 하층 지붕 평탄면 위
    gl,gz,gr=P.UPPER_GABLE
    up_objs, z_ur, under_u = story(usx, usy, z_top, B(usx-12, usy-12, 10, 0,0, z_top-1), upper_walls, P.UPPER_BAND_H,
                          dict(EX=P.EAVE_UX, EY=P.EAVE_UY, kind='upper', gable=(gl,gz,0)), 'U_')
    up_objs=[o for o in up_objs if o['name']!='U_roof']
    groove=(usx+2*(P.RIM_OUT+clr), usy+2*(P.RIM_OUT+clr), P.RIM_IN+P.RIM_OUT+2*clr, 1.8+0.5)
    for pc in roof(EX=P.EAVE_UX, EY=P.EAVE_UY, z0=z_ur, kind='upper', gable=(gl, gz, z_ur+z_t+gr), groove=groove, prefix='U_roof_', under=under_u): up_objs.append(dict(name=pc['name'], parts=[(pc['mesh'],pc['color'],pc['name'])], print=pc['print'], **({'print_parts':[(pc['print_mesh'],pc['color'],pc['name'])]} if 'print_mesh' in pc else {})))
    objs+=up_objs
    # 월대
    pl=platform((sx+8, sy+8))
    objs.insert(0, dict(name='platform', parts=[(pl,'gray','platform')], print='asis'))
    info=dict(z_lower_roof=z_lr, z_lower_roof_top=z_top, z_upper_roof=z_ur, z_ridge=z_ur+z_t+gr)
    return objs, info
def assembled(o):
    """오브젝트의 파트를 조립 좌표로"""
    out=[]
    for m,col,n in o['parts']:
        q=m.copy()
        if o['print']=='local': q.apply_transform(o['M'])
        out.append((q,col,n))
    return out
def printed(o):
    """출력 방향(바닥 z=0) 파트 목록"""
    ms=[m.copy() for m,_,_ in o.get('print_parts', o['parts'])]                  # 출력 전용 메시(평평하게 뽑아 끼우면 휘는 흰 테)가 있으면 그것
    if o['print']=='flip':
        for q in ms: q.apply_transform(trimesh.transformations.rotation_matrix(np.pi,[1,0,0]))
    elif isinstance(o['print'],tuple) and o['print'][0]=='lay':                  # 옆면(u 방향 면)을 베드로
        Rm=trimesh.geometry.align_vectors(np.asarray(o['print'][1],float), [0,0,-1])
        for q in ms: q.apply_transform(Rm)
    zmin=min(q.bounds[0,2] for q in ms)
    for q in ms: q.apply_translation([0,0,-zmin])
    return [(q,col,n) for q,(m,col,n) in zip(ms,o['parts'])]
if __name__=='__main__':
    import time; t=time.time()
    objs,info=build(); print('built %.0fs'%(time.time()-t), {k:round(v,1) for k,v in info.items()})
    MD=os.path.join(HERE,'..','..','models','v2'); os.makedirs(os.path.join(MD,'asm'),exist_ok=True)
    for o in objs:
        for q,col,n in assembled(o):
            print(f"{n:24s} {col:6s} closed={q.is_volume} bodies={len(q.split())} faces={len(q.faces):,} size={np.round(q.bounds[1]-q.bounds[0],1).tolist()}")
            q.export(os.path.join(MD,'asm',n+'.stl'))
    pickle.dump(dict(objs=objs,info=info), open(os.path.join(MD,'objs_v2.pkl'),'wb'))
