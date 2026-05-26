#!/usr/bin/env bash
# 의존성 취약점 스캔 CI 게이트 — G3-5.
# Python: pip-audit (PyPI Advisory + OSV)
# JavaScript: npm audit / pnpm audit
#
# 사용 (CI):
#   ./scripts/ci/dep_audit.sh               # 전수 검사, 취약점 1건 이상 시 non-zero exit
#   ./scripts/ci/dep_audit.sh --report-only # 보고만 하고 exit 0 (기존 파이프 차단 방지)
#
# 출력 아티팩트:
#   artifacts/dep-audit/pip-audit.json
#   artifacts/dep-audit/npm-audit.json
#
# 정책:
#   - critical / high: fail (exit 1)
#   - medium: warn (로그 만)
#   - low: 보고만

set -euo pipefail

REPORT_ONLY=0
if [[ "${1:-}" == "--report-only" ]]; then REPORT_ONLY=1; fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

OUT_DIR="${REPO_ROOT}/artifacts/dep-audit"
mkdir -p "$OUT_DIR"

exit_code=0
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }

echo "[$(now)] === pip-audit (Python) ==="
if command -v uv >/dev/null 2>&1; then
  # uv 통합 pip-audit (uv.lock 기반)
  if ! uv tool run --from pip-audit pip-audit \
      --format json --output "$OUT_DIR/pip-audit.json" \
      --vulnerability-service osv; then
    HIGH=$(jq '[.dependencies[]? | .vulns[]? | select(.fix_versions)] | length' "$OUT_DIR/pip-audit.json" 2>/dev/null || echo 0)
    echo "[$(now)] pip-audit 발견: $HIGH 건"
    [[ "$REPORT_ONLY" = "0" ]] && exit_code=1
  else
    echo "[$(now)] pip-audit clean"
  fi
else
  echo "[$(now)] uv 미설치 — pip-audit 건너뜀"
fi

echo "[$(now)] === npm audit (JavaScript) ==="
if [[ -f pnpm-lock.yaml ]] && command -v pnpm >/dev/null 2>&1; then
  # pnpm audit (npm audit 프로토콜 호환)
  if ! pnpm audit --audit-level high --json > "$OUT_DIR/npm-audit.json" 2>&1; then
    HIGH=$(jq '.metadata.vulnerabilities.high // 0' "$OUT_DIR/npm-audit.json" 2>/dev/null || echo 0)
    CRIT=$(jq '.metadata.vulnerabilities.critical // 0' "$OUT_DIR/npm-audit.json" 2>/dev/null || echo 0)
    echo "[$(now)] pnpm audit high=$HIGH critical=$CRIT"
    if [[ "$REPORT_ONLY" = "0" && (( HIGH > 0 || CRIT > 0 )) ]]; then exit_code=1; fi
  else
    echo "[$(now)] pnpm audit clean"
  fi
elif [[ -f package-lock.json ]] && command -v npm >/dev/null 2>&1; then
  npm audit --audit-level=high --json > "$OUT_DIR/npm-audit.json" 2>&1 || {
    echo "[$(now)] npm audit 경보"
    [[ "$REPORT_ONLY" = "0" ]] && exit_code=1
  }
else
  echo "[$(now)] pnpm/npm lockfile 또는 바이너리 없음 — npm audit 건너뜀"
fi

echo
echo "[$(now)] === 요약 ==="
echo "리포트: $OUT_DIR/"
echo "정책: critical/high 건은 CI fail. medium 이하는 보고만."
if [[ "$exit_code" -eq 0 && -f "$OUT_DIR/pip-audit.json" && -f "$OUT_DIR/npm-audit.json" ]]; then
  python3 scripts/ci/record_dep_audit_evidence.py \
    --pip-report "$OUT_DIR/pip-audit.json" \
    --npm-report "$OUT_DIR/npm-audit.json" \
    --command "./scripts/ci/dep_audit.sh"
fi
exit $exit_code
