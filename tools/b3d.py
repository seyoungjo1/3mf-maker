#!/usr/bin/env python3
"""build123d(OpenCascade B-rep, FreeCAD 와 같은 커널) 형상 → trimesh / STEP·STL.
3D 모서리 필렛·챔퍼·shell·글자처럼 메시 불리언으로 어려운 형상을 build123d 로 만들고, 여기서 메시로 바꿔 QC·EFC·렌더·3MF 로 넘긴다.
  from b3d import to_trimesh, save
  m = to_trimesh(part)            # 닫힌 메시(면 경계 정점 공유), 곡면 편차 tol mm
  save(part, 'out/fillet_box')    # out/fillet_box.step + .stl
예시: python tools/b3d.py --out <dir>  (필렛 상자 40×30×15, 필렛 R4, 구멍 Ø6.3, 바닥 챔퍼 0.4)"""
import os, argparse, numpy as np, trimesh

def to_trimesh(shape, tol=0.02, ang=0.2):
    """B-rep → trimesh. tol: 곡면 편차(mm, 지침 0.05 이하), ang: 각도 허용(rad). BRepMesh 는 면 경계 노드를 같은 좌표로 내므로 같은 좌표만 합친다."""
    verts, tris = shape.tessellate(tol, ang)
    m = trimesh.Trimesh(np.array([(v.X, v.Y, v.Z) for v in verts], float), np.array(tris, np.int64), process=True)
    m.merge_vertices(digits_vertex=6); m.update_faces(m.nondegenerate_faces()); m.remove_unreferenced_vertices(); m.fix_normals()
    return m

def save(shape, stem, tol=0.02, ang=0.2):
    from build123d import export_step
    os.makedirs(os.path.dirname(os.path.abspath(stem)), exist_ok=True)
    export_step(shape, stem + '.step'); m = to_trimesh(shape, tol, ang); m.export(stem + '.stl')
    return m

def example_fillet_box(W=40.0, D=30.0, H=15.0, R=4.0, HOLE=6.3, CH=0.4):
    """freecad-run 예시(tools/freecad/example_fillet_box.py)와 같은 형상: 세로 모서리 필렛 + 관통 구멍 + 바닥 바깥 윤곽 챔퍼(코끼리발)."""
    from build123d import Box, Cylinder, Pos, Align, Axis, Vector, fillet, chamfer
    b = Box(W, D, H, align=Align.MIN)
    b = fillet(b.edges().filter_by(Axis.Z), R)
    b -= Pos(W / 2, D / 2, H / 2) * Cylinder(HOLE / 2, H + 2)
    outer = [e for e in b.edges().group_by(Axis.Z)[0] if (e.center() - Vector(W / 2, D / 2, 0)).length > HOLE]
    return chamfer(outer, CH)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default='b3d_out'); a = ap.parse_args()
    part = example_fillet_box(); m = save(part, os.path.join(a.out, 'fillet_box'))
    print({'brep_valid': part.is_valid, 'brep_volume': round(part.volume, 2), 'mesh_volume': round(m.volume, 2), 'watertight': m.is_watertight,
           'bodies': len(m.split(only_watertight=False)), 'triangles': len(m.faces), 'size': np.round(m.extents, 3).tolist()})
