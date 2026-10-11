# freecad-run 예시: 필렛 상자 + 관통 구멍 + 바닥 챔퍼(코끼리발) → STEP·STL·info.json
# 러너에서 `freecadcmd tools/freecad/example_fillet_box.py` 로 돈다. 출력 폴더 = 환경변수 FC_OUT.
import json, os
import FreeCAD as App, Part, Mesh, MeshPart

OUT = os.environ.get('FC_OUT', '.')
W, D, H, R, HOLE, CH = 40.0, 30.0, 15.0, 4.0, 6.3, 0.4      # mm: 폭·깊이·높이·세로 모서리 필렛·관통 구멍 Ø·바닥 챔퍼

body = Part.makeBox(W, D, H)
body = body.makeFillet(R, [e for e in body.Edges if abs(e.Vertexes[0].Z - e.Vertexes[1].Z) > H - 1e-6])   # 세로 모서리 4개
body = body.cut(Part.makeCylinder(HOLE / 2, H + 2, App.Vector(W / 2, D / 2, -1)))
bottom = [e for e in body.Edges if all(abs(v.Z) < 1e-6 for v in e.Vertexes)
          and (e.CenterOfMass - App.Vector(W / 2, D / 2, 0)).Length > HOLE]          # 바깥 바닥 윤곽(구멍 테두리 제외)
body = body.makeChamfer(CH, bottom)

doc = App.newDocument('example'); obj = doc.addObject('Part::Feature', 'fillet_box'); obj.Shape = body; doc.recompute()
Part.export([obj], os.path.join(OUT, 'fillet_box.step'))
mesh = MeshPart.meshFromShape(Shape=body, LinearDeflection=0.05, AngularDeflection=0.2618, Relative=False)
mesh.write(os.path.join(OUT, 'fillet_box.stl'))
bb = body.BoundBox
info = {'freecad': '.'.join(App.Version()[:3]), 'valid': body.isValid(), 'volume_mm3': round(body.Volume, 2),
        'bbox_mm': [round(bb.XLength, 3), round(bb.YLength, 3), round(bb.ZLength, 3)], 'faces': len(body.Faces),
        'mesh_triangles': mesh.CountFacets, 'mesh_solid': mesh.isSolid()}
json.dump(info, open(os.path.join(OUT, 'info.json'), 'w'), ensure_ascii=False, indent=1)
print('OK', info)
