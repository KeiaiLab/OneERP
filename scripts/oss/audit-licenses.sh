#!/usr/bin/env bash
set -euo pipefail

REPORT_DIR="artifacts/dep-audit"
mkdir -p "$REPORT_DIR"

echo "=== Python 라이선스 ==="
uv run pip-licenses --format=csv --with-urls \
  --output-file="$REPORT_DIR/python-licenses.csv" 2>/dev/null || \
  echo "⚠️ pip-licenses 실행 실패 — 수동 확인 필요"

echo "=== Node.js 라이선스 ==="
if [ -d "apps/web" ]; then
  cd apps/web
  npx license-checker --csv --out "../../$REPORT_DIR/node-licenses.csv" 2>/dev/null || \
    echo "⚠️ license-checker 실행 실패 — 수동 확인 필요"
  cd ../..
fi

echo "=== AGPL 비호환 검사 ==="
if ls "$REPORT_DIR"/*.csv 1>/dev/null 2>&1; then
  grep -i 'CPAL\|Sleepycat\|QPL\|RPSL\|SSPL' "$REPORT_DIR"/*.csv 2>/dev/null && \
    echo "⚠️ 비호환 라이선스 발견!" || \
    echo "✅ AGPL 비호환 라이선스 없음"
else
  echo "⚠️ 라이선스 CSV 미생성 — 수동 확인 필요"
fi
