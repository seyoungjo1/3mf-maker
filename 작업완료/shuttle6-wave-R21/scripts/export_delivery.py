from pathlib import Path
import sys,pickle,json,hashlib
import numpy as np,trimesh as tm
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'tools'))
from generic3mf import write_generic_3mf
from bambu_project import write_bambu_project,verify_bambu_project,DEFAULT_TEMPLATE
TEMPLATE=OUT/'AS/reference_bambu_template.3mf'
from load3mf import load_parts
from pipeline import inter
import mm
from render_preview import render
assert (OUT/'preview/turntable.gif').is_file() and (OUT/'preview_lock/turntable.gif').is_file()
p=pickle.load(open(OUT/'parts_print.pkl','rb'));qc=json.load(open(OUT/'qc/printed_parts.json'))
assert len(qc)==9 and all(r['watertight'] and r['is_volume'] and r['bodies']==1 for r in qc)
assert all(r['faces']<=200000 for r in qc) and sum(r['faces'] for r in qc)<=500000
assert all(not r['flags'] for r in qc if r['name'] in ['shell_coupon','latch'])
# Remaining flags are explicit local supports or pointed collar/key cut edges.
accept={
 'shell_lower':'5.2mm2 pointed original key lead edge; bulk collar retained; the side pass slots remove residual thin collar tongues.',
 'shell_upper':'Local support at the side runner/pocket roof (68mm2 overhang); wave joint itself retains its original geometry.',
 'drawer':'Local supports under original curved flanks/nubs/front key and the thick open semicircular rear end and original solid side shoulders. Original hat now at the front. No stop spring arms.',
 'cap':'8.8mm2 pointed non-bearing tail corners on pivot-ear gussets;4mm-wide pivot ears and root bulk are retained.',
 'stop_left':'80.4mm2 flat inner face requires10mm brim and local supports for its5.7mm bridge.0.142mm final contour reduction follows original C exterior curvature. Local contour-end thin flags are on the flush head tips; the axial load-bearing stem remains4mm thick.',
 'stop_right':'Same geometry and print requirements as stop_left.',
 'drawer_coupon':'Local outer curved flank/nub supports.'}
json.dump({'parts':qc,'accepted_with_reason':accept,'scope':'Raw QC flags retained. This report does not call supported parts support-free.'},open(OUT/'qc/release_geometry.json','w'),ensure_ascii=False,indent=2)
settings=json.load(open(OUT/'AS/reference_print_settings.json'))['bambu']['settings']
settings['bridge_no_support']='0'
colors={'shell_lower':'#33383e','shell_upper':'#33383e','drawer':'#bd6f53','cap':'#bd6f53','latch':'#ffb300','shell_coupon':'#33383e','drawer_coupon':'#bd6f53','stop_left':'#33383e','stop_right':'#33383e'}
groups=[['shell_lower','shell_upper'],['drawer'],['cap'],['latch'],['shell_coupon'],['drawer_coupon'],['stop_left','stop_right']]
labels=['몸통2조각·위통 입구 아래','일체형 내관·대각선','뚜껑·양쪽 지지귀','반대 방향 클립·평면 아래','외관 딸깍 시험편','내관 딸깍 시험편','좌우 멈춤블록·10mm 브림']
plates=[];generic=[];roundtrip=[];renderparts={};renderstates={}
(OUT/'models/plates').mkdir(exist_ok=True)
for i,(names,label) in enumerate(zip(groups,labels),1):
 objects=[];gobs=[];placed=[]
 for j,n in enumerate(names):
  q=p[n].copy();center=[72,184][j] if len(names)==2 else 128
  q.apply_translation([center-q.bounds[:,0].mean(),128-q.bounds[:,1].mean(),-q.bounds[0,2]])
  assert np.all(q.bounds[0]>=-1e-5) and np.all(q.bounds[1]<=[256.00001,256.00001,250.00001])
  assert np.all(q.bounds[0,:2]-8>=0) and np.all(q.bounds[1,:2]+8<=256)
  objects.append({'name':n,'parts':[(q,n,2 if n in ['drawer','cap','drawer_coupon'] else(3 if n=='latch' else 1))], 'object_settings':{'enable_support':'1' if n in ['drawer','shell_upper','drawer_coupon','stop_left','stop_right'] else '0','bridge_no_support':'0'}})
  gobs.append({'name':n,'parts':[(q,colors[n],n)]});placed.append((n,q))
  renderparts[n]=q;renderstates.setdefault(label,{})[n]=[0,0,0]
 if len(placed)==2:assert inter(placed[0][1],placed[1][1])<.01
 file=OUT/'models/plates'/f'P{i:02d}.3mf';write_generic_3mf(file,gobs,title='Shuttle6 R21 '+label,material_order=['#33383e','#bd6f53','#ffb300']);generic.append(str(file))
 loaded=load_parts(str(file))
 for n,q in placed:
  r=loaded[n];assert r.is_volume and len(r.split())==1 and len(r.faces)==len(q.faces)
  # XML serializer has6 decimals; all actual plate vertex coordinates checked.
  err=float(np.max(np.abs(r.vertices-q.vertices)));assert err<.00002,(n,err)
  roundtrip.append({'plate':i,'part':n,'max_vertex_error_mm':err,'bounds_mm':r.bounds.tolist(),'single_solid':True,'source_qc':next(x for x in qc if x['name']==n)})
 plates.append({'name':f'{i:02d} {label}','objects':objects})
strict=mm.run('check3mf',files=generic);assert all(x['warnings']==0 for x in strict.values()),strict
out=OUT/'models/Shuttle6_C_R21_boat_dock_front_hat_bambu.3mf'
write_bambu_project(str(out),[],plates=plates,template=TEMPLATE,filament_colours=['#33383e','#bd6f53','#ffb300'],settings=settings,title='Shuttle6 R21 front hat boat dock thinner housing')
v=verify_bambu_project(str(out),template=TEMPLATE);print('BAMBU_VERIFY',json.dumps(v),flush=True)
assert v['ok'],v
bstrict=mm.run('check3mf',files=[str(out)],bambu_geometry=True);assert all(x['warnings']==0 for x in bstrict.values()),bstrict
json.dump({'generic_strict':strict,'bambu_geometry_strict':bstrict,'bambu_metadata':v,'plate_roundtrip_qc':roundtrip,'actual_bambu_studio_slice_observed':False},open(OUT/'qc/export_checks.json','w'),ensure_ascii=False,indent=2)
json.dump({'settings':settings,'source':'R15 verified actual user Bambu template settings','template':str(TEMPLATE),'template_sha256':hashlib.sha256(Path(TEMPLATE).read_bytes()).hexdigest()},open(OUT/'profile_settings.json','w'),ensure_ascii=False,indent=2)
render(renderparts,str(OUT/'preview_plates'),colors=colors,states=renderstates,frames=36,status='완료 — R21 · P1S 256mm · 국부 서포트: 내관·위통 옆 슬롯·내관 시험편 / 클립·아래통 불필요 / 멈춤블록 브림')
print('EXPORT COMPLETE',out,flush=True)
