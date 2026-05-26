#!/usr/bin/env bash
# 5 docs health check 트랙 통합 러너.
# spec: docs/superpowers/specs/2026-04-13-docs-health-audit-design.md §4
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

run() {
  local name="$1"; shift
  echo "=== ${name} ==="
  "$@"
  local rc=$?
  echo "exit=${rc}"
  return $rc
}

fail=0
run "S1 stale-refs"     uv run python scripts/docs/check_stale_refs.py     || fail=$((fail+1))
run "S2 version-drift"  uv run python scripts/docs/render_versions.py      || fail=$((fail+1))
run "S3 api-drift"      uv run python scripts/docs/audit_api_drift.py      || fail=$((fail+1))
run "S4 tutorials"      uv run python scripts/docs/audit_tutorials.py      || fail=$((fail+1))
run "S5 architecture"   uv run python scripts/docs/audit_architecture.py   || fail=$((fail+1))

echo
echo "총 실패 트랙: ${fail}"
[[ "$fail" -gt 0 ]] && exit 1
exit 0
