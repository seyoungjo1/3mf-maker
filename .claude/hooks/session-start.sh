#!/bin/bash
# Claude Code 클라우드 세션 시작 시 파이썬 의존 라이브러리 설치 (requirements.txt).
# 로컬에서는 아무것도 하지 않는다. 여러 번 실행해도 안전(이미 설치된 것은 건너뜀).
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# 이미 전부 설치돼 있으면 pip 호출을 생략해 시작을 빠르게 한다.
if python3 - << 'PY' 2>/dev/null
import trimesh, shapely, rtree, manifold3d, mapbox_earcut, lib3mf, matplotlib, scipy, networkx, fast_simplification, PIL, playwright
PY
then
  echo "3mf-maker: 파이썬 의존 라이브러리 이미 설치됨"
  exit 0
fi

# Chromium은 컨테이너에 기본 설치(/opt/pw-browsers/chromium) → playwright 브라우저 다운로드 금지
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
python3 -m pip install --quiet --disable-pip-version-check -r requirements.txt
echo "3mf-maker: 파이썬 의존 라이브러리 설치 완료"
