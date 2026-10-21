"""All dimensional sections go through the standard mm API."""
from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(P.parent.parent/'tools'))
import mm
jobs=[
 ('section_tip_macro_R9.png',[str(P/'parts_nominal.pkl')+':drawer'],'y=-0.02',[-4,4],[247.5,250],'R9 actual tip section: tangent30deg / bridge4mm'),
 ('section_radial_R9.png',[str(P/'assembled_shell.pkl'),str(P/'parts_nominal.pkl')+':drawer'],'z=100',None,None,'R9 actual radial section / clearance 0.30 mm'),
 ('section_latch_R9.png',[str(P/'parts_nominal.pkl')+':drawer'],'y=0',[30,44],[0,48],'R9 longer positive latch / nominal mesh'),
 ('section_closed_R9.png',[str(P/'figures/closed_coordinates_R9.pkl')],'x=100',None,None,'R9 closed assembly / actual coordinates'),
 ('section_square_R9.png',[str(P/'assembled_shell.pkl')],'z=210',[-48,48],[-48,48],'R9 body: 82 x 82 / side R100 + corner R30'),
 ('section_cap_R9.png',[str(P/'parts_nominal.pkl')+':drawer'],'z=5',[-48,48],[-48,48],'R9 cap: 86 x 86 / side R102 + corner R32'),
 ('section_glue_R9.png',[str(P/'assembled_shell.pkl')],'z=125',[-45,45],[-45,45],'R9 glue: male OD78.8 / socket ID79.4 / slide ID76'),
 ('section_capacity_R9.png',[str(P/'parts_nominal.pkl')+':drawer',str(P/'content_envelopes.pkl')],'x=0',[-40,40],[180,253],'R9 filled cone: terminal tangent30deg / final bridge4mm / six shuttles + 1.5 mm'),
]
for name,files,plane,xlim,ylim,title in jobs:
 print(json.dumps(mm.run('section',files=files,plane=plane,out=str(P/'figures'/name),xlim=xlim,ylim=ylim,title=title),ensure_ascii=False))
