from pathlib import Path
import sys,pickle,json,numpy as np,trimesh as tm
from shapely.geometry import Polygon,box
from trimesh.transformations import rotation_matrix as R,translation_matrix as T
PTH=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(PTH/'scripts'))
from build import P,pressed,union

def envelope(margin=0.):
 meshes=[]
 for i in range(6):
  start=10.+28*i;tip=start+85;center=tip-14
  theta=np.linspace(0,np.pi/2,41)
  pts=[(0,start),(34,start),(12.5,start+62),(14,start+62),(14,center)]
  pts += [(14*np.cos(a),center+14*np.sin(a)) for a in theta[1:]]
  pts += [(0,start)]
  poly=Polygon(pts)
  if margin:
   poly=poly.buffer(margin,quad_segs=24).intersection(box(0,10,50,300))
  m=tm.creation.revolve(np.asarray(poly.exterior.coords),sections=96);m.fix_normals();meshes.append(m)
 return union(*meshes)

def define(parts):
 from pipeline import inter,gaps
 # Measure the final meridian chord on the actual nominal mesh, after booleans.
 roof=P['END_ACTUAL_ROOF_Z'];v=np.asarray(parts['drawer'].vertices)
 sel=(np.abs(v[:,0])<1e-4)&(v[:,1]>-2.2)&(v[:,1]<-1.8)&(v[:,2]>roof-.4)&(v[:,2]<roof+.001)
 tip=np.unique(v[sel],axis=0);tip=tip[np.argsort(tip[:,2])]
 assert len(tip)>=2,'Terminal meridian vertices missing'
 a,b=tip[-2:];angle=float(np.rad2deg(np.arctan2(b[2]-a[2],b[1]-a[1])))
 opening=2*abs(float(b[1]))
 assert abs(angle-30)<.6 and abs(opening-4)<.01,(angle,opening,a,b)
 dim=json.load(open(PTH/'dimensions.json'))
 dim['end_geometry']['measured_nominal_mesh_chord_from_bed_deg']=angle
 dim['end_geometry']['measured_nominal_bridge_width_mm']=opening
 dim['end_geometry']['measured_chord_endpoints_mm']=[a.tolist(),b.tolist()]
 json.dump(dim,open(PTH/'dimensions.json','w'),ensure_ascii=False,indent=2)
 shell=pickle.load(open(PTH/'assembled_shell.pkl','rb'))['shell']
 core=envelope();clear=envelope(P['CONTENT_CLEARANCE'])
 pickle.dump({'contents':core,'clearance':clear},open(PTH/'content_envelopes.pkl','wb'))
 closed=T([0,0,P['CLOSED_L']])@R(np.pi,[0,1,0])
 in_shell=clear.copy();in_shell.apply_transform(closed)
 measures={'drawer_vs_clearance_mm3':inter(parts['drawer'],clear),'shell_vs_clearance_mm3':inter(shell,in_shell)}
 assert all(0<=v<.01 for v in measures.values()),measures
 measures['scope']='Assumed six-stack envelope225mm, featherD68/baseD28/length85/pitch28; offset1.5mm, clipped only at front resting face. Not measured brand fit.'
 measures['sampled_surface_distance_mm_not_min_clearance']=gaps(parts['drawer'],core,1800,region=[[-36,-36,190],[36,36,239]])
 json.dump(measures,open(PTH/'fit_R9.json','w'),ensure_ascii=False,indent=1)
 G=T([100,255,44])@R(np.pi/2,[1,0,0])
 placed={}
 for name,m,M in [('shell',shell,G),('drawer',parts['drawer'],G@closed)]:
  p=m.copy();p.apply_transform(M);placed[name]=p
 pickle.dump(placed,open(PTH/'figures/closed_coordinates_R9.pkl','wb'))
 lock=parts['drawer'].copy();lock.apply_transform(T([0,0,3])@closed)
 lock_volume=inter(shell,lock);assert lock_volume>1,lock_volume
 st={'닫힘':{'shell':G,'drawer':G@closed},'걸쇠 누름':{'shell':G,'drawer_pressed':G@closed}}
 for d in [0,5,10,20,40,60,80,100,120,140,160,180,200,220,236]:st[f'인출 {d}mm']={'shell':G,'drawer_pressed':G@T([0,0,d])@closed}
 st['열림']={'shell':G,'drawer':G@T([0,0,236])@closed}
 st['분리']={'shell':G,'drawer':T([95,0,0])@G@T([0,0,236])@closed}
 st['몸통 접착']={'shell_lower':G,'shell_upper':G@T([0,0,P['BODY_SPLIT_Z']])}
 st['수납 여유']={'drawer':np.eye(4),'clearance':np.eye(4)}
 st['내용물 누름']={'drawer_pressed':np.eye(4),'contents':np.eye(4)}
 cc=T([0,0,46])@R(np.pi,[0,1,0])
 st['시험편 닫힘']={'shell_coupon':np.eye(4),'drawer_coupon':cc}
 st['시험편 해제']={'shell_coupon':np.eye(4),'coupon_pressed':cc}
 st['콘끝 시험편']={'tip_coupon':np.eye(4)}
 import drawing
 return {'states':st,'extra':{'shell':shell,'drawer_pressed':pressed(parts['drawer']),'contents':core,'clearance':clear,'coupon_pressed':pressed(parts['drawer_coupon'])},
 'pairs':[['shell','drawer',{'contact':True}],['shell','drawer_pressed',{'contact':True}],['shell_lower','shell_upper',{'contact':True}],['drawer','clearance',{'contact':True}],['drawer_pressed','contents',{'contact':True}],['shell_coupon','drawer_coupon',{'contact':True}],['shell_coupon','coupon_pressed',{'contact':True}]],
 'notes':[f'몸통은 가로 분할. 하단131.5mm / 상단121.5mm, 겹침턱10mm·반경 접착 틈0.30mm. 접착제가 경화된 뒤 사용.',f'해제하지 않고3mm 강제 인출 시 걸림 교집합 {lock_volume:.2f}mm³.',f'가상 여유 외피 교집합: {measures}. 실제 브랜드·출력 반복 내구 검증 전.','새 콘: 시작부터45→30도 연속 곡면·외부 채움. 끝 접선45→30도(베드 기준), 개구71.4→4mm, 마지막4mm 브리지. 걸쇠 턱z30·슬롯 끝z45.5에 작은 서포트.','30.5×3×8 스프링·누름1.5mm·뿌리 아래3.5mm. 이론 선형 근사이며 정격 파손 힘·피로 수명·비틀림 내력 아님.'],'sweeps':[]}
