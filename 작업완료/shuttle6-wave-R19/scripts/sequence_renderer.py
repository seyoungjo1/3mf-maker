# Project-local fixed-camera derivative of tools/render_preview.py; shared tools unchanged.
import os,json,numpy as np
from pathlib import Path
HERE=str(Path(__file__).resolve().parents[3]/'tools')
def render_sequence(parts, out, colors=None, states=None, frames=36, size=(1200,900), gif_size=(640,480), status=None, bed=512, timeline=None):
    """실제 메시의 CPU 평면 음영 렌더. 소켓 생성이 금지된 환경에서도 같은 5뷰/상태/GIF를 만든다."""
    from PIL import Image, ImageDraw, ImageFont
    from matplotlib.colors import to_rgb
    from trimesh.transformations import rotation_matrix
    import ctypes,hashlib,subprocess,tempfile
    src=Path(HERE)/'software_raster.c';digest=hashlib.sha256(src.read_bytes()).hexdigest()[:16]
    libpath=Path(tempfile.gettempdir())/('mm_raster_'+digest+'.so')
    if not libpath.exists():
        temp=str(libpath)+'.'+str(os.getpid())
        subprocess.run(['cc','-shared','-O3','-fPIC',str(src),'-o',temp,'-lm'],check=True,capture_output=True)
        os.replace(temp,libpath)
    lib=ctypes.CDLL(str(libpath));raster=lib.mm_raster
    ptr=np.ctypeslib.ndpointer
    raster.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_int,ptr(np.float32,flags='C_CONTIGUOUS'),ptr(np.uint8,flags='C_CONTIGUOUS'),ptr(np.uint8,flags='C_CONTIGUOUS'),ptr(np.float32,flags='C_CONTIGUOUS')]
    os.makedirs(out,exist_ok=True); colors=colors or {}; pngs={}
    font_path='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    font=ImageFont.truetype(font_path,16) if os.path.exists(font_path) else ImageFont.load_default()
    def placed(st):
        active=(states or {}).get(st,{})
        result=[]
        for i,(n,m) in enumerate(parts.items()):
            if active and n not in active:continue
            a=np.asarray(active.get(n,np.eye(4)),float)
            if a.shape==(3,): M=np.eye(4);M[:3,3]=a
            else:M=a.reshape(4,4)
            v=np.asarray(m.vertices)@M[:3,:3].T+M[:3,3]
            result.append((v,np.asarray(m.faces),np.asarray(to_rgb(colors.get(n,'#37474f')))))
        return result
    endpoints=[placed(next(iter(states))),placed(next(reversed(states)))]
    bound_vertices=np.vstack([v for scene in endpoints for v,_,_ in scene])
    fixed_lo=bound_vertices.min(0);fixed_hi=bound_vertices.max(0)
    corners=np.array([[x,y,z] for x in [fixed_lo[0],fixed_hi[0]] for y in [fixed_lo[1],fixed_hi[1]] for z in [fixed_lo[2],fixed_hi[2]]])
    def draw(st,mode,az,res):
        w,h=res; im=Image.new('RGB',res,'#1a1d21'); d=ImageDraw.Draw(im)
        scene=placed(st); vs=np.vstack([v for v,_,_ in scene]);lo=fixed_lo;hi=fixed_hi;c=(lo+hi)/2
        direction={'top':[.001,-.001,1],'bottom':[.001,-.001,-1],'side':[0,-1,.025],'front':[.25,-1,.2]}.get(mode,[np.sin(np.radians(az)),-np.cos(np.radians(az)),.75])
        front=np.asarray(direction,float);front/=np.linalg.norm(front);right=np.cross([0,0,1],front);right/=np.linalg.norm(right);up=np.cross(front,right)
        pr=np.c_[(corners-c)@right,(corners-c)@up]; span=np.maximum(np.ptp(pr,axis=0),1);sc=min((w-100)/span[0],(h-130)/span[1])
        def proj(v):return np.c_[w/2+(v-c)@right*sc,h/2-15-(v-c)@up*sc]
        if mode!='bottom':
            for q in range(0,bed+1,16):
                for v in (np.array([[q,0,0],[q,bed,0]]),np.array([[0,q,0],[bed,q,0]])):
                    pp=proj(v);d.line([tuple(pp[0]),tuple(pp[1])],fill='#30343b',width=1)
        polygons=[];shades=[];light=np.array([-.35,-.55,.76]);light/=np.linalg.norm(light)
        for v,f,rgb in scene:
            tri=v[f];norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-12)
            visible=norm@front>0
            polys=proj(tri[visible].reshape(-1,3)).reshape(-1,3,2)
            zz=(tri[visible]-c)@front
            polygons.append(np.concatenate([polys,zz[:,:,None]],axis=2))
            # Match the bright hemisphere + key light used by the WebGL preview.
            sh=.7+.55*np.maximum(norm[visible]@light,0);shades.append(np.clip(rgb[None,:]*sh[:,None]*255,0,255).astype(np.uint8))
        tris=np.ascontiguousarray(np.concatenate(polygons),dtype=np.float32);cols=np.ascontiguousarray(np.concatenate(shades),dtype=np.uint8)
        pixels=np.array(im,dtype=np.uint8);zb=np.full((h,w),-1e30,np.float32)
        raster(w,h,len(tris),tris,cols,pixels,zb)
        # Screen-space cavity shading from actual depth; makes recessed geometry legible.
        from scipy.ndimage import grey_closing
        radius=max(1,min(10,int(sc*1.6)));closed=grey_closing(zb,size=(2*radius+1,2*radius+1))
        ao=np.clip((closed-zb-.04)/.5,0,1);ao[zb<-1e20]=0
        pixels=(pixels.astype(float)*(1-.48*ao[:,:,None])).astype(np.uint8)
        im=Image.fromarray(pixels);d=ImageDraw.Draw(im)
        if st:d.text((14,10),st.split(' · ',1)[-1],font=font,fill='#f0f0f0')
        label=status or ('검토 — '+' × '.join(f'{x:.1f}' for x in hi-lo)+' mm')
        d.rectangle([0,h-47,w,h],fill='#23272e');d.text((12,h-38),label+' · CPU mesh render',font=font,fill='#d5d9df')
        return im
    imgs=[];durations=[]
    for index,item in enumerate(timeline):
        label=item['state'];im=draw(label,'iso',-35,gif_size)
        if item.get('hold'):
            im.save(os.path.join(out,f"stage_{item['stage']:02d}.png"))
        imgs.append(im.quantize(colors=192));durations.append(item['duration_ms'])
        if index%12==0: print('Frame',index+1,'/',len(timeline),flush=True)
    imgs[0].save(os.path.join(out,'opening_six_steps.gif'),save_all=True,append_images=imgs[1:],duration=durations,loop=0,disposal=2)
    json.dump({'backend':'software','camera':'fixed angle, center and scale for entire sequence','timeline':timeline,'frames':len(imgs),'duration_ms':sum(durations),'detent_positions_mm':[0,36,72,108,144,180],'end_stop_mm':225,'note':'Six detent positions include closed.225mm is the separate final end stop. Shuttlecock geometry is the existing rigid dimensional envelope.'},open(os.path.join(out,'sequence_manifest.json'),'w'),ensure_ascii=False,indent=2)
    return len(imgs)
