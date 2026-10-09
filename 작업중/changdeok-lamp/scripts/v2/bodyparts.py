"""바닥판(갈색, 벽 홈·빛 구멍)과 평방 링(갈색, 벽 윗홈·림). 조립 좌표."""
import numpy as np
from geo import B, CYL, U, D, RING
import params as P
BASE=P.WALL_BASE
def floor_plate(span_x, span_y, t, z0, hole, wall_bottom_t=1.6, slot_depth=1.5, margin=4.0, clr=P.CLR, hole_round=False):
    """기둥 중심선 사각형(span) 바깥으로 margin. 벽 홈: 바탕판 바깥면 = 중심선, 안쪽으로 base+relief."""
    W,Dp=span_x+2*margin, span_y+2*margin
    pl=B(W,Dp,t,0,0,z0)
    sw=wall_bottom_t+2*clr; off=-clr+ sw/2 - 0.0            # 홈 중심: 중심선에서 안쪽으로 (sw/2 - clr)
    slots=[B(span_x+2*(clr+2.4), sw, slot_depth+1, 0, -(span_y/2 - off), z0+t-slot_depth), B(span_x+2*(clr+2.4), sw, slot_depth+1, 0, (span_y/2 - off), z0+t-slot_depth),
           B(sw, span_y, slot_depth+1, -(span_x/2 - off), 0, z0+t-slot_depth), B(sw, span_y, slot_depth+1, (span_x/2 - off), 0, z0+t-slot_depth)]
    pl=D(pl, U(slots))
    pl=D(pl, CYL(hole[0], t+2, 0,0, z0-1) if hole_round else B(hole[0],hole[1],t+2,0,0,z0-1))
    return pl
def top_ring(span_x, span_y, col_d, z0, t=P.RING_T, width=4.0, rim_h=10.5, rim_wall=2.4, wall_top_t=2.6, groove_depth=1.0, clr=P.CLR):
    """평방 링: 바깥 = 기둥 접선(span+col_d), 폭 width. 밑면 벽 홈(폭 wall_top_t+0.6), 윗면 림(o 2.0~2.0+rim_wall)."""
    W,Dp=span_x+col_d, span_y+col_d
    ring=RING(W,Dp,t,z0,width)
    gw=wall_top_t+2*clr; off=gw/2-clr                      # 홈: 바깥면 기준 중심선에서 안쪽
    g=[B(span_x+2*(clr+2.4), gw, groove_depth+1, 0, -(span_y/2-off), z0-1), B(span_x+2*(clr+2.4), gw, groove_depth+1, 0, (span_y/2-off), z0-1),
       B(gw, span_y, groove_depth+1, -(span_x/2-off), 0, z0-1), B(gw, span_y, groove_depth+1, (span_x/2-off), 0, z0-1)]
    ring=D(ring, U(g))
    rim=RING(W-2*2.0, Dp-2*2.0, rim_h+0.5, z0+t-0.5, rim_wall)
    return U([ring, rim]), (W-2*2.0, Dp-2*2.0)             # (메시, 림 바깥 치수)
