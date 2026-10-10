#!/usr/bin/env python3
"""모델 정사영을 DWG 스캔 도면과 같은 축척으로 겹치고, 처마 단면(열별 위·아래 높이)을 표로 낸다.
view=front: refs/scan_front.jpg — 바깥 기둥 중심 574/1373 px = ±SPAN_X/2, 월대 윗면 836 px (기둥 검출)
view=side : refs/scan_side_a.jpg(좌측면) — DWG S4 IMAGE 정합: 바깥 기둥 74783/90189 → 562.5/1010.6 px, 기준선 18888 → 797 px. 오른쪽 = 정면(-y)
출력: qc/v2/overlay_{view}.png(스캔+모델 외곽 빨강), silhouette_{view}.png(회색 겹침/초록 스캔만/빨강 모델만), 표 stdout"""
import glob, os, sys, numpy as np, trimesh
from PIL import Image, ImageDraw, ImageFilter
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); import params as P
ROOT=os.path.join(HERE,'..','..'); view=sys.argv[1] if len(sys.argv)>1 else 'front'
if view=='front':
    scan_f='scan_front.jpg'; px0,px1=574,1373; span=P.SPAN_X; base=836; proj=lambda p:(p[:,0], p[:,2]); depth=lambda t: t[:,1].mean()
else:
    scan_f='scan_side_a.jpg'; px0,px1=522.0,1055.6; span=P.SPAN_Y; base=797; proj=lambda p:(-p[:,1], p[:,2]); depth=lambda t: t[:,0].mean()
scan=Image.open(os.path.join(ROOT,'refs',scan_f)).convert('RGB'); W,H=scan.size
mmpx=span/(px1-px0); cx=(px0+px1)/2
HEX={'gray':(158,158,158),'brown':(109,76,65),'white':(245,245,245),'green':(46,125,50),'tile':(38,50,56)}
import json
cols={k:v for k,v in (s.split('=') for s in open(os.path.join(ROOT,'qc','v2_colors.txt')).read().split(','))}
tris=[]
for f in sorted(glob.glob(os.path.join(ROOT,'models','v2','asm','*.stl'))):
    n=os.path.basename(f)[:-4]; m=trimesh.load(f)
    if len(m.faces)>250000:                                                    # 단순화하면 취두 같은 작은 부재가 뭉개진다(2026-10-10) → 사실상 끔
        import fast_simplification as fs
        v,fc=fs.simplify(np.asarray(m.vertices,np.float32), np.asarray(m.faces), target_reduction=1-250000/len(m.faces)); m=trimesh.Trimesh(v,fc)
    c=np.array([int(cols[n][i:i+2],16) for i in (1,3,5)]); nz=m.face_normals; sh=0.55+0.45*np.clip(np.abs(nz[:,0 if view=='side' else 1])*0.8+nz[:,2]*0.4,0,1)
    for t,s in zip(m.triangles,sh): tris.append((depth(t), t, tuple(int(v) for v in np.clip(c*s,0,255))))
tris.sort(key=lambda r:-r[0] if view=='front' else -r[0])
img=Image.new('RGB',(W,H),(20,22,26)); d=ImageDraw.Draw(img)
for _,t,cl in tris:
    u,z=proj(t); d.polygon([(cx+a/mmpx, base-b/mmpx) for a,b in zip(u,z)], fill=cl)
out=os.path.join(ROOT,'qc','v2'); img.save(os.path.join(out,f'ortho_{view}_model.png'))
S=np.asarray(scan).astype(int).sum(2)>90; M=np.asarray(img).astype(int).sum(2)>90
edge=np.asarray(Image.fromarray((M*255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES))>0
ov=np.asarray(scan).copy(); ov[edge]=[255,40,40]; Image.fromarray(ov).save(os.path.join(out,f'overlay_{view}.png'))
diff=np.zeros((H,W,3),np.uint8); diff[S&M]=[150,150,150]; diff[S&~M]=[40,220,60]; diff[M&~S]=[230,40,40]; Image.fromarray(diff).save(os.path.join(out,f'silhouette_{view}.png'))
def edges(mask,x,r0,r1):
    ys=np.where(mask[r0:r1,x])[0]; return (r0+ys.min(), r0+ys.max()) if len(ys) else (None,None)
f=lambda r: None if r is None else round((base-r)*mmpx,1)
print(f'[{view}] mm/px {mmpx:.4f}  열별 (모델 좌표 mm) 스캔 위/아래 vs 모델 위/아래 — 오른쪽 끝부터')
for lab,(z0,z1) in (('하층',(25,70)),('상층',(68,110))):
    r0,r1=int(base-z1/mmpx),int(base-z0/mmpx); print(lab)
    for uu in np.arange(-125, -60, 4.0):
        x=int(cx+uu/mmpx)
        if 0<=x<W:
            s=edges(S,x,r0,r1); m=edges(M,x,r0,r1); print(f'  u {uu:6.1f}  scan {f(s[0])} {f(s[1])}   model {f(m[0])} {f(m[1])}')
