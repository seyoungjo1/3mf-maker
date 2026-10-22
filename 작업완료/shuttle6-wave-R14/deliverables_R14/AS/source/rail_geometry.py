"""External cradle; unchanged circular chamber; six detent rows inside rail."""
import numpy as np
import trimesh as tm
from shapely.geometry import Point,Polygon
from build import P,extr,box,cyl,union,diff,ring_solid,glue_key,double_curve

def foot_profile():
 r=P['TRAY_R'];s=P['FOOT_SIDE_SLOPE'];bottom=P['FOOT_BOTTOM_Y']
 x=r/np.sqrt(1+s*s);y=-s*x;base=x-s*(y-bottom)
 P.update(FOOT_HALF_BASE=float(base),FOOT_TANGENT_X=float(x),FOOT_TANGENT_Y=float(y))
 return Polygon([(-base,bottom),(base,bottom),(x+.03,y+.1),(-x-.03,y+.1)])

def bore_profile(gap=None):
 gap=P['RADIAL_GAP'] if gap is None else gap
 return Point(0,0).buffer(P['TRAY_R']+gap,quad_segs=48).union(foot_profile().buffer(gap,join_style='round'))

def cam_axes(sign):
 n=np.array([sign,-P['FOOT_SIDE_SLOPE'],0.],float);n/=np.linalg.norm(n)
 t=np.array([sign*P['FOOT_SIDE_SLOPE'],1.,0.]);t/=np.linalg.norm(t)
 return np.column_stack([n,t,[0.,0.,1.]])

def rail_cam(sign,z,pocket=False):
 foot_profile();s=P['FOOT_SIDE_SLOPE'];n=cam_axes(sign)[:,0]
 # Printed bottom to top: 5mm smooth lead-in and 2mm return. The maximum
 # outward step stays below0.115mm per0.2mm layer on the flared cradle.
 y0=-33.8;lead=5.;back=2.;half_z=3.
 ys=np.r_[np.linspace(y0,y0+lead,26),np.linspace(y0+lead,y0+lead+back,13)[1:]]
 zs=np.linspace(z-half_z,z+half_z,25);Y,Z=np.meshgrid(ys,zs,indexing='ij')
 rising=Y<=y0+lead
 t=np.where(rising,(Y-y0)/lead,(Y-y0-lead)/back)
 e=np.where(rising,(1-np.cos(np.pi*t))/2,(1+np.cos(np.pi*t))/2)
 ey=np.where(rising,np.pi*np.sin(np.pi*t)/(2*lead),-np.pi*np.sin(np.pi*t)/(2*back))
 c=(1+np.cos(np.pi*(Z-z)/half_z))/2;cz=-np.pi*np.sin(np.pi*(Z-z)/half_z)/(2*half_z)
 h=(P['RADIAL_GAP']+P['DETENT_INTERFERENCE'])*e*c
 hy=(P['RADIAL_GAP']+P['DETENT_INTERFERENCE'])*ey*c
 hz=(P['RADIAL_GAP']+P['DETENT_INTERFERENCE'])*e*cz
 base=np.stack([sign*(P['FOOT_HALF_BASE']+s*(Y-P['FOOT_BOTTOM_Y'])),Y,Z],axis=-1)
 top=base+h[...,None]*n
 if pocket:
  dy=np.array([sign*s,1.,0.])+hy[...,None]*n
  dz=np.array([0.,0.,1.])+hz[...,None]*n
  normal=sign*np.cross(dy,dz);normal/=np.linalg.norm(normal,axis=-1)[...,None]
  top+=P['DETENT_RELAX_GAP']*normal
 # Positive overlap under the entire patch; no thin separate leaf or neck.
 bottom=base-1.0*n
 ny,nz=Y.shape;count=ny*nz;vertices=np.vstack([top.reshape(-1,3),bottom.reshape(-1,3)])
 faces=[]
 for i in range(ny-1):
  for j in range(nz-1):
   a=i*nz+j;b=a+1;c0=a+nz;d=c0+1
   faces.extend([[a,c0,b],[b,c0,d],[a+count,b+count,c0+count],[b+count,d+count,c0+count]])
 edge=list(range(nz))+[i*nz+nz-1 for i in range(1,ny)]+list(range((ny-1)*nz+nz-2,(ny-1)*nz-1,-1))+[i*nz for i in range(ny-2,0,-1)]
 for a,b in zip(edge,edge[1:]+edge[:1]):faces.extend([[a,b,a+count],[b,b+count,a+count]])
 m=tm.Trimesh(vertices,faces,process=False);m.fix_normals()
 if not m.is_volume:m.invert()
 return m

def pocket_cutters(stations):
 return [rail_cam(sign,z,True) for z in stations for sign in [-1,1]]

def socket():
 z=P['BODY_SPLIT_Z'];L=P['GLUE_L'];tail=P['GLUE_TAPER_L'];theta=np.arange(192)*2*np.pi/192
 rings=[np.c_[r*np.cos(theta),r*np.sin(theta),np.full(192,h)] for r,h in [(P['GLUE_SOCKET_R'],z-.02),(P['GLUE_SOCKET_R'],z+L),(P['ID']/2,z+L+tail)]]
 return tm.boolean.intersection([ring_solid(rings),box(-50,P['COLLAR_CUT_Y']-.15,z-1,50,50,z+L+tail+1)],engine='manifold')

def reinforcement():
 return extr(foot_profile().buffer(P['RADIAL_GAP']+P['FOOT_WALL'],join_style='round'),P['BODY_L'])

def remake_body_pair(shell):
 z=P['BODY_SPLIT_Z'];L=P['GLUE_L']
 lower=tm.boolean.intersection([shell,box(-50,-50,-1,50,50,z)],engine='manifold')
 upper=tm.boolean.intersection([shell,box(-50,-50,z,50,50,300)],engine='manifold')
 theta=np.arange(192)*2*np.pi/192
 rings=[np.c_[r*np.cos(theta),r*np.sin(theta),np.full(192,h)] for r,h in [(P['GLUE_R'],z),(P['GLUE_R'],z+L-1),(P['GLUE_R']-.35,z+L)]]
 collar=diff(ring_solid(rings),cyl(P['ID']/2,L+.1,z-.05),box(-50,-50,z-.05,50,P['COLLAR_CUT_Y'],z+L+.05))
 lower=union(lower,collar,glue_key());upper=diff(upper,socket(),glue_key(True))
 rein=reinforcement()
 lower=union(lower,tm.boolean.intersection([rein,box(-50,-50,-1,50,50,z)],engine='manifold'))
 upper=union(upper,tm.boolean.intersection([rein,box(-50,-50,z,50,50,300)],engine='manifold'))
 upper=diff(upper,socket(),glue_key(True))
 bore=extr(bore_profile(),P['BODY_L']+1-P['FLOOR'],P['FLOOR'])
 stations=[P['CLOSED_L']-(P['DETENT_Z']+i*P['DETENT_PITCH']) for i in range(6)]
 lower=diff(lower,bore,*pocket_cutters(stations));upper=diff(upper,bore,*pocket_cutters(stations))
 upper.apply_translation([0,0,-z]);return lower,upper

def make_shell_coupon():
 outline=Polygon(double_curve(256)[0]).union(foot_profile().buffer(P['RADIAL_GAP']+P['FOOT_WALL']))
 return diff(extr(outline,36.),extr(bore_profile(),38.,-1.),*pocket_cutters([26.]))

def adapt_R13_pair(old_lower,old_upper):
 z=P['BODY_SPLIT_Z']
 old_lower=tm.boolean.intersection([old_lower,box(-50,-50,-1,50,50,z)],engine='manifold')
 old_upper.apply_translation([0,0,z])
 lower=union(old_lower,cyl(35.8,z-P['FLOOR'],P['FLOOR']))
 upper=union(old_upper,cyl(35.8,P['BODY_L']-z,z),cyl(37.4,P['GLUE_L']+P['GLUE_TAPER_L'],z))
 return remake_body_pair(union(lower,upper))
