#!/usr/bin/env python3
"""C안: 공칭 모델과 EFC 모델. 검토 단계는 3MF를 생성하지 않는다."""
from pathlib import Path
import sys,json,pickle
import numpy as np
import trimesh as tm
from shapely.geometry import Point,Polygon,LineString,box as rect
from shapely.ops import unary_union
from scipy.spatial import cKDTree
HERE=Path(__file__).resolve().parent; PROJ=HERE.parent; ROOT=PROJ.parent.parent
sys.path.insert(0,str(ROOT/'tools'))
from efc import pre_expand_first_layer
P=dict(OUTER_W=74.6,SIDE_R=100.,CORNER_R=30.,CAP_W=78.6,CAP_SIDE_R=102.,CAP_CORNER_R=32.,ID=68.6,BODY_L=243.,FLOOR=3.,CAP_T=10.,CLOSED_L=253.,TRAY_R=34.,TRAY_T=2.,TRAY_END=249.8,STOP_T=1.25,USE_L=225.,RADIAL_GAP=.3,GROOVE_D=.6,GROOVE_W=2.4,PATTERN_START=55.,PATTERN_END=190.,CONTENT_D=64.,CONTENT_L=225.,STACK_PITCH=28.,SHUTTLE_L=85.,CONTENT_BASE_D=28.,END_ANGLE_FROM_BED=45.,END_BRIDGE_D=4.,BODY_SPLIT_Z=121.5,GLUE_L=10.,GLUE_R=35.7,GLUE_INNER_R=34.3,GLUE_SOCKET_R=36.,CONTENT_CLEARANCE=0.)
P.update(TRAY_INNER_R=32.,FLAT_OUTER_Y=-32.,FLAT_INNER_Y=-30.,CAP_JOINT_L=6.,CAP_JOINT_GAP=.20,DETENT_R=1.6,DETENT_X=33.1,DETENT_Y=-1.5,DETENT_Z=20.,DETENT_POCKET_R=1.85,CONTENT_OFFSET_Y=2.)
COLORS={'shell':'#33383e','drawer':'#bd6f53','shell_coupon':'#33383e','drawer_coupon':'#bd6f53'}
def box(x0,y0,z0,x1,y1,z1):
 m=tm.creation.box([x1-x0,y1-y0,z1-z0]);m.apply_translation([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2]);return m
def extr(poly,h,z=0):
 if hasattr(poly,'geoms'):
  return tm.util.concatenate([extr(p,h,z) for p in poly.geoms if p.area>1e-5])
 m=tm.creation.extrude_polygon(poly,h,engine='earcut');m.apply_translation([0,0,z]);return m
def cyl(r,h,z=0):
 m=tm.creation.cylinder(r,h,sections=192);m.apply_translation([0,0,z+h/2]);return m
def union(*ms):return tm.boolean.union(list(ms),engine='manifold')
def diff(a,*ms):return tm.boolean.difference([a,*ms],engine='manifold')
def semicircle(ro,ri):return Point(0,0).buffer(ro,quad_segs=48).difference(Point(0,0).buffer(ri,quad_segs=48)).intersection(rect(-ro-1,-ro-1,ro+1,0))
def wave_centerlines(bounds,pitch=24.,step=10.5):
 """四重の扇を上の扇で隠す。同じ単純半円を重ねて交差させない青海波。"""
 x0,y0,x1,y1=bounds;clip=rect(x0,y0,x1,y1);cover=Polygon();visible=[]
 rmax=pitch/2
 rows=range(int(np.floor(y0/step))-2,int(np.ceil(y1/step))+2)
 for row in reversed(list(rows)):
  cy=row*step;shift=pitch/2*(row%2);filled=[]
  for col in range(int(np.floor(x0/pitch))-2,int(np.ceil(x1/pitch))+2):
   cx=col*pitch+shift
   for r in (rmax*.23,rmax*.46,rmax*.69,rmax*.92):
    a=np.linspace(0,np.pi,61);line=LineString(np.c_[cx+r*np.cos(a),cy+r*np.sin(a)])
    g=line.difference(cover).intersection(clip)
    if not g.is_empty:visible.append(g)
   disk=Point(cx,cy).buffer(rmax,quad_segs=48).intersection(rect(cx-rmax-1,cy,cx+rmax+1,cy+rmax+1));filled.append(disk)
  cover=unary_union([cover,*filled])
 return unary_union(visible)
def wave_lines(clip):
 return wave_centerlines(clip.bounds).buffer(.6,cap_style='round',join_style='round').intersection(clip)
def double_curve(n=256,offset=0.,corner_radius=None):
 """Tangent R100 side / R30 corner arcs. Offset is an exact parallel curve.
 Four quadrants, sampled at uniform arc length; normals stay continuous at joins.
 """
 R=P['SIDE_R'];r=P['CORNER_R'] if corner_radius is None else float(corner_radius);d=R-P['OUTER_W']/2
 a=(-d+np.sqrt(2*(R-r)**2-d*d))/2
 alpha=np.arctan2(a,a+d);lengths=np.array([R*alpha,r*(np.pi/2-2*alpha),R*alpha]);L=sum(lengths)
 xy=[];normals=[]
 for s in np.arange(n)*(4*L/n):
  quadrant=int(s/L);u=s-quadrant*L
  if u<lengths[0]:t=u/R;c=np.array([-d,0]);radius=R
  elif u<sum(lengths[:2]):t=alpha+(u-lengths[0])/r;c=np.array([a,a]);radius=r
  else:t=np.pi/2-alpha+(u-sum(lengths[:2]))/R;c=np.array([0,-d]);radius=R
  normal=np.array([np.cos(t),np.sin(t)]);point=c+(radius+offset)*normal
  ang=quadrant*np.pi/2;rot=np.array([[np.cos(ang),-np.sin(ang)],[np.sin(ang),np.cos(ang)]])
  xy.append(rot@point);normals.append(rot@normal)
 return np.array(xy),np.array(normals),4*L
P['OUTER_PERIMETER']=float(double_curve()[2]);P['PATTERN_PITCH']=P['OUTER_PERIMETER']/12
def ring_solid(rings):
 n=len(rings[0]);vs=np.concatenate(rings).tolist();faces=[];nr=len(rings)
 for j in range(nr-1):
  for i in range(n):
   a=j*n+i;b=j*n+(i+1)%n;c=(j+1)*n+i;d=(j+1)*n+(i+1)%n;faces.extend([[a,b,c],[b,d,c]])
 bot=len(vs);vs.append([0,0,rings[0][0,2]]);top=len(vs);vs.append([0,0,rings[-1][0,2]])
 for i in range(n):faces.extend([[bot,(i+1)%n,i],[top,(nr-1)*n+i,(nr-1)*n+(i+1)%n]])
 m=tm.Trimesh(vs,faces,process=False);m.fix_normals();return m
def cap_solid():
 xy,normals,_=double_curve(256,2.);rings=[]
 for z in np.r_[np.linspace(0,4,17),6.,np.linspace(6,10,17)[1:]]:
  inset=1.3*(1+np.cos(np.pi*z/4))/2 if z<=4 else (.6*(1-np.cos(np.pi*(z-6)/4))/2 if z>6 else 0.)
  rings.append(np.c_[xy-inset*normals,np.full(len(xy),z)])
 return ring_solid(rings)
def patterned_shell():
 n=256;xy,normals,circ=double_curve(n);ss=np.arange(n)*circ/n;period=P['PATTERN_PITCH']
 lines=wave_centerlines((-period,40,circ+period,205),period,11.25)
 pts=[]
 def sample(g):
  if g.geom_type=='LineString':
   for d in np.linspace(0,g.length,max(2,int(g.length/.18)+1)):pts.append(g.interpolate(d).coords[0])
  elif hasattr(g,'geoms'):
   for q in g.geoms:sample(q)
 sample(lines);tree=cKDTree(np.array(pts))
 zs=np.r_[np.linspace(0,6,16),53.,np.linspace(55.,190.,226),192.,P['BODY_L']-2,np.linspace(P['BODY_L']-1.9,P['BODY_L'],8)]
 rings=[]
 for z in zs:
  dd=tree.query(np.c_[ss,np.full(n,z)])[0]
  dep=np.minimum(.6*np.clip(1-dd/1.2,0,1),max(0,.5*min(z-55,190-z)))
  # Preserve at least1.3mm wall around the expanded glue socket.
  # Fade the ornament into an intentional plain joining band.
  a=P['BODY_SPLIT_Z']-2;b=P['BODY_SPLIT_Z']+15
  fade=np.clip((a-z)/2,0,1) if z<a else (np.clip((z-b)/2,0,1) if z>b else 0.)
  dep*=fade
  inset=0.
  if z<6:inset=1.5*(1+np.cos(np.pi*z/6))/2
  if z>P['BODY_L']-2:inset=.6*(1-np.cos(np.pi*(z-P['BODY_L']+2)/2))/2
  rings.append(np.c_[xy-(inset+dep)[:,None]*normals,np.full(n,z)])
 m=ring_solid(rings)
 m=diff(m,cyl(P['ID']/2,P['BODY_L'],3))
 return diff(m,*[sphere(P['DETENT_POCKET_R'],[sign*P['DETENT_X'],P['DETENT_Y'],P['CLOSED_L']-P['DETENT_Z']]) for sign in [-1,1]])
def roof_window(bottom,shoulder,half_width,x0,x1):
 top=shoulder+(half_width-2)/.55
 poly=Polygon([(-half_width,bottom),(half_width,bottom),(half_width,shoulder),(2,top),(-2,top),(-half_width,shoulder)])
 cut=extr(poly,x1-x0)
 cut.apply_transform(np.array([[0,0,1,x0],[1,0,0,0],[0,1,0,0],[0,0,0,1]],float))
 return cut
def cone_cavity_profile(end):
 """Full-width continuous circular profile:45deg at mouth to30deg at4mm roof.

 No straight cone run and no delayed tip-only blend. Angles are to print bed.
 """
 beta0=np.deg2rad(45.);beta1=np.deg2rad(60.)
 rt=P['TRAY_INNER_R'];rf=P['END_BRIDGE_D']/2
 R=(rt-rf)/(np.cos(beta0)-np.cos(beta1))
 roof=end-P['STOP_T'];start=roof-R*(np.sin(beta1)-np.sin(beta0))
 rc=rt-R*np.cos(beta0);zc=start-R*np.sin(beta0)
 points=[(rt,start-.1)]+[(rc+R*np.cos(t),zc+R*np.sin(t)) for t in np.linspace(beta0,beta1,193)]
 points[-1]=(rf,roof)
 P['END_BLEND_L']=roof-start;P['END_TIP_R']=R
 P['END_FINAL_BRIDGE_D']=2*rf;P['END_TERMINAL_ANGLE_FROM_BED']=30.
 P['END_ROUND_START_Z']=start;P['END_ROUND_START_D']=2*rt
 P['END_ACTUAL_ROOF_Z']=roof;P['END_ACTUAL_ROOF_T']=end-roof
 dr,dz=np.diff(np.array(points[-2:]),axis=0)[0]
 P['END_LAST_CHORD_ANGLE_FROM_BED']=float(np.rad2deg(np.arctan2(dz,-dr)))
 assert abs(P['END_LAST_CHORD_ANGLE_FROM_BED']-30)<.3
 return points

END_PROFILE=cone_cavity_profile(P['TRAY_END'])

def sphere(r,center):
 m=tm.creation.uv_sphere(radius=r,count=[16,24]);m.apply_translation(center);return m

def trough_profiles():
 # Width stays64 at the open mouth; flatten both lower boundaries to preserve2mm floor.
 outer=Point(0,0).buffer(P['TRAY_R'],quad_segs=48).intersection(rect(-40,P['FLAT_OUTER_Y'],40,0))
 inner=Point(0,0).buffer(P['TRAY_INNER_R'],quad_segs=48).intersection(rect(-40,P['FLAT_INNER_Y'],40,1))
 return outer,inner,outer.difference(inner)

def make_cap():
 _,_,section=trough_profiles()
 cap_clip=Polygon(double_curve(256,-2.3)[0])
 cap=diff(cap_solid(),extr(wave_lines(cap_clip),.61,-.01))
 # Deep U-shaped keyed socket, front face remains >=3.8mm thick.
 cap=diff(cap,extr(section.buffer(P['CAP_JOINT_GAP'],join_style='round'),6.21,3.8))
 # Two short, captive shoulders retain the assembly cap when the round body detents release.
 return diff(cap,*[box(32.55,-8.5,4.4,34.1,-5.5,7.65) if sign==1 else box(-34.1,-8.5,4.4,-32.55,-5.5,7.65) for sign in [-1,1]])

def make_drawer(end=249.8,end_stop=True,decorate=True):
 outer_poly,_,section=trough_profiles()
 trough=extr(section,end-10,10)
 tongue=extr(section,6.05,4.)
 # One-time assembly snaps: solid short lugs, no long flexible clip.
 lugs=[]
 for sign in [-1,1]:
  profile=Polygon([(sign*32.8,4.6),(sign*33.85,6.2),(sign*33.85,7.4),(sign*32.8,7.4)])
  lug=extr(profile,2.5);lug.apply_transform(np.array([[1,0,0,0],[0,0,-1,-5.75],[0,1,0,0],[0,0,0,1]],float));lugs.append(lug)
 tongue=union(tongue,*lugs)
 if end_stop:
  profile=cone_cavity_profile(end);start=profile[0][1]+.1
  theta=np.arange(192)*2*np.pi/192
  rings=[np.c_[r*np.cos(theta),r*np.sin(theta),np.full(192,z)] for r,z in profile]
  outer=extr(outer_poly,end-start,start)
  stop=diff(outer,ring_solid(rings));m=union(trough,tongue,stop)
 else:m=union(trough,tongue)
 bosses=[diff(sphere(P['DETENT_R'],[sign*P['DETENT_X'],P['DETENT_Y'],P['DETENT_Z']]),cyl(P['TRAY_INNER_R'],6,P['DETENT_Z']-3)) for sign in [-1,1]]
 return union(m,*bosses)

def pressed(mesh):
 # Kinematic pass representation only: the two detents compress into the sliding bore.
 # This is not a material/force simulation and no rated click force is inferred.
 return tm.boolean.intersection([mesh,cyl(P['ID']/2-.05,300,-1)],engine='manifold')

def split_body(shell):
 z=P['BODY_SPLIT_Z'];L=P['GLUE_L'];ri=P['GLUE_INNER_R']
 lower=tm.boolean.intersection([shell,box(-50,-50,-1,50,50,z)],engine='manifold')
 upper=tm.boolean.intersection([shell,box(-50,-50,z,50,50,300)],engine='manifold')
 theta=np.arange(192)*2*np.pi/192
 collar=diff(cyl(P['GLUE_R'],L,z),cyl(ri,L+.02,z-.01))
 lower=union(lower,collar)
 # Female socket blends back to the unchanged38mm sliding radius.
 rings=[np.c_[r*np.cos(theta),r*np.sin(theta),np.full(192,h)] for r,h in [(P['GLUE_SOCKET_R'],z-.01),(P['GLUE_SOCKET_R'],z+L),(P['ID']/2,z+L+3.5)]]
 upper=diff(upper,ring_solid(rings))
 upper.apply_translation([0,0,-z])
 return lower,upper
def make_parts():
 lower,upper=split_body(patterned_shell());drawer=make_drawer()
 tip=tm.boolean.intersection([drawer,box(-50,-50,240,50,50,251)],engine='manifold');tip.apply_translation([0,0,-240])
 coupon=diff(extr(Polygon(double_curve()[0]),36),cyl(P['ID']/2,38,-1),*[sphere(P['DETENT_POCKET_R'],[sign*P['DETENT_X'],P['DETENT_Y'],46-P['DETENT_Z']]) for sign in [-1,1]])
 return {'shell_lower':lower,'shell_upper':upper,'drawer':drawer,'cap':make_cap(),'shell_coupon':coupon,'drawer_coupon':make_drawer(42.,False,False),'tip_coupon':tip}

def print_transform(name,mesh):
 from trimesh.transformations import rotation_matrix as R
 M=R(np.pi/4,[0,0,1])@R(np.pi/2,[1,0,0]) if name in ['drawer','drawer_coupon','tip_coupon'] else np.eye(4)
 copy=mesh.copy();copy.apply_transform(M);M[2,3]-=copy.bounds[0,2]
 return M

def main():
 (PROJ/'models').mkdir(exist_ok=True);parts=make_parts();pickle.dump(parts,open(PROJ/'parts_nominal.pkl','wb'))
 for n,m in parts.items():
  assert m.is_volume and len(m.split())==1,(n,m.is_volume)
  m.export(PROJ/'models'/f'{n}_nominal.stl');print(n,'triangles',len(m.faces),'volume',round(m.volume,2),flush=True)
 out={}
 for n,m in parts.items():
  print('EFC',n,flush=True);oriented=m.copy();oriented.apply_transform(print_transform(n,m));out[n]=pre_expand_first_layer(oriented)
  if len(out[n].faces)>190000:
   import manifold3d as mf
   raw=out[n]
   for tolerance in (.005,.01,.02,.04):
    g=mf.Manifold(mf.Mesh(vert_properties=np.asarray(raw.vertices,np.float32),tri_verts=np.asarray(raw.faces,np.uint32))).simplify(tolerance).to_mesh()
    candidate=tm.Trimesh(np.asarray(g.vert_properties)[:,:3],np.asarray(g.tri_verts),process=False)
    if candidate.is_volume and len(candidate.faces)<190000:
     out[n]=candidate;print('bounded simplify',n,tolerance,len(candidate.faces),flush=True);break
   assert len(out[n].faces)<190000,(n,'triangle budget')
 pickle.dump(out,open(PROJ/'parts.pkl','wb'))
 for n,m in out.items():m.export(PROJ/'models'/f'{n}_print.stl')
 upper=parts['shell_upper'].copy();upper.apply_translation([0,0,P['BODY_SPLIT_Z']])
 shell=tm.util.concatenate([parts['shell_lower'],upper]);pickle.dump({'shell':shell},open(PROJ/'assembled_shell.pkl','wb'))
 o=np.array([[0,0,100]]*3,float);d=np.array([[1,0,0],[-1,0,0],[0,-1,0]],float)
 loc,ids,_=shell.ray.intersects_location(o,d,multiple_hits=True)
 hits={int(i):sorted(np.linalg.norm(loc[ids==i]-o[i],axis=1).tolist()) for i in range(3)}
 dl,_,_=parts['drawer'].ray.intersects_location(o[:1],d[2:],multiple_hits=True);rr=sorted(np.linalg.norm(dl-o[0],axis=1).tolist())
 metrics={'parameters_mm':P,'shell_ray_radii_mm':hits,'drawer_bottom_radii_mm':rr,'measured_body_id_mm':2*min(hits[2]),'nominal_open_tray_id_mm':64.,'measured_radial_gap_mm':P['ID']/2-P['TRAY_R'],'capacity_basis':'User specifies nominal64mm open trough;6 nested length225mm is an assumption. Feathers are compliant and the upper half is open. No rigid68mm exclusion claim; no physical feather compression simulation.','status':'R10 REVIEW; flat horizontal tray; separate keyed cap; rounded detents without long clip; physical fit/click untested'}
 metrics['end_geometry']={'main_angle_from_bed_deg':45.,'terminal_tangent_from_bed_deg':30.,'last_mesh_chord_from_bed_deg':P['END_LAST_CHORD_ANGLE_FROM_BED'],'round_start_z_mm':P['END_ROUND_START_Z'],'final_bridge_mm':4.,'roof_underside_z_mm':P['END_ACTUAL_ROOF_Z'],'roof_thickness_mm':1.25,'outside_filled':True,'angle_reference':'Canonical design axis of R9; tray now prints horizontally, these are not bed overhang angles.'}
 metrics['detent']={'boss_radius_mm':1.6,'pocket_radius_mm':1.85,'boss_outer_radius_x_mm':34.7,'body_bore_radius_mm':34.3,'nominal_radial_interference_mm':.4,'force_N':None,'scope':'Rounded integrated detents, no separate clip. Actual shell/tray compliance and click force untested.'}
 metrics['cap_joint']={'length_mm':6.,'gap_per_side_mm':.2,'mode':'U-shaped key and socket with2 short captive assembly shoulders. Not the body click latch. Retention and one-time insertion compliance require physical check.'}
 metrics['print_transforms']={n:print_transform(n,m).tolist() for n,m in parts.items()}
 metrics['print_dimensions_mm']={n:(m.bounds[1]-m.bounds[0]).tolist() for n,m in out.items()}
 for n,m in out.items():
  pickle.dump({n:m},open(PROJ/'models'/f'{n}_qc.pkl','wb'))
 json.dump(metrics,open(PROJ/'dimensions.json','w'),ensure_ascii=False,indent=2,allow_nan=False);print(json.dumps(metrics,ensure_ascii=False,indent=1,allow_nan=False),flush=True)
if __name__=='__main__':main()
