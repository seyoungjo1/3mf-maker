"""Narrow dish foot inside the original C exterior; low paired detents."""
import numpy as np,trimesh as tm
from shapely.geometry import Point,Polygon,box as rect
from build import P,extr,box,cyl,union,diff,ring_solid,glue_key,double_curve

def foot_profile():
 return rect(-7.5,-34.3,7.5,-33.3).buffer(.5,quad_segs=12)
def bore_profile(gap=None):
 gap=P['RADIAL_GAP'] if gap is None else gap
 return Point(0,0).buffer(P['TRAY_R']+gap,quad_segs=48).union(foot_profile().buffer(gap,join_style='round'))
def cam_axes(sign):return np.diag([sign,1.,1.])
def rail_cam(sign,z,pocket=False):
 ys=np.linspace(-34.7,-33.5,25);zs=np.linspace(z-3,z+3,25);Y,Z=np.meshgrid(ys,zs,indexing='ij')
 base_x=7.5+np.sqrt(np.maximum(0,.5**2-np.minimum(Y+34.3,0)**2))
 e=(1-np.cos(2*np.pi*(Y+34.7)/1.2))/2;c=(1+np.cos(np.pi*(Z-z)/3))/2
 h=(P['RADIAL_GAP']+P['DETENT_INTERFERENCE'])*e*c;top=np.stack([sign*(base_x+h),Y,Z],axis=-1)
 if pocket:
  # A normal offset of the triangulated height field, not a scaled sphere.
  dxdy=np.gradient(base_x+h,ys,axis=0);dxdz=np.gradient(base_x+h,zs,axis=1)
  n=np.stack([np.full(Y.shape,sign),-dxdy,-dxdz],axis=-1);n/=np.linalg.norm(n,axis=-1)[...,None]
  top+=.2*n
 bottom=np.stack([sign*(base_x-1),Y,Z],axis=-1)
 ny,nz=Y.shape;count=ny*nz;vertices=np.vstack([top.reshape(-1,3),bottom.reshape(-1,3)]);faces=[]
 for i in range(ny-1):
  for j in range(nz-1):
   a=i*nz+j;b=a+1;c0=a+nz;d=c0+1;faces.extend([[a,c0,b],[b,c0,d],[a+count,b+count,c0+count],[b+count,d+count,c0+count]])
 edge=list(range(nz))+[i*nz+nz-1 for i in range(1,ny)]+list(range((ny-1)*nz+nz-2,(ny-1)*nz-1,-1))+[i*nz for i in range(ny-2,0,-1)]
 for a,b in zip(edge,edge[1:]+edge[:1]):faces.extend([[a,b,a+count],[b,b+count,a+count]])
 m=tm.Trimesh(vertices,faces,process=False);m.fix_normals();assert m.is_volume;return m

def pocket_cutters(stations):return [rail_cam(s,z,True) for z in stations for s in [-1,1]]
def joint_row():
 period=P['PATTERN_PITCH'];row=int(P['BODY_SPLIT_Z']//(period*.525))
 return row*period*.525,period/2*(row%2),period*.46

def seam_from_s(ss):
 cy,shift,rr=joint_row();dx=(np.asarray(ss)-shift+P['PATTERN_PITCH']/2)%P['PATTERN_PITCH']-P['PATTERN_PITCH']/2
 return cy+np.minimum(np.sqrt(np.maximum(0,rr*rr-dx*dx)),np.sqrt(rr*rr-2.*2.))

def seam_z(theta):
 xy,_,circ=double_curve(4096);angles=np.unwrap(np.arctan2(xy[:,1],xy[:,0]));a=np.mod(theta,2*np.pi)
 ss=np.interp(a,np.r_[angles,2*np.pi],np.r_[np.arange(len(xy))*circ/len(xy),circ])
 return seam_from_s(ss)
def seam_mask(offset=0.):
 n=2048;t=np.arange(n)*2*np.pi/n;z=seam_z(t)+offset;rings=[]
 for r in [20.,34.,40.,60.]:rings.append(np.c_[r*np.cos(t),r*np.sin(t),z])
 # A graph solid below the seam; the area around the centre is irrelevant to the hollow wall.
 v=np.vstack([np.array([[0,0,joint_row()[0]+offset]]),*rings,np.c_[60*np.cos(t),60*np.sin(t),np.full(n,-2.)],[[0,0,-2.]]]);f=[]
 for i in range(n):f.append([0,1+i,1+(i+1)%n])
 for j in range(3):
  for i in range(n):
   a=1+j*n+i;b=1+j*n+(i+1)%n;c=1+(j+1)*n+i;d=1+(j+1)*n+(i+1)%n;f.extend([[a,c,b],[b,c,d]])
 for i in range(n):
  a=1+3*n+i;b=1+3*n+(i+1)%n;c=1+4*n+i;d=1+4*n+(i+1)%n;f.extend([[a,b,c],[b,d,c],[len(v)-1,d,c]])
 m=tm.Trimesh(v,f,process=False);m.fix_normals();assert m.is_volume;return m

def remake_body_pair(shell):
 z=P['BODY_SPLIT_Z'];L=P['GLUE_L'];z0=joint_row()[0]
 lower=tm.boolean.intersection([shell,seam_mask(-.05)],engine='manifold');upper=diff(shell,seam_mask(.05))
 theta=np.arange(192)*2*np.pi/192
 rings=[np.c_[r*np.cos(theta),r*np.sin(theta),np.full(192,h)] for r,h in [(P['GLUE_R'],z0-.05),(P['GLUE_R'],z+L-1),(P['GLUE_R']-.35,z+L)]]
 clearance_slot=box(-10,-50,z0-1,10,-29,z+L+P['GLUE_TAPER_L']+1)
 collar=diff(ring_solid(rings),cyl(P['ID']/2,z+L-z0+1,z0-.1),clearance_slot)
 lower=union(lower,collar,glue_key())
 rings=[np.c_[r*np.cos(theta),r*np.sin(theta),np.full(192,h)] for r,h in [(P['GLUE_SOCKET_R'],z0-.1),(P['GLUE_SOCKET_R'],z+L),(P['ID']/2,z+L+P['GLUE_TAPER_L'])]]
 socket=diff(ring_solid(rings),clearance_slot)
 upper=diff(upper,socket,glue_key(True))
 bore=extr(bore_profile(),P['BODY_L']+1-P['FLOOR'],P['FLOOR'])
 stations=[P['CLOSED_L']-(P['DETENT_Z']+i*P['DETENT_PITCH']) for i in range(6)]
 lower=diff(lower,bore,*pocket_cutters(stations));upper=diff(upper,bore,*pocket_cutters(stations))
 import manifold3d as mf
 raw=mf.Manifold(mf.Mesh(vert_properties=np.asarray(lower.vertices,np.float32),tri_verts=np.asarray(lower.faces,np.uint32))).simplify(.001).to_mesh()
 lower=tm.Trimesh(np.asarray(raw.vert_properties)[:,:3],np.asarray(raw.tri_verts),process=False)
 pieces=lower.split();assert sum(abs(m.volume) for m in pieces if abs(m.volume)<1e-4)<1e-4
 lower=max(pieces,key=lambda m:abs(m.volume));lower=diff(lower,upper)
 assert lower.is_volume and len(lower.split())==1
 upper.apply_translation([0,0,-z]);return lower,upper

def make_shell_coupon():
 return diff(extr(Polygon(double_curve(256)[0]),36.),extr(bore_profile(),38.,-1.),*pocket_cutters([26.]))
