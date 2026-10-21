"""Three main review states, rendered through standard mm after full QC/assembly."""
from pathlib import Path
import json,pickle,sys
P=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(P.parent.parent/'tools'));sys.path.insert(0,str(P/'scripts'))
import mm
if not json.load(open(P/'qc/run_R11.json')).get('ok'):
 raise SystemExit('Full review pipeline must pass first')
from assembly import define
parts=pickle.load(open(P/'parts_nominal.pkl','rb'));assembly=define(parts)
shell=pickle.load(open(P/'assembled_shell.pkl','rb'))['shell']
pickle.dump({'shell':shell,'drawer':parts['drawer'],'cap':parts['cap'],'shell_lower':parts['shell_lower'],'shell_upper':parts['shell_upper']},open(P/'review_parts.pkl','wb'))
states={k:{n:M.ravel().tolist() for n,M in assembly['states'][k].items()} for k in ['닫힘','열림','분리']}
from trimesh.transformations import translation_matrix as T
G=assembly['states']['몸통 접착']['shell_lower']
from build import P as dims
states['몸통 두조각']={'shell_lower':G.ravel().tolist(),'shell_upper':(G@T([0,0,dims['BODY_SPLIT_Z']+30])).ravel().tolist()}
json.dump(states,open(P/'figures/review_states_R11.json','w'),ensure_ascii=False,indent=1)
print(json.dumps(mm.run('render',files=[str(P/'review_parts.pkl')],out=str(P/'preview_R11'),colors={'shell':'#33383e','shell_lower':'#33383e','shell_upper':'#33383e','drawer':'#bd6f53','cap':'#bd6f53'},states=states,frames=36,status='완료 — C안 R11 · 몸통만 접착2분할 · 공칭 내경64 · 내관 눕힘 · 뚜껑 별도 · 둥근 딸깍 돌기'),ensure_ascii=False))
