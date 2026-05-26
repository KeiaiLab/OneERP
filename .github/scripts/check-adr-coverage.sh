#!/usr/bin/env bash
# check-adr-coverage.sh — PR이 'needs-adr' 라벨을 가졌으면 ADR 신규 파일 존재 검사.
# 사용 (CI): PR_NUMBER, BASE_REF, GH_TOKEN env 필요.
# 종료 코드: 0=통과, 1=차단.

set -euo pipefail

LABEL="needs-adr"
PR_NUMBER="${PR_NUMBER:-}"
BASE_REF="${BASE_REF:-main}"

if [ -z "$PR_NUMBER" ]; then
  echo "::notice::PR_NUMBER 미설정 — local 실행으로 간주, skip"
  exit 0
fi

# hotfix 브랜치 또는 [skip-adr] 트레일러 예외
HEAD_REF=$(gh pr view "$PR_NUMBER" --json headRefName -q .headRefName 2>/dev/null || echo "")
PR_BODY=$(gh pr view "$PR_NUMBER" --json body -q .body 2>/dev/null || echo "")
PR_TITLE=$(gh pr view "$PR_NUMBER" --json title -q .title 2>/dev/null || echo "")
case "$HEAD_REF" in
  hotfix/*)
    echo "::notice::hotfix/* 브랜치 — ADR 게이트 예외"
    exit 0
    ;;
esac
if echo "$PR_TITLE $PR_BODY" | grep -qE '\[skip-adr\]'; then
  echo "::notice::[skip-adr] 트레일러 — ADR 게이트 예외"
  exit 0
fi

# 라벨 검사
HAS_LABEL=$(gh pr view "$PR_NUMBER" --json labels -q ".labels[].name" 2>/dev/null | grep -c "^$LABEL$" || true)
if [ "$HAS_LABEL" = "0" ]; then
  echo "::notice::needs-adr 라벨 없음 — skip"
  exit 0
fi

# 신규 ADR 파일 검사
NEW_ADR=$(git diff --name-only --diff-filter=A "origin/$BASE_REF...HEAD" -- 'docs/kb/adr/*.md' 2>/dev/null | wc -l | xargs)
if [ "$NEW_ADR" -lt 1 ]; then
  echo "::error::PR labeled '$LABEL' but no new ADR file under docs/kb/adr/"
  echo "ADR 작성: cp ai-dev/templates/adr-template.md docs/kb/adr/NNNN-<slug>.md"
  exit 1
fi

# INDEX.md 갱신 검사
if ! git diff --name-only "origin/$BASE_REF...HEAD" -- 'docs/kb/adr/INDEX.md' 2>/dev/null | grep -q .; then
  echo "::warning::INDEX.md 미갱신 — 신규 ADR 등록 필요"
fi

echo "::notice::ADR 커버리지 OK ($NEW_ADR new file(s))"
exit 0
