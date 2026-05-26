#!/usr/bin/env bash
# scripts/ci/detect-changes.sh
# main 브랜치 대비 변경된 서비스 디렉토리를 감지하여 빌드 대상 목록을 출력한다.
set -euo pipefail

BASE_REF="${1:-origin/main}"
SERVICES=()

changed_files=$(git diff --name-only "$BASE_REF"...HEAD 2>/dev/null || git diff --name-only HEAD~1)

for svc_dir in services/*/; do
  svc_name="$(basename "$svc_dir")"
  if echo "$changed_files" | grep -q "^services/${svc_name}/\|^packages/core/"; then
    SERVICES+=("$svc_name")
  fi
done

# packages/core 변경 시 전체 BE 서비스 빌드
if echo "$changed_files" | grep -q "^packages/core/"; then
  for svc_dir in services/*/; do
    svc_name="$(basename "$svc_dir")"
    if [[ ! " ${SERVICES[*]} " =~ " ${svc_name} " ]]; then
      SERVICES+=("$svc_name")
    fi
  done
fi

# apps/web 변경 시 web 추가
if echo "$changed_files" | grep -q "^apps/web/"; then
  SERVICES+=("web")
fi

# JSON 배열로 출력 (CI matrix용 (플랫폼 미정))
if [ ${#SERVICES[@]} -eq 0 ]; then
  echo '[]'
else
  printf '%s\n' "${SERVICES[@]}" | jq -R . | jq -sc .
fi
