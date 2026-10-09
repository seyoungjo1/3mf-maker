#!/usr/bin/env python3
"""Recover ignored pipeline inputs from tracked 3MFs; leave print files unchanged.

Recover the raw v7 assembly frame from the plate placements, and nominal mating
parts from v5 3MF XML. No STL round trip or vertex merging is used.
"""
import pickle
import sys
from pathlib import Path

import numpy as np
import trimesh

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(PROJECT / 'scripts')]
from load3mf import load_parts
from build_v7 import stretch_y, shave_lip, fix_bottom, CUT_FRONT, CUT_REAR, D_FRONT, D_REAR


def prepare():
    parts = load_parts(PROJECT / 'models/Toolbox48_v7_A_base_handle_latch.3mf')
    parts.update(load_parts(PROJECT / 'models/Toolbox48_v7_B_lid_logo.3mf'))
    # Plate placements measured against the raw v7 assembly frame.
    shifts = {'base': [22.5, 42.0125, 0], 'handle': [40.78, -378.35234, 0],
              'latch': [55.9, -376.91469, 0],
              'lid': [309.7, 15.025, 0], 'logo': [309.7, 15.025, 0]}
    for name, mesh in parts.items():
        mesh.apply_translation(shifts[name])
    nominal = {name: mesh.copy() for name, mesh in parts.items()}
    original = load_parts(ROOT / '작업중/toolbox42/models/Toolbox42_v5_A_base_handle_latch.3mf')
    base = original['base'].copy()
    base.apply_translation([22.5, -39.9875, 0])
    base = stretch_y(base, [(CUT_FRONT, D_FRONT), (CUT_REAR, D_REAR)])
    base, _ = shave_lip(base)
    base = fix_bottom(base)
    base.apply_translation([0, 0, -base.bounds[0, 2]])
    nominal['base'] = base
    for name, shift in [('handle', [40.925, -240.325, 0]), ('latch', [47.9, -239.91469, 0])]:
        nominal[name] = original[name].copy()
        nominal[name].apply_translation(shift)
    # Only the additive first-layer EFC skirt may differ. Float32 Boolean
    # recovery tolerance is 0.05 mm³ and 0.00005 mm in bounding coordinates.
    box = trimesh.creation.box(extents=[2000, 2000, 2000])
    box.apply_translation([0, 0, 1000.201])
    for name in ('base', 'handle', 'latch'):
        a = trimesh.boolean.intersection([parts[name], box], engine='manifold')
        b = trimesh.boolean.intersection([nominal[name], box], engine='manifold')
        common = trimesh.boolean.intersection([a, b], engine='manifold')
        delta = abs(a.volume + b.volume - 2 * common.volume)
        assert delta < 0.05, (name, 'nominal recovery changed geometry', delta)
        assert np.allclose(a.bounds, b.bounds, atol=0.00005, rtol=0), name
        print(f'{name}: above-EFC symmetric difference {delta:.6f} mm³')
    for filename, data in [('v7parts.pkl', parts), ('v7parts_nominal.pkl', nominal)]:
        with open(PROJECT / filename, 'wb') as stream:
            pickle.dump(data, stream)


if __name__ == '__main__':
    prepare()
