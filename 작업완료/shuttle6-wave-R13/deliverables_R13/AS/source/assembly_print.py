"""Print-project overview; full21+ state review remains in qc/review_R13."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from assembly import define as full_define

def define(parts):
 result=full_define(parts)
 keys=['닫힘','열림','분리','인출 36mm','인출 72mm','인출 108mm','인출 144mm','인출 180mm','몸통 접착','뚜껑 끼움 전','뚜껑 딸깍 통과','뚜껑 끼움 완료','딸깍 통과 18mm','딸깍 시험편 닫힘','딸깍 시험편 통과']
 result['states']={k:result['states'][k] for k in keys}
 result['notes'].append('Full extraction, dimensional gauge and coupon states were verified against the identical meshes in the preceding review_R13. Print-project overview retains seven assembly/cap states; scalar dimensional/interference/rotation/spring checks still run in full_define.')
 return result
