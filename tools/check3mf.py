#!/usr/bin/env python3
"""lib3mf strict 모드로 3MF 를 읽어 경고 수를 센다. 사용: python tools/check3mf.py a.3mf [b.3mf ...]  (경로는 ASCII 권장)"""
import sys, lib3mf
def check(path):
    w = lib3mf.get_wrapper(); model = w.CreateModel(); r = model.QueryReader('3mf'); r.SetStrictModeActive(True)
    r.ReadFromFile(path); n = r.GetWarningCount()
    warns = [r.GetWarning(i)[1] if isinstance(r.GetWarning(i), tuple) else str(r.GetWarning(i)) for i in range(n)]
    objs = model.GetObjects(); cnt = 0
    while objs.MoveNext(): cnt += 1
    return n, warns, cnt
if __name__ == '__main__':
    bad = 0
    for p in sys.argv[1:]:
        n, warns, cnt = check(p); bad += n
        print(f'{p}: strict 경고 {n}, 오브젝트 {cnt}' + (' | ' + '; '.join(warns[:5]) if warns else ''))
    sys.exit(1 if bad else 0)
