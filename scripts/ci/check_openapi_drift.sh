#!/usr/bin/env bash
# OpenAPI 타입 drift 감지 — 생성 결과 vs 커밋 결과 비교
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# 타입 생성
./scripts/ci/gen_openapi_types.sh

# diff 확인
if git -C web rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  DIFF_CMD=(git -C web diff --exit-code -- lib/types/generated/)
  CACHED_DIFF_CMD=(git -C web diff --cached --exit-code -- lib/types/generated/)
  UNTRACKED_CMD=(git -C web ls-files --others --exclude-standard -- lib/types/generated/)
else
  DIFF_CMD=(git diff --exit-code -- web/lib/types/generated/)
  CACHED_DIFF_CMD=(git diff --cached --exit-code -- web/lib/types/generated/)
  UNTRACKED_CMD=(git ls-files --others --exclude-standard -- web/lib/types/generated/)
fi

if ! "${DIFF_CMD[@]}" || ! "${CACHED_DIFF_CMD[@]}"; then
  echo "ERROR: OpenAPI 타입이 코드와 동기화되지 않았습니다."
  echo "로컬에서 ./scripts/ci/gen_openapi_types.sh 실행 후 커밋하세요."
  exit 1
fi

UNTRACKED="$("${UNTRACKED_CMD[@]}")"
if [[ -n "$UNTRACKED" ]]; then
  echo "ERROR: OpenAPI 생성 타입에 미추적 파일이 있습니다."
  echo "$UNTRACKED"
  echo "로컬에서 ./scripts/ci/gen_openapi_types.sh 실행 후 커밋하세요."
  exit 1
fi

echo "OpenAPI 타입 동기화 확인 완료"
