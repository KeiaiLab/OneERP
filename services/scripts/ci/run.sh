#!/usr/bin/env bash
# oneerp-services 레포 전체 품질 게이트
# 도메인별 디렉토리 구조에서 린트·타입검사·테스트를 실행한다.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

echo "=== BE 품질 게이트 (oneerp-services) ==="

echo "[1/5] ruff format (check)"
uv run ruff format --check .

echo "[2/5] ruff lint"
uv run ruff check .

echo "[3/5] ty type check"
uv run ty check .

export ONEERP_DEBUG=true

echo "[4/5] unit tests — core"
uv run pytest -m "not integration and not e2e" core/tests/ -q

echo "[4/5] unit tests — services (도메인별 독립 실행)"
DOMAINS=(finance hr scm sales platform collab marketing logistics portal compliance assets ehs)
for domain in "${DOMAINS[@]}"; do
  for svc_dir in "${domain}"/*/; do
    svc_name="$(basename "$svc_dir")"
    echo "  [${domain}/${svc_name}]"
    if [[ ! -d "$svc_dir/tests" ]]; then
      echo "    SKIP: tests/ 디렉토리 없음"
      continue
    fi
    if [[ "$svc_name" == "gateway" ]]; then
      unset ONEERP_TEST_TENANT_ID ONEERP_TEST_USER_SUB ONEERP_TEST_USER_ROLES \
        ONEERP_TEST_USER_PERMISSIONS ONEERP_TEST_USER_TIER || true
    else
      export ONEERP_TEST_TENANT_ID=test-tenant
      export ONEERP_TEST_USER_SUB=tenant-admin
      export ONEERP_TEST_USER_ROLES=admin
      export ONEERP_TEST_USER_PERMISSIONS='*:*'
      export ONEERP_TEST_USER_TIER=tenant_admin
    fi
    uv run --directory "$svc_dir" pytest tests/ -m "not integration and not e2e" -q
  done
done
unset ONEERP_TEST_TENANT_ID ONEERP_TEST_USER_SUB ONEERP_TEST_USER_ROLES \
  ONEERP_TEST_USER_PERMISSIONS ONEERP_TEST_USER_TIER

echo "[5/5] deployment catalog validation"
uv run python -m scripts.deploy validate

echo ""
echo "=== 전체 품질 게이트 통과 ==="
