#!/usr/bin/env python3
"""인벌류트 기어 생성기 (스퍼 / 헤링본) — FDM 0.4 노즐 기준 규칙 내장.
규칙(스터디 2026-10): 모듈 ≥ 1.0(이 ≥ 2.5 mm 피치), 잇수 ≥ 12(언더컷 보정 전제 17 미만 주의), 압력각 20°, 백래시 0.10 mm(물림당, 이 두께에서 뺌),
팁 여유 0.25·m, 이뿌리 필렛 0.3·m, 헤링본 나선각 25°(20~30), 두께 12~20·m, 눕혀 출력(서포트 없음), 구멍 +0.3.
사용: python gear.py --module 1.5 --teeth 20 --width 8 --bore 5.3 [--herringbone] [--helix 25] --out gear.stl
"""
import argparse, math, numpy as np, trimesh
from shapely.geometry import Polygon
from shapely.affinity import rotate
from trimesh.creation import triangulate_polygon
def involute_profile(m, z, pa=20.0, backlash=0.10, clearance=0.25, root_fillet=0.3, pts=24):
    r=m*z/2; rb=r*math.cos(math.radians(pa)); ra=r+m; rf=r-(1+clearance)*m
    half_t=(math.pi*m/2 - backlash)/2           # 피치원에서 이 두께의 절반(백래시 뺀 값) → 각
    def inv(a): return math.tan(a)-a
    a_p=math.acos(rb/r); phi_p=half_t/r + inv(a_p)   # 피치점의 각 위치(이 중심선 기준)
    tooth=[]
    a_max=math.acos(rb/ra) if ra>rb else 0
    for t in np.linspace(0,a_max,pts):          # 인벌류트: 기초원→팁
        rr=rb/math.cos(t); ang=phi_p-inv(t); tooth.append((rr*math.cos(ang), rr*math.sin(ang)))
    one=[]; 
    # 이 하나: 뿌리(필렛 근사) → 인벌류트 왼쪽 → 팁 → 인벌류트 오른쪽(대칭) → 뿌리
    left=tooth; right=[(x,-y) for x,y in tooth][::-1]
    rfil=root_fillet*m
    base_ang=phi_p  # 기초원 시작 각
    # 뿌리 원호 구간(이 사이) 점들: 각 base_ang .. (2π/z − base_ang)
    seg=[]
    for k in range(z):
        th=2*math.pi*k/z
        def rot(p): return (p[0]*math.cos(th)-p[1]*math.sin(th), p[0]*math.sin(th)+p[1]*math.cos(th))
        # 뿌리 원호 (이전 이의 오른쪽 끝 → 이 이의 왼쪽 시작)
        a0=-(2*math.pi/z)+base_ang+ (rfil/rf); a1=-base_ang-(rfil/rf)
        for a in np.linspace(a0,a1,6): seg.append(rot((rf*math.cos(a),rf*math.sin(a))))
        # 필렛 근사: 뿌리→기초원 직선 (짧음)
        for p in right[::-1][::-1]: pass
        seg.extend(rot(p) for p in [(rf*math.cos(-base_ang),rf*math.sin(-base_ang))])
        seg.extend(rot(p) for p in right)      # 오른쪽 플랭크: 팁→? (right는 팁→기초 순) → 뒤집어 기초→팁
        seg.extend(rot(p) for p in left[::-1])
        seg.append(rot((rf*math.cos(base_ang),rf*math.sin(base_ang))))
    poly=Polygon(seg).buffer(0)
    return poly, dict(pitch_r=r, tip_r=ra, root_r=rf, base_r=rb)
def loft(polys, zs):
    """같은 점 수의 폴리곤들을 z별로 쌓아 닫힌 메시로."""
    rings=[np.array(p.exterior.coords)[:-1] for p in polys]; M=len(rings[0]); assert all(len(r)==M for r in rings)
    V=np.vstack([np.column_stack([r,np.full(M,z)]) for r,z in zip(rings,zs)]); F=[]
    for k in range(len(zs)-1):
        a=k*M; b=(k+1)*M; i=np.arange(M); j=(i+1)%M; F.append(np.column_stack([a+i,a+j,b+j])); F.append(np.column_stack([a+i,b+j,b+i]))
    F=np.vstack(F).tolist()
    for k,sign in [(0,-1),(len(zs)-1,1)]:
        vv,ff=triangulate_polygon(Polygon(rings[k]),engine='earcut'); bi=len(V); V=np.vstack([V,np.column_stack([vv,np.full(len(vv),zs[k])])]); F.extend(((ff[:,::-1] if sign<0 else ff)+bi).tolist())
    m=trimesh.Trimesh(V,np.array(F),process=True); m.merge_vertices(); trimesh.repair.fix_normals(m); return m
def make_gear(module, teeth, width, bore=0.0, herringbone=False, helix=25.0, pa=20.0, backlash=0.10, steps=24):
    poly,info=involute_profile(module,teeth,pa,backlash)
    if not herringbone:
        g=trimesh.creation.extrude_polygon(poly,width)
    else:
        r=info['pitch_r']; zs=np.linspace(0,width,steps+1); polys=[]
        for z in zs:
            h=min(z,width-z)                                # 중앙에서 꺾이는 V자
            ang=math.degrees(h*math.tan(math.radians(helix))/r)
            polys.append(rotate(poly,ang,origin=(0,0)))
        g=loft(polys,zs)
    if bore>0:
        cyl=trimesh.creation.cylinder(radius=bore/2,height=width+2,sections=64); cyl.apply_translation([0,0,width/2]); g=g.difference(cyl,engine='manifold')
    info.update(module=module,teeth=teeth,width=width,bore=bore,herringbone=herringbone,helix=helix,backlash=backlash)
    return g,info
def check_rules(info):
    w=[]
    if info['module']<1.0: w.append(f"모듈 {info['module']} < 1.0: 이가 0.4 노즐로 너무 작음")
    if info['teeth']<12: w.append(f"잇수 {info['teeth']} < 12: 이 형상 왜곡")
    if info['teeth']<17: w.append(f"잇수 {info['teeth']} < 17: 언더컷 — 전위(profile shift) 권장")
    if not (12*info['module']<=info['width']<=20*info['module']): w.append(f"두께 {info['width']}: 권장 {12*info['module']:.1f}~{20*info['module']:.1f} (12~20·m)")
    if info['herringbone'] and not (20<=info['helix']<=30): w.append('헤링본 나선각 20~30° 권장')
    return w
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--module',type=float,default=1.5); ap.add_argument('--teeth',type=int,default=20); ap.add_argument('--width',type=float,default=8)
    ap.add_argument('--bore',type=float,default=0); ap.add_argument('--herringbone',action='store_true'); ap.add_argument('--helix',type=float,default=25); ap.add_argument('--backlash',type=float,default=0.10); ap.add_argument('--out',required=True)
    a=ap.parse_args(); g,info=make_gear(a.module,a.teeth,a.width,a.bore,a.herringbone,a.helix,backlash=a.backlash)
    g.export(a.out); print({k:(round(v,3) if isinstance(v,float) else v) for k,v in info.items()}); print('is_volume',g.is_volume,'faces',len(g.faces),'축간거리(같은 기어 2개) =',round(info['module']*info['teeth'],3)); 
    for w_ in check_rules(info): print('⚠',w_)
