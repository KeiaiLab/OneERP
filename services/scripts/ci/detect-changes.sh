#!/usr/bin/env bash
# scripts/ci/detect-changes.sh (oneerp-services 레포용)
# 도메인별 디렉토리 구조에서 변경된 서비스를 감지한다.
# core submodule 변경 시 전체 BE 서비스를 빌드 대상에 포함한다.
set -euo pipefail

BASE_REF="${1:-origin/main}"
SERVICES=()
DOMAINS=(finance hr scm sales platform collab marketing logistics portal compliance assets ehs)

changed_files=$(git diff --name-only "$BASE_REF"...HEAD 2>/dev/null || git diff --name-only HEAD~1)

# core submodule 변경 여부 (submodule hash diff)
CORE_CHANGED=false
if git diff --name-only "$BASE_REF"...HEAD 2>/dev/null | grep -q "^core$"; then
  CORE_CHANGED=true
fi

for domain in "${DOMAINS[@]}"; do
  if [[ ! -d "$domain" ]]; then
    continue
  fi
  for svc_dir in "${domain}"/*/; do
    [[ -d "$svc_dir" ]] || continue
    svc_name="$(basename "$svc_dir")"

    # 해당 서비스 디렉토리에 변경이 있거나 core가 변경된 경우
    if echo "$changed_files" | grep -q "^${domain}/${svc_name}/" || $CORE_CHANGED; then
      if [[ ! " ${SERVICES[*]:-} " =~ " ${svc_name} " ]]; then
        SERVICES+=("$svc_name")
      fi
    fi
  done
done

# JSON 배열로 출력 (CI matrix용 (플랫폼 미정))
if [ ${#SERVICES[@]} -eq 0 ]; then
  echo '[]'
else
  printf '%s\n' "${SERVICES[@]}" | jq -R . | jq -sc .
fi
