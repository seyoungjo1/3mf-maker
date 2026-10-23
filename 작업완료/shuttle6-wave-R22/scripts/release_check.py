from pathlib import Path
import json,pickle,hashlib,zipfile
import numpy as np
from PIL import Image
O=Path(__file__).resolve().parent.parent
q=json.load(open(O/'qc/printed_parts.json'));assert len(q)==9 and all(x['watertight'] and x['is_volume'] and x['bodies']==1 and x['faces']<=200000 for x in q);assert sum(x['faces'] for x in q)<=500000
p=pickle.load(open(O/'parts_nominal.pkl','rb'));assert all(m.is_volume and len(m.split())==1 for m in p.values())
a=json.load(open(O/'qc/assembly.json'));assert all(x['body_overlap_mm3']<.01 and x['stop_key_overlap_mm3']<.01 for x in a['slide'] if x['travel_mm']<=225);assert all(x['body_overlap_mm3']<.01 and x['cap_overlap_mm3']<.01 for x in a['latch_sweep']);assert a['gauge_overlap_mm3']<.01
c=json.load(open(O/'qc/cone_checks.json'));assert len(c['receiver_slide_raw_solid_checks'])==9 and max(x['receiver_overlap_mm3'] for x in c['receiver_slide_raw_solid_checks'])<.01;assert c['rear_end_half_disc_thickness_mm']>5.7
s=json.load(open(O/'qc/stop_checks.json'));assert s['body_joint_overlap_mm3']<.01
ex=json.load(open(O/'qc/export_checks.json'));assert ex['bambu_metadata']['ok'] and all(v['warnings']==0 for v in ex['generic_strict'].values()) and all(v['warnings']==0 for v in ex['bambu_geometry_strict'].values());assert len(ex['plate_roundtrip_qc'])==9
f=json.load(open(O/'qc/settings_finalized.json'));assert f['all_geometry_bytes_unchanged'] and f['final_vendor_verification']['ok']
previews={}
for name in ['preview','preview_lock','preview_stops','preview_keyring','preview_dock','preview_front_cone','preview_plates']:
 d=O/name;assert len(list(d.glob('view_*.png')))>=5
 for pth in d.glob('*.png'):
  with Image.open(pth) as im:im.verify()
 with Image.open(d/'turntable.gif') as im:
  frames=im.n_frames;assert frames>=20
  for i in range(frames):im.seek(i);im.load()
 previews[name]={'pngs':len(list(d.glob('*.png'))),'gif_frames':frames}
with Image.open(O/'preview_six_steps/opening_six_steps.gif') as im:
 assert im.n_frames==66
 for i in range(im.n_frames):im.seek(i);im.load()
 previews['preview_six_steps']={'pngs':len(list((O/'preview_six_steps').glob('stage_*.png'))),'gif_frames':im.n_frames}
assert previews['preview_six_steps']['pngs']==8
mf=O/'models/Shuttle6_C_R22_boat_dock_round_front_hat_bambu.3mf'
with zipfile.ZipFile(mf) as z:assert z.testzip() is None
assert max(pth.stat().st_size for pth in O.rglob('*') if pth.is_file())<100_000_000
report={'ok':True,'printed_triangles':sum(x['faces'] for x in q),'single_solids':9,'bambu_file':mf.name,'bambu_sha256':hashlib.sha256(mf.read_bytes()).hexdigest(),'render_integrity':previews,'scope':'Digital geometry, metadata, render and file checks. No physical print or observed Bambu GUI slicing.'}
json.dump(report,open(O/'qc/release_check.json','w'),indent=2);print(json.dumps(report),flush=True)
