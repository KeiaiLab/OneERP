#!/usr/bin/env bash
# OneERP git worktree 감사·정리 도구
# - 머지된 worktree + 로컬 브랜치를 안전하게 일괄 정리
# - Ralph Loop 운영 worktree(feat/ralph-harness) 같은 미머지 대상은 절대 건드리지 않음
#
# 사용법:
#   ./scripts/dev/audit-worktrees.sh                 # 감사만 (분류 결과 출력)
#   ./scripts/dev/audit-worktrees.sh --remove-merged # main에 머지된 worktree + 로컬 브랜치 삭제
#   ./scripts/dev/audit-worktrees.sh --prune         # git worktree prune 으로 stale 레퍼런스 정리
#   ./scripts/dev/audit-worktrees.sh --all           # remove-merged + prune 연속 실행

set -euo pipefail

MAIN_BRANCH="${MAIN_BRANCH:-main}"

MODE="audit"
case "${1:-}" in
  --remove-merged) MODE="remove" ;;
  --prune)         MODE="prune"  ;;
  --all)           MODE="all"    ;;
  -h|--help)       grep '^#' "$0" | sed 's/^# \?//' ; exit 0 ;;
  "")              MODE="audit"  ;;
  *) echo "알 수 없는 옵션: $1" >&2 ; exit 1 ;;
esac

merged_branches=$(git branch --merged "$MAIN_BRANCH" -a \
  | sed 's/^[+ *]*//' \
  | grep -v "^$MAIN_BRANCH$" \
  | grep -v "HEAD" \
  | grep -v "^$" || true)

declare -a wt_paths wt_branches
current_path=""
while IFS= read -r line; do
  if [[ "$line" == worktree\ * ]]; then
    current_path="${line#worktree }"
  elif [[ "$line" == branch\ refs/heads/* ]]; then
    current_branch="${line#branch refs/heads/}"
    wt_paths+=("$current_path")
    wt_branches+=("$current_branch")
  fi
done < <(git worktree list --porcelain)

safe_idx=()
risky_idx=()
for i in "${!wt_branches[@]}"; do
  branch="${wt_branches[$i]}"
  if [ "$branch" = "$MAIN_BRANCH" ]; then continue; fi
  if echo "$merged_branches" | grep -q -Fx "$branch"; then
    safe_idx+=("$i")
  else
    risky_idx+=("$i")
  fi
done

total=${#wt_branches[@]}
echo "=== worktree 감사 결과 (기준 브랜치: $MAIN_BRANCH) ==="
echo "  전체 등록 worktree: ${total}개"
echo "  머지됨(안전 정리 대상): ${#safe_idx[@]}개"
echo "  미머지(절대 건드리지 않음): ${#risky_idx[@]}개"

if [ "${#risky_idx[@]}" -gt 0 ]; then
  echo ""
  echo "[미머지 목록 — 수동 검토 필요]"
  for i in "${risky_idx[@]}"; do
    path="${wt_paths[$i]}"
    branch="${wt_branches[$i]}"
    ahead=$(git rev-list --count "$MAIN_BRANCH..$branch" 2>/dev/null || echo "?")
    if [ -d "$path" ]; then
      dirty=$(git -C "$path" status --porcelain 2>/dev/null | awk 'NF>0' | wc -l | tr -d ' ')
    else
      dirty="GONE"
    fi
    echo "  - $branch  (ahead=$ahead, dirty=$dirty)"
    echo "      $path"
  done
fi

if [ "$MODE" = "audit" ]; then exit 0; fi

if [ "$MODE" = "remove" ] || [ "$MODE" = "all" ]; then
  echo ""
  echo "[정리 진행] ${#safe_idx[@]}개 머지된 worktree + 로컬 브랜치 삭제"
  removed=0; forced=0; failed=0
  for i in "${safe_idx[@]}"; do
    branch="${wt_branches[$i]}"
    path="${wt_paths[$i]}"
    if git worktree remove "$path" 2>/dev/null; then
      :
    elif git worktree remove --force "$path" 2>/dev/null; then
      forced=$((forced + 1))
    else
      failed=$((failed + 1))
      echo "  FAIL(worktree): $branch"
      continue
    fi
    if git branch -d "$branch" 2>/dev/null; then
      removed=$((removed + 1))
    else
      echo "  WARN(branch del): $branch  (worktree는 제거됨)"
    fi
  done
  echo "  완료: ${removed}개 (force 사용: ${forced}, 실패: ${failed})"
fi

if [ "$MODE" = "prune" ] || [ "$MODE" = "all" ]; then
  echo ""
  echo "[prune 진행]"
  git worktree prune -v || true
fi

echo ""
echo "=== 최종 상태 ==="
final_count=$(git worktree list | wc -l | tr -d ' ')
echo "  worktree 수: $final_count"
