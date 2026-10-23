"""Tripo glb → z-up mm 메시 + 정리(가장 큰 조각, 바닥 평면 절단, 구멍 메움) + 실측 요약.

glb 는 glTF 규약(y-up, 단위 없음, 큰 변 = 1.0). x 축 +90° 회전으로 z-up 으로 바꾸고 scale 로 mm 를 맞춘다.
python 작업중/gukse-clicker/scripts/tripo_import.py <glb> --out <stl> [--long 53] [--cut 0.6]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import trimesh


def load_zup(glb: str) -> trimesh.Trimesh:
    s = trimesh.load(glb, force="scene")
    m = s.to_geometry() if hasattr(s, "to_geometry") else s.dump(concatenate=True)
    m = trimesh.Trimesh(m.vertices.copy(), m.faces.copy(), process=True)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    return m


def largest(m: trimesh.Trimesh) -> trimesh.Trimesh:
    parts = m.split(only_watertight=False)
    return max(parts, key=lambda p: len(p.faces)) if len(parts) > 1 else m


def cut_bottom(m: trimesh.Trimesh, dz: float) -> trimesh.Trimesh:
    """바닥에서 dz 위를 평면으로 잘라 뚜껑을 씌운다(너덜한 바닥 조각 제거, 평평한 안착면)."""
    z0 = m.bounds[0][2] + dz
    out = m.slice_plane([0, 0, z0], [0, 0, 1], cap=True)
    out.apply_translation([0, 0, -z0])
    return out


def summary(m: trimesh.Trimesh) -> dict:
    return {"faces": int(len(m.faces)), "watertight": bool(m.is_watertight),
            "extents": [round(float(v), 2) for v in m.extents],
            "volume": round(float(m.volume), 1) if m.is_watertight else None,
            "bodies": len(m.split(only_watertight=False))}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("glb")
    ap.add_argument("--out", required=True)
    ap.add_argument("--long", type=float, default=0, help="가장 긴 수평 변을 이 mm 로")
    ap.add_argument("--cut", type=float, default=0.0, help="바닥에서 이만큼(mm, 스케일 후) 잘라냄")
    a = ap.parse_args(argv)
    m = load_zup(a.glb)
    raw = summary(m)
    if a.long:
        m.apply_scale(a.long / max(m.extents[0], m.extents[1]))
    m = largest(m)
    m.apply_translation(-np.array([*(m.bounds[0][:2] + m.bounds[1][:2]) / 2, m.bounds[0][2]]))
    if a.cut:
        m = largest(cut_bottom(m, a.cut))
    trimesh.repair.fill_holes(m)
    trimesh.repair.fix_normals(m)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    m.export(a.out)
    print(json.dumps({"raw": raw, "out": summary(m), "file": a.out}, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
