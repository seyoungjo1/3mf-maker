"""사용자 Bambu Studio(02.08.02.61, P1S)가 내보낸 sample/test+lunch+box(1).3mf 의 project_settings.config 를
기준(ground truth)으로, 필라멘트를 PLA Basic n개로 바꾼 project_settings 를 만든다.
- 키 집합은 샘플과 동일(추가/삭제 없음). 값 형식(문자열/문자열 배열)도 동일.
- 필라멘트별 키: Bambu Studio 소스 Preset.cpp s_Preset_filament_options, 변형(variant)별 키: PrintConfig.cpp filament_options_with_variant.
- PLA 값은 공식 프로파일 체인 fdm_filament_common → fdm_filament_pla → Bambu PLA Basic @base → (include fdm_filament_template_direct_dual) → Bambu PLA Basic @BBL P1S 0.4 nozzle.
"""
import json, re, sys, os
# BambuStudio 소스 체크아웃 위치 (환경변수 BBS_SRC). 준비: git clone --depth 1 --filter=blob:none --sparse https://github.com/bambulab/BambuStudio
#   git sparse-checkout set --no-cone /src/libslic3r/Preset.cpp /src/libslic3r/PrintConfig.cpp '/resources/profiles/BBL/filament/*.json'
BBS=os.environ.get('BBS_SRC','BambuStudio'); PROF=os.path.join(BBS,'resources/profiles/BBL/filament/'); SRC=os.path.join(BBS,'src/libslic3r/')
def cpp_set(path, name):
    txt=open(path,encoding='utf-8',errors='ignore').read()
    m=re.search(name+r'\s*\{(.*?)\};', txt, re.S); body=re.sub(r'//[^\n]*','',m.group(1)); return set(re.findall(r'"([^"]+)"',body))
FIL_OPTS=cpp_set(SRC+'Preset.cpp','s_Preset_filament_options')
VARIANT=cpp_set(SRC+'PrintConfig.cpp','std::set<std::string> filament_options_with_variant =')
def load_chain(name):
    """inherits/include 체인을 아래부터 합친다 (파일 자체 값이 최우선)."""
    d=json.load(open(PROF+name+'.json',encoding='utf-8')); out={}
    if 'inherits' in d: out.update(load_chain(d['inherits']))
    for inc in d.get('include',[]): out.update(load_chain(inc))
    out.update({k:v for k,v in d.items() if k not in ('inherits','include','type','name','from','instantiation','setting_id','filament_id')})
    return out
def build(sample_path, out_path, n_fil, colours, pla_profile='Bambu PLA Basic @BBL P1S 0.4 nozzle', filament_id='GFA00', overrides=None):
    S=json.load(open(sample_path,encoding='utf-8')); P=load_chain(pla_profile)
    nvar=len(S['filament_extruder_variant'])   # 샘플: 필라멘트 1개에 변형 2개(Standard/High Flow)
    out={}
    for k,v in S.items():
        if k in VARIANT and isinstance(v,list):
            per=P.get(k); 
            if per is None: per=v[:nvar]
            per=list(per)+[per[-1]]*(nvar-len(per)) if len(per)<nvar else per[:nvar]
            out[k]=[str(x) for x in per]*n_fil
        elif k in FIL_OPTS and isinstance(v,list):
            per=P.get(k); val=str(per[0]) if isinstance(per,list) else (str(per) if per is not None else v[0])
            out[k]=[val]*n_fil
        else: out[k]=v
    # 필라멘트 개수에 묶인 특수 키 (샘플 1개 → n개)
    out['filament_settings_id']=[pla_profile]*n_fil
    out['filament_ids']=[filament_id]*n_fil
    out['filament_colour']=list(colours[:n_fil]); out['filament_multi_colour']=list(colours[:n_fil])
    for k in ['filament_colour_type','filament_is_mixed','filament_nozzle_map','filament_volume_map','filament_mixed_gradient','filament_mixed_gradient_per_part']: out[k]=[S[k][0]]*n_fil
    for k in ['filament_mixed_components','filament_mixed_gradient_curve','filament_mixed_gradient_range','filament_mixed_sublayer_ratios','default_filament_colour']: out[k]=[S[k][0]]*n_fil
    out['filament_map']=['1']*n_fil
    out['filament_self_index']=[str(i+1) for i in range(n_fil) for _ in range(nvar)]
    out['filament_extruder_variant']=S['filament_extruder_variant'][:nvar]*n_fil
    out['flush_volumes_matrix']=['0' if i==j else '140' for i in range(n_fil) for j in range(n_fil)]
    out['flush_volumes_vector']=['140']*(2*n_fil)
    # filament_dev_* 는 Bambu 가 필라멘트 수에 맞춰 늘리지 않는 키(Preset.cpp filament_dev_options) → 샘플 값 그대로
    for k in S:
        if k.startswith('filament_dev_'): out[k]=S[k]
    for k,v in (overrides or {}).items(): out[k]=v
    assert set(out)==set(S), (set(out)^set(S))
    json.dump(out,open(out_path,'w',encoding='utf-8'),indent=4,ensure_ascii=False)
    return out,S
def check(out,S,n_fil,n_plates):
    """샘플 대비 배열 길이 규칙 검사: 필라멘트별 1→n, 변형별 2→2n, 플레이트별(wipe_tower_x/y) 2→n_plates, 나머지 동일."""
    nvar=len(S['filament_extruder_variant']); bad=[]
    for k,v in S.items():
        o=out[k]
        if type(o)!=type(v): bad.append((k,'type')); continue
        if not isinstance(v,list): continue
        if k in ('wipe_tower_x','wipe_tower_y'): exp=n_plates
        elif k=='flush_volumes_matrix': exp=n_fil*n_fil
        elif k=='flush_volumes_vector': exp=2*n_fil
        elif k.startswith('filament_dev_'): exp=len(v)
        elif k in VARIANT or k=='filament_self_index': exp=nvar*n_fil
        elif k in FIL_OPTS or len(v)==1 and k.startswith('filament_') or k in ('default_filament_colour','filament_map','filament_ids','filament_settings_id','filament_colour','filament_multi_colour','filament_colour_type','filament_is_mixed','filament_nozzle_map','filament_volume_map','filament_mixed_components','filament_mixed_gradient','filament_mixed_gradient_curve','filament_mixed_gradient_per_part','filament_mixed_gradient_range','filament_mixed_sublayer_ratios'):
            exp=n_fil if len(v)==1 else len(v)
        else: exp=len(v)
        if len(o)!=exp: bad.append((k,len(v),len(o),exp))
        if any(not isinstance(x,str) for x in o): bad.append((k,'non-str'))
    return bad
if __name__=='__main__':
    # 사용: python build_project_settings.py <sample.3mf 또는 project_settings.json> <out.json>
    import zipfile
    src,outp=sys.argv[1],sys.argv[2]
    if src.endswith('.3mf'):
        open('_sample_ps.json','wb').write(zipfile.ZipFile(src).read('Metadata/project_settings.config')); src='_sample_ps.json'
    out,S=build(src,outp,2,['#30949D','#F2AF38'],overrides={'enable_support':'1','support_type':'normal(auto)','support_on_build_plate_only':'1','wipe_tower_x':['165']*2,'wipe_tower_y':['222.466']*2})
    print('FIL_OPTS',len(FIL_OPTS),'VARIANT',len(VARIANT))
    print('bad:',check(out,S,2,2))
    for k in ['filament_settings_id','filament_colour','filament_type','filament_ids','nozzle_temperature','textured_plate_temp','hot_plate_temp','filament_flow_ratio','filament_max_volumetric_speed','filament_self_index','filament_extruder_variant','flush_volumes_matrix','flush_volumes_vector','filament_map','filament_density','filament_vendor','fan_min_speed','filament_retraction_length','slow_down_min_speed','curr_bed_type','enable_support','support_type','brim_type','wall_loops','sparse_infill_density','layer_height','filament_start_gcode']:
        print(f'{k:30s}',str(out[k])[:110])
