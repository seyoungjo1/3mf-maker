#!/usr/bin/env python3
"""Extend the measured six curved cradles to eight 7 mm nameplates each.

Insert straight sections rather than scale: nameplate cradle radii, holes,
hinges, handle, clip and logo stay the same size. All inputs are repository 3MF.
"""
from pathlib import Path
import json
import sys
import numpy as np
import trimesh
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[3]
PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / '작업중/toolbox42/scripts')]
from load3mf import load_parts
from overhang import layer_poly
from efc import pre_expand_first_layer, pre_expand_first_layer_group
from generic3mf import write_generic_3mf


def volume(mesh):
    return abs(float(mesh.volume)) if mesh.is_volume else 0.0


def extrude(polygons, height):
    geometries = polygons if isinstance(polygons, (list, tuple)) else list(getattr(polygons, 'geoms', [polygons]))
    meshes = [trimesh.creation.extrude_polygon(p, height, engine='earcut')
              for p in geometries if isinstance(p, Polygon) and p.area > 1e-7]
    return trimesh.util.concatenate(meshes)


def insert_y(mesh, y, length):
    """Cut at a straight section, translate one half, and fill the exact section."""
    lo, hi = mesh.bounds
    def slab(y0, y1):
        bounds = np.array([[lo[0]-1, y0, lo[2]-1], [hi[0]+1, y1, hi[2]+1]])
        m = trimesh.creation.box(bounds=bounds)
        return mesh.intersection(m, engine='manifold')
    lower = slab(lo[1]-1, y)
    upper = slab(y, hi[1]+1)
    section = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    planar, transform = section.to_2D(normal=[0, 1, 0])
    assert np.allclose(transform[:3, 2], [0, 1, 0])
    bridge = extrude(planar.polygons_full, length)
    bridge.apply_transform(transform)
    upper.apply_translation([0, length, 0])
    result = trimesh.boolean.union([lower, bridge, upper], engine='manifold')
    assert result.is_volume
    expected = volume(mesh) + sum(p.area for p in planar.polygons_full) * length
    assert abs(volume(result)-expected) < 0.1, (volume(result), expected)
    return result


def outer(poly):
    return Polygon(max(getattr(poly, 'geoms', [poly]), key=lambda p:p.area).exterior)


def remove_boolean_dust(mesh):
    components = mesh.split(only_watertight=False)
    meaningful = [m for m in components if abs(m.volume) > 1e-4]
    discarded = sum(abs(m.volume) for m in components if abs(m.volume) <= 1e-4)
    assert discarded < 1e-3 and len(meaningful) == 1, [float(m.volume) for m in meaningful]
    return meaningful[0]


def build():
    A = load_parts(ROOT / '작업중/toolbox42/models/Toolbox42_v5_A_base_handle_latch.3mf')
    B = load_parts(ROOT / '작업중/toolbox42/models/Toolbox42_v6_B_lid_logo.3mf')
    base = A['base'].copy()
    # Each existing 50 mm deep cradle gains 7 mm. No radius or joint scaling.
    base = insert_y(base, 158.0, 7.0)
    base = insert_y(base, 218.0, 7.0)  # original y=211, after first insertion
    physical_base = base.copy()
    # Reinforce only the EXTERNAL bottom perimeter; keep curved internal seats.
    core = box(20, 117.775002, 191, 242.775002)
    footprint = outer(layer_poly(base, 7.8137).intersection(core))
    perimeter = footprint.difference(footprint.buffer(-3.8, join_style='mitre'))
    skirt = extrude(perimeter, 7.8)
    base = base.union(skirt, engine='manifold')
    physical_base = base.copy()
    base = pre_expand_first_layer(base)

    lid = insert_y(B['lid'], 95.0, 7.0)
    lid = insert_y(lid, 162.0, 7.0)  # original y=155
    logo = B['logo'].copy(); logo.apply_translation([0, 7, -logo.bounds[0,2]])
    # First six layers of multicolour exterior are vertical. Pocket unchanged.
    # Include the small tab/root contours as well as the main panel perimeter.
    edge = unary_union([outer(layer_poly(lid,z)) for z in
                        [.3137,.5137,.7137,.9137,1.1137]])
    rim = edge.difference(edge.buffer(-4.0, join_style='mitre'))
    lid = lid.union(extrude(rim, 1.2), engine='manifold')
    # The old pocket had a 0.3 mm air gap around an inlay that is printed in place.
    # Fill that gap with the lid colour, preserving the exact logo geometry.
    face = extrude(edge, float(logo.bounds[1,2]))
    face = face.difference(logo, engine='manifold')
    lid = remove_boolean_dust(lid.union(face, engine='manifold'))
    physical_lid, physical_logo = lid.copy(), logo.copy()
    # Compensate the target silhouette, not the already-expanded v6 silhouette.
    # This preserves 0.15 mm compensation without accidentally doubling it.
    first = extrude(edge.buffer(.15,join_style='mitre'),.2)
    first = first.difference(logo,engine='manifold')
    lid = remove_boolean_dust(lid.union(first,engine='manifold'))
    assert volume(lid.intersection(logo, engine='manifold')) < 0.01

    # Copy the working clip/handle vertex and face arrays without remodeling.
    parts = {'base':base, 'handle':A['handle'], 'latch':A['latch'], 'lid':lid, 'logo':logo}
    models = PROJECT / 'models'; models.mkdir(exist_ok=True)
    colors = ['#37474f', '#ffb300']
    write_generic_3mf(models/'Toolbox48_A_base_handle_clip.3mf',
        [{'name':n, 'parts':[(parts[n], colors[0], n)]} for n in ['base','handle','latch']],
        'Toolbox48 A — 6 cradles x 8 nameplates', material_order=colors)
    write_generic_3mf(models/'Toolbox48_B_lid_logo.3mf',
        [{'name':'lid+logo', 'parts':[(lid,colors[0],'lid'),(logo,colors[1],'logo')]}],
        'Toolbox48 B — lid and logo', material_order=colors)
    # STL files retain shared plate coordinates so lid/colour registration is exact.
    for n,m in parts.items():m.export(models/f'Toolbox48_{n}.stl')
    # Non-EFC geometric assembly export, separate from print preparation.
    write_generic_3mf(models/'Toolbox48_geometry.3mf',
        [{'name':n,'parts':[(m,colors[int(n=='logo')],n)]} for n,m in
         {'base':physical_base,'lid':physical_lid,'logo':physical_logo,
          'handle':A['handle'],'latch':A['latch']}.items()],
        'Toolbox48 geometry — assembly input, not a print plate', material_order=colors)
    parameters = {'rows':2,'columns':3,'per_cradle':8,'capacity':48,
                  'nameplate_mm':[50,30,7],'cradle_depth_before_mm':50,
                  'cradle_depth_after_mm':57,'stack_clearance_mm':1,
                  'added_length_mm':14,'efc_mm':0.15,
                  'clip_and_handle':'unchanged v5 mesh',
                  'base_y_insertions_mm':[[158,7],[218,7]],
                  'lid_y_insertions_mm':[[95,7],[162,7]],
                  'logo_translation_mm':[0,7,0]}
    (PROJECT/'docs/parameters.json').write_text(json.dumps(parameters,indent=2)+'\n')
    for n,m in parts.items():
        assert m.is_watertight and m.is_volume
        assert len(m.faces) <= 200000
        assert np.all(m.bounds[0] >= -1e-5) and np.all(m.bounds[1] <= [256,256,250])
        print(n, len(m.faces), np.round(m.extents,3).tolist(), round(volume(m),1))
    return parts


if __name__ == '__main__': build()
