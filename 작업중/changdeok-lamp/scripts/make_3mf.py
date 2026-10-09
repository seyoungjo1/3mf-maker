#!/usr/bin/env python3
"""창덕궁 램프 v1 — 플레이트별 일반 3MF(열쇠고리 mm3mf 방식, 파트별 extruder) 작성.
플레이트 A: 월대(회색1) + 하층·상층 몸체(갈색2) + 발광 갓 2개(흰색3)
플레이트 B: 하층·상층 지붕(기와5, 처마 띠 흰색3 파트 포함) + 공포 띠 2개(초록4, 뒤집어 배치)
필라멘트 번호는 두 플레이트 공통: 1 회색 / 2 갈색 / 3 흰색 / 4 초록 / 5 기와색.
첫 층은 +0.15 선반영(EFC 0.15 프로파일 전용; 보정 0 으로 찍으면 첫 층이 0.15 두꺼워질 뿐 문제 없음).
사용: python make_3mf.py → ../3mf/Changdeok_Lamp_v1_A_platform_bodies.3mf, ..._B_roofs_bands.3mf (+ 배치표 출력)
"""
import os, sys, pickle, json, numpy as np, trimesh
from trimesh.transformations import rotation_matrix as R
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.abspath(os.path.join(HERE,'..','..','..'))
sys.path.insert(0, os.path.join(ROOT,'작업중','toolbox42','scripts')); from generic3mf import write_generic_3mf
sys.path.insert(0, os.path.join(ROOT,'tools')); from efc import pre_expand_first_layer, pre_expand_first_layer_group
EFC=0.15   # 사용자 프로파일 코끼리발 보정 — 첫 층을 미리 0.15 키움(출력물 1→2층 단차 0)
MODELS=os.path.join(HERE,'..','models'); OUT=os.path.join(HERE,'..','3mf'); os.makedirs(OUT,exist_ok=True)
COLORS={1:'#9e9e9e',2:'#6d4c41',3:'#f5f5f5',4:'#2e7d32',5:'#37474f'}; ORDER=[COLORS[i] for i in (1,2,3,4,5)]
NAMES={1:'회색(월대)',2:'갈색(몸체)',3:'흰색(갓·처마띠)',4:'초록(공포띠)',5:'기와색(지붕)'}
d=pickle.load(open(os.path.join(MODELS,'parts_v1.pkl'),'rb')); parts=d['parts']
def printed(name, rotz=0, efc=True):
    m,slot,flip=parts[name]; q=m.copy()
    if flip: q.apply_transform(R(np.pi,[1,0,0]))
    if rotz: q.apply_transform(R(np.radians(rotz),[0,0,1]))
    q.apply_translation([0,0,-q.bounds[0,2]])
    if efc: q=pre_expand_first_layer(q, EFC)
    return q, COLORS[slot]
def place(q, cx, cy):          # 바닥면 중심을 베드 (cx,cy) 에
    b=q.bounds; q.apply_translation([cx-(b[0,0]+b[1,0])/2, cy-(b[0,1]+b[1,1])/2, 0]); return q
BED=256; M=4; G=6             # 베드, 가장자리 여유, 파트 간격
plates={}
# ---- A ----
plat,c1=printed('platform',90); pb=plat.bounds; pw,pd=pb[1,0]-pb[0,0],pb[1,1]-pb[0,1]
place(plat, M+pw/2, M+pd/2)
lb,c2=printed('lower_body'); lbw,lbd=lb.bounds[1,0]-lb.bounds[0,0],lb.bounds[1,1]-lb.bounds[0,1]
ub,_=printed('upper_body'); ubw,ubd=ub.bounds[1,0]-ub.bounds[0,0],ub.bounds[1,1]-ub.bounds[0,1]
xr=M+pw+G+max(lbw,ubw)/2
place(lb, xr, M+lbd/2); place(ub, xr, M+lbd+G+ubd/2)
ls,c3=printed('lower_screen'); lsw,lsd=ls.bounds[1,0]-ls.bounds[0,0],ls.bounds[1,1]-ls.bounds[0,1]
us,_=printed('upper_screen'); usw,usd=us.bounds[1,0]-us.bounds[0,0],us.bounds[1,1]-us.bounds[0,1]
place(ls, M+lsw/2, M+pd+G+lsd/2); place(us, xr, M+lbd+G+ubd+G+usd/2)
plates['A_platform_bodies']=[{'name':'platform','parts':[(plat,c1,'platform')]},{'name':'lower_body','parts':[(lb,c2,'lower_body')]},{'name':'upper_body','parts':[(ub,c2,'upper_body')]},
                             {'name':'lower_screen','parts':[(ls,c3,'lower_screen')]},{'name':'upper_screen','parts':[(us,c3,'upper_screen')]}]
# ---- B ----
lr,c5=printed('lower_roof',efc=False); lrt,_=printed('lower_roof_trim',efc=False); lr,lrt=pre_expand_first_layer_group([lr,lrt],EFC)   # 지붕+흰 띠는 한 덩어리로 바깥만 키움
ur,_=printed('upper_roof',efc=False); urt,_=printed('upper_roof_trim',efc=False); ur,urt=pre_expand_first_layer_group([ur,urt],EFC)
lrw,lrd=lrt.bounds[1,0]-lrt.bounds[0,0],lrt.bounds[1,1]-lrt.bounds[0,1]; urw,urd=urt.bounds[1,0]-urt.bounds[0,0],urt.bounds[1,1]-urt.bounds[0,1]
for q in (lr,lrt): place(q, M+lrw/2, M+lrd/2)
for q in (ur,urt): place(q, M+urw/2, M+lrd+G+urd/2)
lbd_,c4=printed('lower_band',90); ubd_,_=printed('upper_band',90)
bw=max(lbd_.bounds[1,0]-lbd_.bounds[0,0], ubd_.bounds[1,0]-ubd_.bounds[0,0]); xb=M+lrw+G+bw/2
l1=lbd_.bounds[1,1]-lbd_.bounds[0,1]; l2=ubd_.bounds[1,1]-ubd_.bounds[0,1]
place(lbd_, xb, M+l1/2); place(ubd_, xb, M+l1+G+l2/2)
plates['B_roofs_bands']=[{'name':'lower_roof','parts':[(lr,c5,'lower_roof_tile'),(lrt,c3,'lower_roof_eave_white')]},
                         {'name':'upper_roof','parts':[(ur,c5,'upper_roof_tile'),(urt,c3,'upper_roof_eave_white')]},
                         {'name':'lower_band','parts':[(lbd_,c4,'lower_band')]},{'name':'upper_band','parts':[(ubd_,c4,'upper_band')]}]
layout={}
for pname,objs in plates.items():
    allb=np.array([[o['parts'][0][0].bounds[0], o['parts'][0][0].bounds[1]] for o in objs])
    lo=allb[:,0].min(0); hi=allb[:,1].max(0); assert (lo>=0).all() and (hi[:2]<=BED).all(), (pname, lo, hi)
    fn=os.path.join(OUT,f'Changdeok_Lamp_v1_{pname}.3mf'); write_generic_3mf(fn, objs, title=f'Changdeok Injeongjeon Lamp v1 {pname}', material_order=ORDER)
    layout[pname]={o['name']:[round(float(v),1) for v in np.r_[o['parts'][0][0].bounds[0],o['parts'][0][0].bounds[1]]] for o in objs}
    print(fn, '베드 사용', np.round(hi-lo,1).tolist(), 'extent', np.round(lo,1).tolist(), np.round(hi,1).tolist())
    for o in objs:
        for q,col,n in o['parts']: print(f"   {o['name']:12s} {n:24s} 색 {col} extruder {ORDER.index(col)+1} 바닥면 중심 ({(q.bounds[0,0]+q.bounds[1,0])/2:.1f}, {(q.bounds[0,1]+q.bounds[1,1])/2:.1f}) 크기 {np.round(q.bounds[1]-q.bounds[0],1).tolist()}")
json.dump({'filaments':{i:NAMES[i]+' '+COLORS[i] for i in COLORS},'layout':layout}, open(os.path.join(OUT,'layout_v1.json'),'w'), ensure_ascii=False, indent=1)
