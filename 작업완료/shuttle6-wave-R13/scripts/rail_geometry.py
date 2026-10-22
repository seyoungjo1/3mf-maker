"""One lower flat guide; the upper shell has a printable lead-in after its socket.

The R12 external surfaces, shoulder, and adhesive alignment key are preserved.
The flat fills the original circular bore instead of thinning the outer wall.
"""
import numpy as np
from shapely.geometry import Point, box as rect
from build import P, extr, union, diff, box, sphere


def guide_fill(z0, z1, flat_y, radius=None):
    radius = P['ID']/2 + .12 if radius is None else radius
    section = Point(0, 0).buffer(radius, quad_segs=48).intersection(
        rect(-radius-1, -radius-1, radius+1, flat_y))
    return extr(section, z1-z0, z0)


def upper_guide_ramp(start_z, flat_y):
    """A vertical-extrusion wedge grows inward <=0.1mm per 0.2mm layer."""
    radius = P['ID']/2 + .12
    y0 = -P['ID']/2
    length = (flat_y-y0)/.5
    # A filled longitudinal wedge intersected with the circular bore envelope.
    from shapely.geometry import Polygon
    profile = Polygon([(-radius-1, start_z), (y0, start_z),
                       (flat_y, start_z+length), (flat_y, P['BODY_L']),
                       (-radius-1, P['BODY_L'])])
    wedge = extr(profile, 2*radius+2)
    wedge.apply_transform(np.array([[0,0,1,-radius-1],
                                    [1,0,0,0], [0,1,0,0], [0,0,0,1.]], float))
    from build import cyl
    import trimesh as tm
    return tm.boolean.intersection([wedge, cyl(radius, P['BODY_L']-start_z, start_z)], engine='manifold')


def detent_cutters(stations):
    return [sphere(P['DETENT_POCKET_R'], [s*P['DETENT_X'], P['DETENT_Y'], z])
            for z in stations for s in [-1, 1]]


def finish_shell_pair(lower, upper):
    z = P['BODY_SPLIT_Z']
    flat_y = P['FLAT_OUTER_Y'] - P['RADIAL_GAP']
    stations = [P['CLOSED_L']-(P['DETENT_Z']+i*P['DETENT_PITCH'])
                for i in range(P['DETENT_COUNT'])]
    lower = union(lower, guide_fill(P['FLOOR'], z+P['GLUE_L'], flat_y))
    lower = diff(lower, *detent_cutters(stations))
    upper.apply_translation([0, 0, z])
    # Preserve the female glue socket. The guide resumes with a gentle ramp.
    upper = union(upper, upper_guide_ramp(z+P['GLUE_L']+3.5, flat_y))
    upper = diff(upper, *detent_cutters(stations))
    upper.apply_translation([0, 0, -z])
    return lower, upper


def finish_shell_coupon(coupon):
    flat_y = P['FLAT_OUTER_Y'] - P['RADIAL_GAP']
    return union(coupon, guide_fill(0, 36, flat_y))
