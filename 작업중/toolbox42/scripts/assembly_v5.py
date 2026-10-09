"""Toolbox42 v5 조립 검증: 경첩(뚜껑↔본체), 손잡이(↔본체 앞 귀), 걸쇠 — 모두 ⌀3.4 구멍(M3 핀/볼트) 기준.
출력: 조립 변환행렬(json), 각도별 간섭 부피, 간격, 걸쇠 걸림 깊이."""
import pickle, json, numpy as np, trimesh
from trimesh.transformations import rotation_matrix as R, translation_matrix as T
import sys; P=pickle.load(open(sys.argv[1],'rb'))   # 사용: python assembly_v5.py v5parts.pkl (fix_parts_v5.py 결과); B=P['base']; D=P['lid']; G=P['logo']; H=P['handle']; L=P['latch']
def inter_vol(a,b):
    try: m=a.intersection(b,engine='manifold'); return float(abs(m.volume)) if m.is_volume else 0.0
    except Exception as e: return -1
def min_gap(a,b,n=6000):
    pts=b.sample(n); d=trimesh.proximity.ProximityQuery(a).signed_distance(pts); return float(-d.max())
out={}
# ---------- 경첩: 본체 너클 구멍 축 (x 방향), 뚜껑 귀 구멍 축 ----------
knuckle=np.array([0,192.39,26.5]); lid_ear_print=np.array([0,68.42,10.0])
# 뚜껑: 출력 방향(뒤집힘) → 실제 방향: x축 180° 회전 (y→-y, z→-z) 후 평행이동
flip=R(np.pi,[1,0,0])
ear_flipped=(flip@np.append(lid_ear_print,1))[:3]
# x: 뚜껑 귀 쌍 중심 387.1/483.3 ↔ 너클 중심 79.9/176.1 → x 오프셋
dx=(79.9+176.1)/2-(387.1+483.3)/2
M_lid_closed=T([dx, knuckle[1]-ear_flipped[1], knuckle[2]-ear_flipped[2]])@flip
lid_c=D.copy(); lid_c.apply_transform(M_lid_closed); logo_c=G.copy(); logo_c.apply_transform(M_lid_closed)
print('뚜껑(닫힘) bounds',lid_c.bounds.round(2).tolist(),' 본체 bounds',B.bounds.round(2).tolist())
print('  뚜껑 rim 최저 z =',round(lid_c.bounds[0,2],2),' 본체 rim 상단 z = 29.9 →', '내려앉음' if lid_c.bounds[0,2]<29.9 else f'틈 {lid_c.bounds[0,2]-29.9:.2f}')
iv=inter_vol(B,lid_c); gap=min_gap(B,lid_c); print(f'  닫힘 간섭 부피 {iv:.2f} mm³, 최소 간격 {gap:.2f} mm')
out['hinge']={'axis_y':192.39,'axis_z':26.5,'lid_matrix_closed':M_lid_closed.tolist(),'closed_intersection_mm3':iv,'closed_min_gap_mm':gap,'sweep':[]}
for ang in [15,30,45,60,75,90,105,120]:
    Mo=T(knuckle)@R(np.radians(ang),[1,0,0])@T(-knuckle)@M_lid_closed   # 경첩축 둘레 회전(뒤쪽으로 열림)
    lo=D.copy(); lo.apply_transform(Mo); iv=inter_vol(B,lo); out['hinge']['sweep'].append({'deg':ang,'intersection_mm3':iv,'matrix':Mo.tolist()})
    print(f'  열림 {ang:3d}°: 간섭 {iv:8.2f} mm³')
# ---------- 손잡이: 본체 앞 귀 구멍(y 65.45, z 18.25) ↔ 다리 끝 구멍(y -162.57, z 4.5) ----------
ear=np.array([0,65.45,18.25]); leg_hole=np.array([0,-162.57,4.5])
# 다리가 아래로 늘어진 상태: 손잡이를 x축 -90° 회전(다리 -y 방향 → -z 방향 아래로), 구멍 축 x 유지
hx=(63.6+136.4)/2; ex=(91.6+164.4)/2
def handle_M(theta_deg):
    # 손잡이 로컬: 구멍을 원점으로 → 회전 → 귀 구멍으로
    return T(ear+[0,0,0])@R(np.radians(theta_deg),[1,0,0])@T([ex-hx,0,0])@T(-leg_hole)
out['handle']={'sweep':[]}
for th in [-90,-60,-30,0,30,60,90,120,150,180]:   # 0 = 출력 자세 그대로(다리가 -y, 앞으로 뻗음)
    hm=H.copy(); hm.apply_transform(handle_M(th)); iv=inter_vol(B,hm); g=min_gap(B,hm)
    out['handle']['sweep'].append({'deg':th,'intersection_mm3':iv,'min_gap_mm':g,'matrix':handle_M(th).tolist(),'bar_z':float(hm.bounds[0,2]),'bar_zmax':float(hm.bounds[1,2])})
    print(f'  손잡이 각도 {th:4d}°: 간섭 {iv:8.2f} mm³, 최소 간격 {g:6.2f}, z범위 {hm.bounds[0,2]:.1f}~{hm.bounds[1,2]:.1f}')
# ---------- 걸쇠: 결합 상대 찾기 ----------
print('걸쇠 암: 안쪽 간격 33.0, 바깥 43.0, 암 중심 간격 38.0, 링 구멍 ⌀3.4')
print('본체 앞 귀(걸쇠용 추정): x 102.75~108.44 / 147.56~153.25 → 안쪽 간격 39.1, 바깥 50.5, 중심 간격 44.8, 구멍 ⌀2.27 (y 72.64, z 11.49)')
print('→ 어느 쪽도 맞지 않음: 암이 귀 사이(39.1)에 들어가기엔 43 > 39.1, 귀를 감싸기엔 33 < 50.5. 구멍도 3.4 vs 2.27.')
# 뚜껑 탭(닫힘) 실제 위치
tab=lid_c.slice_plane([0,0,29.9],[0,0,1]); 
tb=[(e) for e in [lid_c.bounds]]
# 탭: 출력좌표 y 185.26~190.51 → 닫힘 상태 y
pts=np.array([[435,185.26,8.29,1],[435,190.51,8.29,1],[435,190.51,18,1],[435,185.26,18,1]])@M_lid_closed.T
print('뚜껑 탭(닫힘, 본체 좌표): y %.2f~%.2f, z %.2f~%.2f ; 본체 앞벽 바깥면 y=77.8, 걸쇠 귀 구멍 y=72.64 z=11.49'%(pts[:,1].min(),pts[:,1].max(),pts[:,2].min(),pts[:,2].max()))
out['tab_closed']={'y':[float(pts[:,1].min()),float(pts[:,1].max())],'z':[float(pts[:,2].min()),float(pts[:,2].max())]}
json.dump(out,open('assembly.json','w'))
pickle.dump({'lid_closed':M_lid_closed,'knuckle':knuckle,'handle_M':{th:handle_M(th) for th in [0,90,180]}},open('assembly_M.pkl','wb'))
