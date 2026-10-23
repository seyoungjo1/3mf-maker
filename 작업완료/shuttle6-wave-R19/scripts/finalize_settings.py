from pathlib import Path
import sys,zipfile,hashlib,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT/'tools'))
from bambu_project import verify_bambu_project
p=O/'models/Shuttle6_C_R19_keyring5_bambu.3mf'
with zipfile.ZipFile(p) as z:data={n:z.read(n) for n in z.namelist()}
before={n:hashlib.sha256(v).hexdigest() for n,v in data.items() if n.startswith('3D/')}
r=ET.fromstring(data['Metadata/model_settings.config']);changed=[]
for ob in r.findall('object'):
 md={v.get('key'):v for v in ob.findall('metadata')};name=md.get('name').get('value')
 if name in ['stop_left','stop_right']:
  assert 'enable_support' in md;md['enable_support'].set('value','1');changed.append(name)
data['Metadata/model_settings.config']=ET.tostring(r,encoding='utf-8',xml_declaration=True)
with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for n,v in data.items():z.writestr(n,v)
with zipfile.ZipFile(p) as z:after={n:hashlib.sha256(z.read(n)).hexdigest() for n in before}
assert before==after
result=verify_bambu_project(str(p));assert result['ok'],result
json.dump({'changed_support_enabled':changed,'all_geometry_bytes_unchanged':before==after,'final_vendor_verification':result},open(O/'qc/settings_finalized.json','w'),ensure_ascii=False,indent=2)
print('FINAL SETTINGS VERIFIED',changed,flush=True)
