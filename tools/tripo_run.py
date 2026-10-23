#!/usr/bin/env python3
"""Tripo3D API 로 모델 생성(이미지→3D, 글→3D) — Actions `tripo-run` 이 돌린다.

요청 파일 = `<프로젝트>/tripo/<이름>.json`:
  {"type": "image_to_model", "image": "turtle.png",      # 요청 파일 기준 상대 경로
   "texture": false, "pbr": false, "face_limit": 120000,  # 선택
   "model_version": "...",                                 # 선택(없으면 Tripo 기본)
   "extra": {...}}                                         # 선택: task 본문에 그대로 합침
  또는 {"type": "text_to_model", "prompt": "..."}
결과 = `<프로젝트>/tripo_out/<이름>/`: status.json · task.json(응답 원문) · 받은 파일(glb 등) · log.txt
API 키는 환경변수 TRIPO_API_KEY (Actions 비밀). 생성 1회 = Tripo 크레딧 사용 — 요청 파일이 바뀐 push 에서만 돈다.

python tools/tripo_run.py <요청.json> [--dry]
"""
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

API = "https://api.tripo3d.ai/v2/openapi"


def _req(method, url, key, body=None, ctype=None, timeout=120):
    h = {"Authorization": f"Bearer {key}"}
    if ctype:
        h["Content-Type"] = ctype
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as f:
            return json.loads(f.read().decode())
    except urllib.error.HTTPError as e:
        txt = e.read().decode(errors="replace")
        try:
            return {"http": e.code, **json.loads(txt)}
        except ValueError:
            return {"http": e.code, "text": txt[:500]}


def upload(path: Path, key, log):
    """이미지 업로드 → 파일 토큰. 엔드포인트 이름이 버전마다 달라 둘 다 시도한다."""
    data = path.read_bytes()
    bnd = uuid.uuid4().hex
    mt = mimetypes.guess_type(path.name)[0] or "image/png"
    body = (f"--{bnd}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
            f"Content-Type: {mt}\r\n\r\n").encode() + data + f"\r\n--{bnd}--\r\n".encode()
    for ep in ("/upload/sts", "/upload"):
        res = _req("POST", API + ep, key, body, f"multipart/form-data; boundary={bnd}")
        log(f"upload {ep}: {json.dumps(res, ensure_ascii=False)[:300]}")
        d = res.get("data") or {}
        tok = d.get("file_token") or d.get("image_token")
        if res.get("code") == 0 and tok:
            return tok
    raise RuntimeError("업로드 실패")


def build_task(spec: dict, base: Path, key, log):
    t = spec.get("type", "image_to_model")
    task = {"type": t}
    if t == "image_to_model":
        img = base / spec["image"]
        ext = img.suffix.lower().lstrip(".").replace("jpeg", "jpg")
        task["file"] = {"type": ext, "file_token": upload(img, key, log)}
    elif t == "text_to_model":
        task["prompt"] = spec["prompt"]
        if spec.get("negative_prompt"):
            task["negative_prompt"] = spec["negative_prompt"]
    else:
        raise ValueError(f"모르는 type: {t}")
    for k in ("texture", "pbr", "face_limit", "model_version", "auto_size", "orientation", "quad"):
        if k in spec:
            task[k] = spec[k]
    task.update(spec.get("extra") or {})
    return task


def _urls(obj, pre=""):
    """응답 output 안의 내려받을 주소(문자열 http…) 전부."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _urls(v, f"{pre}{k}.")
    elif isinstance(obj, str) and obj.startswith("http"):
        yield pre.rstrip("."), obj


def run(spec_path: str, dry=False):
    sp = Path(spec_path)
    spec = json.loads(sp.read_text(encoding="utf-8"))
    out = sp.parent.parent / "tripo_out" / sp.stem
    out.mkdir(parents=True, exist_ok=True)
    logf = open(out / "log.txt", "w", encoding="utf-8")

    def log(s):
        print(s)
        logf.write(s + "\n")
        logf.flush()

    status = {"spec": str(sp), "ok": False}
    try:
        key = os.environ.get("TRIPO_API_KEY", "").strip()
        if not key:
            raise RuntimeError("TRIPO_API_KEY 가 비어 있음(Actions 비밀 이름 확인)")
        log(f"키: {os.environ.get('TRIPO_KEY_NAME', 'TRIPO_API_KEY')} (길이 {len(key)}, 앞 {key[:4]}…)")
        if dry:
            res = _req("GET", API + "/user/balance", key)
            log(f"balance: {json.dumps(res, ensure_ascii=False)}")
            status.update(ok=res.get("code") == 0, balance=res.get("data"))
            return status
        task = build_task(spec, sp.parent, key, log)
        log("task: " + json.dumps({k: v for k, v in task.items() if k != "file"}, ensure_ascii=False))
        res = _req("POST", API + "/task", key, json.dumps(task).encode(), "application/json")
        log(f"create: {json.dumps(res, ensure_ascii=False)}")
        tid = (res.get("data") or {}).get("task_id")
        if not tid:
            raise RuntimeError("task 생성 실패")
        status["task_id"] = tid
        t0 = time.time()
        while True:
            time.sleep(5)
            st = _req("GET", f"{API}/task/{tid}", key)
            d = st.get("data") or {}
            log(f"{time.time() - t0:5.0f}s {d.get('status')} {d.get('progress')}")
            if d.get("status") in ("success", "failed", "banned", "expired", "cancelled", "unknown"):
                break
            if time.time() - t0 > 1500:
                raise RuntimeError("시간 초과(25분)")
        (out / "task.json").write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
        status["status"] = d.get("status")
        files = []
        for name, url in _urls(d.get("output") or {}):
            ext = Path(url.split("?")[0]).suffix or ".bin"
            fn = out / (name.replace(".", "_") + ext)
            urllib.request.urlretrieve(url, fn)
            files.append(fn.name)
            log(f"받음 {fn.name} {fn.stat().st_size} B")
        status["files"] = files
        status["ok"] = d.get("status") == "success" and bool(files)
    except Exception as e:  # noqa: BLE001 — 결과 폴더에 원인을 남긴다
        status["error"] = str(e)
        log(f"오류: {e}")
    finally:
        (out / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
        logf.close()
    return status


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    s = run(a[0], dry="--dry" in sys.argv)
    print(json.dumps(s, ensure_ascii=False))
    sys.exit(0 if s.get("ok") else 1)
