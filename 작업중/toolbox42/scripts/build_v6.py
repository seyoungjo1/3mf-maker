#!/usr/bin/env python3
"""v6: 뚜껑만 바뀜 → 플레이트 B(뚜껑 v6 + 로고) 일반 3MF + STL. 사용: python scripts/build_v6.py v5parts.pkl lid_v6.pkl"""
import sys, os, pickle
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); from generic3mf import write_generic_3mf
MODELS=os.path.join(HERE,'..','models'); C1,C2='#30949D','#F2AF38'
P=pickle.load(open(sys.argv[1],'rb')); lid=pickle.load(open(sys.argv[2],'rb')); logo=P['logo'].copy()
b=lid.bounds; d=[40-b[0,0],60-b[0,1],-b[0,2]]; lid=lid.copy(); lid.apply_translation(d); logo.apply_translation(d)
write_generic_3mf(os.path.join(MODELS,'Toolbox42_v6_B_lid_logo.3mf'),[{'name':'lid+logo','parts':[(lid,C1,'lid'),(logo,C2,'logo')]}],'Toolbox42 v6 B')
m=lid.copy(); m.apply_translation(-m.bounds[0]); m.export(os.path.join(MODELS,'Toolbox42_lid_v6.stl')); print('done')
