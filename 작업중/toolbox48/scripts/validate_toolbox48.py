#!/usr/bin/env python3
"""Validate 48 upright reference nameplates, preserved joints, motion and 3MF."""
from pathlib import Path
import json
import sys
import numpy as np
import trimesh
import lib3mf
from trimesh.transformations import rotation_matrix as R, translation_matrix as T
ROOT=Path(__file__).resolve().parents[3]; PROJECT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'작업중/toolbox42/scripts')]
from load3mf import load_parts
from generic3mf import write_generic_3mf
from overhang import layer_poly
from shapely.geometry import box


def iv(a,b):
    m=a.intersection(b,engine='manifold')
    return abs(float(m.volume)) if m.is_volume else 0.0


def moved(m,M):
    out=m.copy();out.apply_transform(M);return out


def main():
    np.random.seed(48)
    models=PROJECT/'models';qc=PROJECT/'qc';qc.mkdir(exist_ok=True)
    p=load_parts(models/'Toolbox48_geometry.3mf')
    a=load_parts(models/'Toolbox48_A_base_handle_clip.3mf')
    b=load_parts(models/'Toolbox48_B_lid_logo.3mf')
    old=load_parts(ROOT/'작업중/toolbox42/models/Toolbox42_v5_A_base_handle_latch.3mf')
    for n in ['handle','latch']:
        assert np.array_equal(a[n].vertices,old[n].vertices)
        assert np.array_equal(a[n].faces,old[n].faces)
    report={'capacity':48,'orientation':'upright: 50 mm x, 7 mm y, 30 mm z',
            'clip':'unchanged; user confirmed normal physical operation',
            'handle':'unchanged','reference':'sample/일괄4개_상판.3mf'}
    # The U-shaped INSIDE profile is identical at witness sections in both rows.
    witness=[]
    for y0,y1 in [(140,140),(190,197)]:
        profiles=[]
        for mesh,y in [(old['base'],y0),(p['base'],y1)]:
            s=mesh.section(plane_origin=[0,y,0],plane_normal=[0,1,0])
            # Compare continuous section paths: booleans change triangulation.
            from shapely.geometry import LineString
            from shapely.ops import unary_union
            profile=unary_union([LineString(v[:,[0,2]]) for v in s.discrete])
            profiles.append(profile.intersection(box(24.01,2.58,186.99,14.51)))
        error=profiles[0].hausdorff_distance(profiles[1])
        assert error < .002,error
        witness.append({'old_y':y0,'new_y':y1,'max_profile_vertex_distance_mm':float(error)})
    report['U_profile_witness_sections']=witness
    # Measured hole axes: base (y=246.375,z=26.5), lid print (63.4,10.01).
    hinge=np.array([0,246.375,26.5])
    closed=T([-20.15,309.775,36.51])@R(np.pi,[1,0,0])
    lid_closed=moved(p['lid'],closed)
    report['hinge']={'closed_matrix':closed.tolist(),'sweep':[]}
    for deg in range(0,121,15):
        matrix=T(hinge)@R(-np.deg2rad(deg),[1,0,0])@T(-hinge)@closed
        volume=iv(p['base'],moved(p['lid'],matrix))
        assert volume < .01,(deg,volume)
        report['hinge']['sweep'].append({'angle_deg':deg,'intersection_mm3':volume})
    report['handle_sweep']=[]
    handle_axis=np.array([0,105.4375,18.25])
    def handle_matrix(deg):return T(handle_axis)@R(np.deg2rad(deg),[1,0,0])@T([46.45,-77.75,-4.5])
    for deg in range(-90,91,15):
        volume=iv(p['base'],moved(p['handle'],handle_matrix(deg)))
        assert volume < .01,(deg,volume)
        report['handle_sweep'].append({'angle_deg':deg,'intersection_mm3':volume})
    report['surface_distance_samples']={}
    for name,mesh in [('lid',lid_closed),('handle',moved(p['handle'],handle_matrix(0)))]:
        _,distances,_=trimesh.proximity.closest_point(p['base'],mesh.sample(3000))
        report['surface_distance_samples'][name]={
            'min_mm':float(distances.min()),'p1_mm':float(np.quantile(distances,.01)),
            'p5_mm':float(np.quantile(distances,.05))}
    report['beam_estimates']={}
    for name,L,width,height,load,factor in [
        ('handle_bar',76,12.7,9,20,48),('handle_leg',25,9,5.4,10,3),
        ('lid_panel',140,171,2.6,20,48)]:
        inertia=width*height**3/12
        moment=load*L/(4 if factor==48 else 1)
        report['beam_estimates'][name]={
            'deflection_mm':load*L**3/(factor*3300*inertia),
            'stress_MPa':moment*height/(2*inertia),'load_N':load,
            'span_mm':L,'b_mm':width,'h_mm':height}
    source=load_parts(ROOT/'sample/일괄4개_상판.3mf')['2_민 우_밑판']
    source.apply_translation(-source.bounds[0]);source.apply_transform(R(np.pi/2,[1,0,0]))
    tags={};positions=[]
    for row,ys in enumerate([121.775002,181.775002]):
        for col,xc in enumerate([53.1,105.5,157.9]):
            for slot in range(8):
                name=f'nameplate_{row+1}_{col+1}_{slot+1}'
                mesh=source.copy();mesh.apply_translation([xc-25,ys+.5+7*slot+7,2.6])
                assert np.allclose(mesh.extents,[50,7,30],atol=1e-5)
                tags[name]=mesh
                positions.append({'name':name,'bounds_mm':mesh.bounds.tolist()})
    assert len(tags)==48
    group=trimesh.util.concatenate(list(tags.values()))
    bv=iv(group,p['base']);lv=iv(group,lid_closed)
    assert bv<.01 and lv<.01,(bv,lv)
    # Neighbours are 7 mm apart; overlapping solids are forbidden (touch is fine).
    first=list(tags.values())
    pair_intersections=[iv(first[i],first[i+1]) for i in range(7)]
    assert max(pair_intersections)<.01
    report['storage']={'base_intersection_mm3':bv,'closed_lid_intersection_mm3':lv,
                       'adjacent_intersections_mm3':pair_intersections,'placements':positions,
                       'bottom_z_mm':2.6,'top_z_mm':32.6,'per_cradle_depth_mm':57,
                       'pitch_mm':7,'total_depth_clearance_mm':1}
    strict=[]
    for filename in ['Toolbox48_A_base_handle_clip.3mf','Toolbox48_B_lid_logo.3mf']:
        wrapper=lib3mf.get_wrapper();model=wrapper.CreateModel();reader=model.QueryReader('3mf')
        reader.SetStrictModeActive(True)
        # lib3mf file API uses ASCII paths, while the project lives in a Korean path.
        tmp=Path('/tmp')/filename;tmp.write_bytes((models/filename).read_bytes())
        reader.ReadFromFile(str(tmp));assert reader.GetWarningCount()==0
        parts=load_parts(models/filename)
        for n,m in parts.items():
            assert m.is_watertight and m.is_volume
            assert n=='logo' or len(m.split(only_watertight=False))==1
            assert len(m.faces)<=200000
            assert np.all(m.bounds[0]>=-1e-5) and np.all(m.bounds[1]<=[256,256,250])
        assert sum(len(m.faces) for m in parts.values())<=500000
        strict.append({'file':filename,'warning_count':reader.GetWarningCount(),
                       'total_faces':sum(len(m.faces) for m in parts.values())})
    report['strict_3mf']=strict
    # Combined multicolour outline, including logo, must have no early exterior growth.
    from shapely.ops import unary_union
    contours=[unary_union([layer_poly(b['lid'],z),layer_poly(b['logo'],z)]) for z in [.3137,.5137,.7137,.9137]]
    exterior=[max(getattr(q,'geoms',[q]),key=lambda g:g.area).exterior for q in contours]
    from shapely.geometry import Polygon
    first_outline=Polygon(exterior[0])
    delta=[first_outline.symmetric_difference(Polygon(e)).area for e in exterior]
    assert max(delta)<.1,delta
    report['multicolour_first_five_layers_exterior_difference_mm2']=delta
    # Model-view meshes are proof of fit; these are not print plates.
    colors=['#37474f','#ffb300']
    upright={'base':p['base'],**tags}
    write_generic_3mf(qc/'upright48.3mf',[{'name':n,'parts':[(m,colors[0] if n=='base' else '#d7ddd7',n)]} for n,m in upright.items()], '48 upright nameplates — fit visualization')
    assembly={**p,**tags}
    write_generic_3mf(qc/'assembly48.3mf',[{'name':n,'parts':[(m,colors[int(n=='logo')] if n in p else '#d7ddd7',n)]} for n,m in assembly.items()], 'Toolbox48 assembly visualization')
    states={}
    for label,degree in [('닫힘',0),('열림',90)]:
        matrix=T(hinge)@R(-np.deg2rad(degree),[1,0,0])@T(-hinge)@closed
        states[label]={'lid':matrix.ravel().tolist(),'logo':matrix.ravel().tolist(),'handle':handle_matrix(0).ravel().tolist()}
    states['분리']={'lid':(T([0,0,55])@closed).ravel().tolist(),'logo':(T([0,0,55])@closed).ravel().tolist(),**{n:[0,0,40] for n in tags}}
    (qc/'states.json').write_text(json.dumps(states,ensure_ascii=False,indent=2)+'\n')
    (qc/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['storage','hinge','handle_sweep']},ensure_ascii=False,indent=2))
    print('PASS: 48 upright nameplates, U profiles, base/lid clearance, 9 hinge + 13 handle angles, unchanged clip/handle, strict 3MF')

if __name__=='__main__':main()
