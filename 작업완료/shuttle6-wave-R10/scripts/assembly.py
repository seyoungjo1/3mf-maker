from pathlib import Path
import sys,pickle,json,numpy as np,trimesh as tm
from shapely.geometry import Polygon,box
from trimesh.transformations import rotation_matrix as R,translation_matrix as T
PTH=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(PTH/'scripts'))
from build import P,pressed,union

def envelope():
 """Rigid dimensional gauge only, not a rigid material model of feather shuttlecocks."""
 meshes=[]
 for i in range(6):
  start=10.+28*i;center=start+71
  theta=np.linspace(0,np.pi/2,41)
  pts=[(0,start),(32,start),(12.5,start+62),(14,start+62),(14,center)]
  pts += [(14*np.cos(a),center+14*np.sin(a)) for a in theta[1:]]
  pts += [(0,start)]
  m=tm.creation.revolve(np.asarray(Polygon(pts).exterior.coords),sections=96);m.fix_normals();m.apply_translation([0,2,0]);meshes.append(m)
 return union(*meshes)

def define(parts):
 from pipeline import inter,gaps
 shell=pickle.load(open(PTH/'assembled_shell.pkl','rb'))['shell']
 core=envelope();pickle.dump({'contents':core},open(PTH/'content_envelopes.pkl','wb'))
 closed=T([0,0,P['CLOSED_L']])@R(np.pi,[0,1,0])
 in_shell=core.copy();in_shell.apply_transform(closed)
 measures={'drawer_vs_dimensional_gauge_mm3':inter(parts['drawer'],core),'shell_vs_dimensional_gauge_mm3':inter(shell,in_shell),'cap_joint_overlap_mm3':inter(parts['cap'],parts['drawer'])}
 assert all(0<=v<.01 for v in measures.values()),measures
 dim=json.load(open(PTH/'dimensions.json'))
 # Actual straight section ray hit; compensate the1mm off-axis offset analytically.
 hits,_,_=parts['drawer'].ray.intersects_location([[0,-1,100]],[[1,0,0]],multiple_hits=True)
 xs=sorted(hits[:,0]);inner=2*float(np.sqrt(xs[0]**2+1))
 floor_hits,_,_=parts['drawer'].ray.intersects_location([[0,0,100]],[[0,-1,0]],multiple_hits=True)
 fy=sorted(abs(floor_hits[:,1]));floor=float(fy[-1]-fy[0])
 assert abs(inner-64)<.015 and abs(floor-2)<.015,(inner,floor)
 dim['measured_open_tray_id_mm']=inner;dim['measured_flat_floor_thickness_mm']=floor
 dim['measured_flat_base_width_mm']=float(2*np.sqrt(34**2-32**2))
 dim['detent']['actual_boss_x_extreme_mm']=float(parts['drawer'].bounds[1,0])
 dim['detent']['actual_x_interference_mm']=float(parts['drawer'].bounds[1,0]-P['ID']/2)
 dim['cap_joint']['actual_solid_overlap_mm3']=measures['cap_joint_overlap_mm3']
 roof=P['END_ACTUAL_ROOF_Z'];v=np.asarray(parts['drawer'].vertices)
 sel=(np.abs(v[:,0])<1e-4)&(v[:,1]>-2.3)&(v[:,1]<-1.8)&(v[:,2]>roof-.4)&(v[:,2]<roof+.001)
 tip=np.unique(v[sel],axis=0);tip=tip[np.argsort(tip[:,2])];a,b=tip[-2:]
 angle=float(np.rad2deg(np.arctan2(b[2]-a[2],b[1]-a[1])))
 dim['end_geometry']['measured_nominal_mesh_chord_from_bed_deg']=angle
 dim['end_geometry']['measured_nominal_bridge_width_mm']=2*abs(float(b[1]))
 assert abs(angle-30)<.6
 json.dump(dim,open(PTH/'dimensions.json','w'),ensure_ascii=False,indent=2)
 compressed=pressed(parts['drawer']);coupon_compressed=pressed(parts['drawer_coupon'])
 # Record the intended elastic bead crossing as interference, not a zero-force/zero-collision claim.
 crossings=[]
 for distance in [0,.25,.5,.75,1,1.5,2,3,5,8,10,12,14]:
  m=parts['drawer'].copy();m.apply_transform(T([0,0,distance])@closed)
  crossings.append({'extraction_mm':distance,'rigid_overlap_mm3':inter(shell,m)})
 assert crossings[0]['rigid_overlap_mm3']<.01
 measures['detent_crossing_without_compliance']=crossings
 measures['scope']='Nominal64mm dimensional gauge offset upward2mm over flat floor,6 nested225mm assumption. Not a measured feather envelope or deformation/contact simulation. Rounded beads have intentional elastic crossing; click force not calculated.'
 json.dump(measures,open(PTH/'fit_R10.json','w'),ensure_ascii=False,indent=2)
 G=T([100,255,40])@R(np.pi/2,[1,0,0])
 st={'닫힘':{'shell':G,'drawer':G@closed,'cap':G@closed}}
 for d in [.5,1,2,5,8,10]:st[f'딸깍 통과 {d}mm']={'shell':G,'drawer_compressed':G@T([0,0,d])@closed,'cap':G@T([0,0,d])@closed}
 for d in [14,40,80,120,180,236]:st[f'인출 {d}mm']={'shell':G,'drawer':G@T([0,0,d])@closed,'cap':G@T([0,0,d])@closed}
 st['열림']={'shell':G,'drawer':G@T([0,0,236])@closed,'cap':G@T([0,0,236])@closed}
 st['분리']={'shell':G,'drawer':T([90,0,0])@G@T([0,0,236])@closed,'cap':T([90,0,0])@G@T([0,0,256])@closed}
 st['몸통 접착']={'shell_lower':G,'shell_upper':G@T([0,0,P['BODY_SPLIT_Z']])}
 st['뚜껑 끼움 전']={'drawer':np.eye(4),'cap':T([0,0,-15])}
 st['뚜껑 끼움 완료']={'drawer':np.eye(4),'cap':np.eye(4)}
 st['64 공칭 게이지']={'drawer':np.eye(4),'contents':np.eye(4)}
 cc=T([0,0,46])@R(np.pi,[0,1,0])
 st['딸깍 시험편 닫힘']={'shell_coupon':np.eye(4),'drawer_coupon':cc}
 st['딸깍 시험편 통과']={'shell_coupon':np.eye(4),'coupon_compressed':T([0,0,3])@cc}
 placed={}
 for name,m,M in [('shell',shell,G),('drawer',parts['drawer'],G@closed),('cap',parts['cap'],G@closed)]:
  q=m.copy();q.apply_transform(M);placed[name]=q
 pickle.dump(placed,open(PTH/'figures/closed_coordinates_R10.pkl','wb'))
 import drawing
 return {'states':st,'extra':{'shell':shell,'drawer_compressed':compressed,'contents':core,'coupon_compressed':coupon_compressed},
 'pairs':[['shell','drawer',{'contact':True}],['shell','drawer_compressed',{'contact':True}],['shell','cap',{'contact':True}],['drawer','cap',{'contact':True}],['drawer_compressed','cap',{'contact':True}],['shell_lower','shell_upper',{'contact':True}],['drawer','contents',{'contact':True}],['shell_coupon','drawer_coupon',{'contact':True}],['shell_coupon','coupon_compressed',{'contact':True}]],
 'notes':['R10: Open nominal ID64, flat lower plane and2mm floor. Feather compliance is not modelled as rigid plastic.','Tray prints horizontally on diagonal; cap separately face down. Body only2pieces upright.','Long clip and release button removed; two integrated round beads meet matching inner-shell pockets. Pull-through feel only, no rated positive lock.','Bead crossing poses use a geometrically compressed bead for collision checks; this is a kinematic representation, not FEA or force validation.',f'Actual dimensional/closed joint overlaps: {measures}.','Cap has6mm U-shaped keyed insertion and0.2mm per-side clearance; retention/friction must be checked physically.'], 'sweeps':[]}
