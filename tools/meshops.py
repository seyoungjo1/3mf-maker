"""메시 공용 연산. 불리언 계산 찌꺼기 제거 등.
drop_slivers(m, tol=1e-3): 부피 < tol 인 조각만 버리고 (메시, 버린 조각 수, 버린 부피 합) 을 돌려준다.
의미 있는 조각(≥ tol)은 절대 숨기지 않는다 — 그 판정은 QC 의 '조각 수' 가 한다."""
import trimesh
def drop_slivers(m, tol=1e-3):
    bs = m.split(only_watertight=False)
    if len(bs) <= 1: return m, 0, 0.0
    keep = [b for b in bs if abs(b.volume) >= tol]; gone = [b for b in bs if abs(b.volume) < tol]
    out = keep[0] if len(keep) == 1 else trimesh.util.concatenate(keep)
    return out, len(gone), float(sum(abs(b.volume) for b in gone))
