#!/usr/bin/env python3
"""모델 정면 정사영을 도면 정면 스캔(refs/scan_front.jpg)과 같은 축척으로 그려 겹친다.
축척: 스캔의 바깥 기둥 중심(574 px, 1373 px) = 모델 ±SPAN_X/2, 월대 윗면 = 836 px.
출력: qc/v2/ortho_front_model.png, overlay_front.png(스캔 + 모델 외곽 빨강)"""
import glob, os, sys, numpy as np, trimesh
from PIL import Image, ImageDraw, ImageFilter
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); import params as P
ROOT=os.path.join(HERE,'..','..')
scan=Image.open(os.path.join(ROOT,'refs','scan_front.jpg')).convert('RGB'); W,H=scan.size
mmpx=P.SPAN_X/(1373-574); x0px=(574+1373)/2; zbase=836
col={'gray':(158,158,158),'brown':(109,76,65),'white':(245,245,245),'green':(46,125,50),'tile':(38,50,56)}
def c(n):
    if n=='platform': return col['gray']
    if n.endswith('white') or n.endswith('ridge'): return col['white']
    if 'green' in n: return col['green']
    if n.endswith('tile'): return col['tile']
    return col['brown']
tris=[]
for f in sorted(glob.glob(os.path.join(ROOT,'models','v2','asm','*.stl'))):
    n=os.path.basename(f)[:-4]; m=trimesh.load(f)
    if len(m.faces)>60000:
        import fast_simplification as fs
        v,fc=fs.simplify(np.asarray(m.vertices,np.float32), np.asarray(m.faces), target_reduction=1-60000/len(m.faces)); m=trimesh.Trimesh(v,fc)
    nz=m.face_normals; shade=0.55+0.45*np.clip(-nz[:,1]*0.8+nz[:,2]*0.4,0,1); base=np.array(c(n))
    for t,s in zip(m.triangles,shade): tris.append((t[:,1].mean(), t, tuple(int(v) for v in np.clip(base*s,0,255))))
tris.sort(key=lambda r:-r[0])
img=Image.new('RGB',(W,H),(20,22,26)); d=ImageDraw.Draw(img)
for _,t,cl in tris: d.polygon([(x0px+p[0]/mmpx, zbase-p[2]/mmpx) for p in t], fill=cl)
out=os.path.join(ROOT,'qc','v2'); os.makedirs(out,exist_ok=True); img.save(os.path.join(out,'ortho_front_model.png'))
mask=(np.asarray(img).sum(2)>90).astype(np.uint8)*255
edge=np.asarray(Image.fromarray(mask).filter(ImageFilter.FIND_EDGES))>0
ov=np.asarray(scan).copy(); ov[edge]=[255,40,40]; Image.fromarray(ov).save(os.path.join(out,'overlay_front.png'))
print('saved', out)
