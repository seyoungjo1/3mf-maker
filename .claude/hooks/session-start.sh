#!/bin/bash
# 3mf-maker 세션 시작 훅 — 모든 세션(클라우드·로컬)에서 실행된다. 출력(stdout)은 그대로 Claude 의 컨텍스트에 들어간다.
# 1) main 최신 내용 받기(작업 트리가 깨끗할 때만 병합)  2) 클라우드면 파이썬 의존 설치
# 3) 렌더러(Chromium) 확인  4) 스킬(SKILL.md + 핵심 references) 전문 출력 → 세션이 반드시 스킬을 읽고 시작
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0

echo "================ 3mf-maker 세션 시작 점검 ================"
# 1) main 동기화
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git fetch -q origin main 2>/dev/null && {
    behind=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
    if [ "$behind" != "0" ]; then
      if [ -z "$(git status --porcelain 2>/dev/null)" ]; then
        git merge -q --no-edit origin/main 2>/dev/null && echo "main 동기화: origin/main 커밋 ${behind}개 병합함" || { git merge --abort 2>/dev/null; echo "⚠ main 병합 충돌 — 작업 전에 직접 'git merge origin/main' 으로 해결할 것"; }
      else
        echo "⚠ 현재 브랜치가 main 보다 ${behind}커밋 뒤처짐(작업 트리 변경 있어 자동 병합 안 함) — 작업 전에 'git merge origin/main' 할 것"
      fi
    else
      echo "main 동기화: 최신"
    fi
  } || echo "⚠ origin/main 을 받지 못함(네트워크) — 로컬 내용 기준으로 진행"
fi

# 2) 클라우드: 파이썬 의존 설치
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  if ! python3 -c "import trimesh, shapely, rtree, manifold3d, mapbox_earcut, lib3mf, matplotlib, scipy, networkx, fast_simplification, PIL, playwright" 2>/dev/null; then
    export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
    python3 -m pip install --quiet --disable-pip-version-check -r requirements.txt >/dev/null 2>&1 && echo "파이썬 의존 설치 완료" || echo "⚠ 파이썬 의존 설치 실패 — 'pip install -r requirements.txt' 확인"
  else
    echo "파이썬 의존: 설치됨"
  fi
fi

# 3) 렌더러 점검
python3 tools/render_preview.py --check 2>/dev/null || echo "⚠ 렌더러 점검 실패 — tools/render_preview.py --check 로 원인 확인. 렌더 없이 보고하지 말 것"

# 3-1) 표준 프로그램 명령 목록(모든 작업은 이것으로)
echo
echo "================ 표준 프로그램: python tools/mm.py <명령> (새 도면: mm.py new <이름> → mm.py make 작업중/<이름>/pipeline.json) ================"
python3 tools/mm.py help 2>/dev/null | sed -n '/^  [a-z]/p' || echo "⚠ tools/mm.py help 실패"
echo "보고 첫머리 체크리스트 = mm make 결과의 checklist.line 그대로. API: python tools/mm_agent.py \"요청\" --project <이름>"

# 4) 스킬 전문
echo
echo "================ 반드시 따를 지침: .claude/skills/3d-print-3mf (main 기준) ================"
echo "모든 모델링·QC·렌더·3MF 작업은 아래 SKILL.md 순서를 따른다. 장식·반복 부재 모델은 references/studies/detail-design-method.md 절차, 결과는 tools/render_preview.py 로 렌더해 보여준다."
for f in .claude/skills/3d-print-3mf/SKILL.md \
         .claude/skills/3d-print-3mf/references/design_rules.md \
         .claude/skills/3d-print-3mf/references/presentation.md \
         .claude/skills/3d-print-3mf/references/bambu_3mf.md; do
  [ -f "$f" ] && { echo; echo "----- $f -----"; cat "$f"; }
done
echo
echo "(나머지 참고: .claude/skills/3d-print-3mf/references/studies/README.md 색인 — 작업 주제에 맞는 스터디 문서를 Read 할 것)"
exit 0
