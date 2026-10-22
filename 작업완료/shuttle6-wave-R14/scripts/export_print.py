"""Export verified R30 geometry on six single-colour P1S plates.

Called by mm make only after the geometry QC / assembly / render pipeline passed.
The Bambu project writer and its metadata verification stay in the standard tools.
"""
from pathlib import Path
import hashlib,json,pickle,sys,zipfile
import numpy as np
P=Path(__file__).resolve().parent.parent;REPO=P.parent.parent
sys.path.insert(0,str(REPO/'tools'))
from generic3mf import write_generic_3mf
from bambu_project import DEFAULT_TEMPLATE

def main():
 # A fresh checkout can reproduce the complete project from this make config.
 required=['qc/review_R14/report.json','parts.pkl','dimensions.json']
 if any(not (P/f).is_file() for f in required):
  import mm
  result=mm.run('make',config=str(P/'pipeline_review.json'))
  assert result['ok'],result
 review=json.load(open(P/'qc/review_R14/report.json'))
 assert not review['warn'] and review['stages']['assembly']['warnings']==0
 assert review['stages']['renders'], 'Geometry preview must exist before printing export'
 dimensions=json.load(open(P/'dimensions.json'))
 assert dimensions['parameters_mm']['CORNER_R']==30
 assert abs(dimensions['measured_radial_gap_mm']-.3)<.001
 parts=pickle.load(open(P/'parts.pkl','rb'))
 colors={'shell_lower':'#33383e','shell_upper':'#33383e','drawer':'#bd6f53','cap':'#bd6f53','shell_coupon':'#33383e','drawer_coupon':'#bd6f53','tip_coupon':'#bd6f53'}
 profiles=json.loads(zipfile.ZipFile(DEFAULT_TEMPLATE).read('Metadata/project_settings.config'))
 cfg=json.load(open(P/'pipeline_final.json'))
 settings=cfg['bambu']['settings']
 for key,value in settings.items():
  assert key in profiles, f'Unsupported setting {key}; available similar keys: {[k for k in profiles if key.split("_")[0] in k]}'
  assert type(value) is type(profiles[key]), (key,type(profiles[key]).__name__)
 printer=str(profiles.get('printer_settings_id',''))
 assert 'P1S' in printer, f'Actual template printer is {printer}'
 assert all('PLA' in str(v) for v in profiles['filament_type'][:2]), profiles['filament_type']
 assert all(abs(float(d)-.4)<1e-6 for d in profiles['nozzle_diameter']), profiles['nozzle_diameter']
 audit={'template':str(Path(DEFAULT_TEMPLATE).relative_to(REPO)),
  'template_sha256':hashlib.sha256(Path(DEFAULT_TEMPLATE).read_bytes()).hexdigest(),
  'printer':printer,'nozzle_diameter':profiles['nozzle_diameter'],
  'filament_type':profiles['filament_type'],'filament_settings_id':profiles['filament_settings_id'],
  'settings_applied':settings,'support_reason':'Horizontal tray: added external flat cradle. Actual geometry QC requires85.4mm2 local support only under front square cap key; no support on long cradle/rail cams. Cap separate face-down. Actual Bambu Studio slicing not yet observed.',
  'geometry_source_sha256':hashlib.sha256((P/'parts.pkl').read_bytes()).hexdigest(),'plates':[]}
 out=P/'models/plates_R14';out.mkdir(exist_ok=True)
 groups=[['shell_lower','shell_upper'],['drawer'],['cap'],['shell_coupon'],['drawer_coupon'],['tip_coupon']]
 for names,file in zip(groups,cfg['plates']):
  objects=[];bounds=[]
  for i,n in enumerate(names):
   mesh=parts[n].copy();assert mesh.is_volume and len(mesh.split())==1
   # Body halves share a bed; both stand on their flat first faces.
   cx=[72.,184.][i] if len(names)==2 else 128.
   b=mesh.bounds;mesh.apply_translation([cx-(b[0,0]+b[1,0])/2,128-(b[0,1]+b[1,1])/2,-b[0,2]])
   assert np.all(mesh.bounds[0]>=-1e-6) and np.all(mesh.bounds[1]<=[256,256,250])
   assert np.all(mesh.bounds[0,:2]-10>=0) and np.all(mesh.bounds[1,:2]+10<=256)
   objects.append({'name':n,'parts':[(mesh,colors[n],n)]});bounds.append({'part':n,'bounds_mm':mesh.bounds.tolist(),'triangles':len(mesh.faces)})
  write_generic_3mf(P/file,objects,title=f'Shuttle6 C R14 {names}',material_order=[colors[names[0]]])
  audit['plates'].append({'file':file,'objects':bounds,'color':colors[names[0]]})
 json.dump(audit,open(P/'profile_settings_R14.json','w'),ensure_ascii=False,indent=2)
 assert sum(len(m.faces) for m in parts.values())<=500000,'Combined file triangle budget'
 dimensions['status']='R14 PRINT EXPORT; body lower/upper glued; full circular64mm chamber with additive external cradle horizontal; separate cap; six paired shallow pull-through detents with lower flat guide; dimensional gauge and assembly checked; physical feather/click/slicing untested'
 json.dump(dimensions,open(P/'dimensions.json','w'),ensure_ascii=False,indent=2,allow_nan=False)
 print(json.dumps(audit,ensure_ascii=False,indent=1))

if __name__=='__main__':main()
