#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

expected_uv_minor="0.11"
actual_uv="$(uv --version | awk '{print $2}')"
actual_uv_minor="${actual_uv%.*}"
if [[ "$actual_uv_minor" != "$expected_uv_minor" ]]; then
  echo "ERROR: uv version mismatch. expected=${expected_uv_minor}.x actual=$actual_uv" >&2
  exit 1
fi

PYTHON_GATE_FILES=(
  "core/tests/unit/test_kernel_architecture_boundaries.py"
  "core/tests/unit/test_app_factory.py"
  "core/tests/unit/test_worker_plane_domains.py"
  "core/tests/unit/test_plane_assembler.py"
  "services/hr/learning/tests/unit/test_context_boundary.py"
  "services/sales/reservation/tests/unit/test_context_boundary.py"
)

: "${ONEERP_JWT_SECRET:=ci-local-secret-000000000000000000000000}"
: "${ONEERP_DEBUG:=true}"
: "${ONEERP_FERRETDB_URI:=mongodb://localhost:27017}"

export ONEERP_JWT_SECRET ONEERP_DEBUG ONEERP_FERRETDB_URI

echo "=== BE 최소 품질 게이트 ==="

echo "[1/9] ruff format (gate files)"
uv run ruff format --check "${PYTHON_GATE_FILES[@]}"

echo "[2/9] ruff lint (gate files)"
uv run ruff check "${PYTHON_GATE_FILES[@]}"

echo "[3/9] ty type check (gate files)"
uv run ty check "${PYTHON_GATE_FILES[@]}"

echo "[4/9] architecture gate"
uv run --directory core --with fastapi python -m pytest tests/unit/test_kernel_architecture_boundaries.py -q

echo "[5/9] assembly gate"
uv run --directory core --with fastapi python -m pytest \
  tests/unit/test_app_factory.py \
  tests/unit/test_worker_plane_domains.py \
  tests/unit/test_plane_assembler.py \
  -q

echo "[6/9] bounded-context gates"
uv run --with fastapi python -m pytest services/hr/learning/tests/unit/test_context_boundary.py services/sales/reservation/tests/unit/test_context_boundary.py -q

echo "[7/9] OpenAPI drift gate"
./scripts/ci/check_openapi_drift.sh

echo "[8/9] contract + deploy gate"
./scripts/ci/run_contract_tests.sh

echo "[9/11] buildx compliance (ADR-0010 §2.1, CLAUDE.md)"
python3 ./scripts/ci/check_buildx_compliance.py

echo "[10/11] dependency audit (G3-5 · pip-audit + pnpm audit)"
./scripts/ci/dep_audit.sh

echo "[11/11] commercial readiness audit (ADR-0001 23 gates)"
python3 ./scripts/audit/commercial_readiness.py --format text >/dev/null
echo "  audit ok"

echo ""
echo "=== FE 품질 게이트 ==="

if command -v pnpm &>/dev/null && [[ -f "$ROOT_DIR/pnpm-lock.yaml" ]]; then
  echo "[FE 1/4] biome ci"
  pnpm --filter @oneerp/web lint

  echo "[FE 2/4] tsc --noEmit"
  pnpm --filter @oneerp/web typecheck

  echo "[FE 3/4] vitest"
  pnpm --filter @oneerp/web test

  echo "[FE 4/4] next build"
  pnpm --filter @oneerp/web build
else
  echo "SKIP: pnpm 미설치 또는 pnpm-lock.yaml 없음"
fi

echo ""
echo "=== 전체 품질 게이트 통과 ==="
