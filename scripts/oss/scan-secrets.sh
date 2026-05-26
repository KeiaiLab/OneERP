#!/usr/bin/env bash
set -euo pipefail

REPORT_DIR="artifacts/secrets"
mkdir -p "$REPORT_DIR"

echo "=== gitleaks: 현재 소스 스캔 ==="
gitleaks dir . \
  --report-path "$REPORT_DIR/gitleaks-source-$(date +%Y%m%d).json" \
  --report-format json \
  --verbose \
  --exit-code 0 2>/dev/null || echo "gitleaks 미설치 — 수동 설치 필요 (brew install gitleaks)"

echo ""
echo "=== 하드코딩 내부 주소 grep ==="
grep -rn \
  --include='*.py' --include='*.yaml' --include='*.yml' \
  --include='*.toml' --include='*.json' --include='*.ts' --include='*.tsx' \
  'keiailab\.com\|116\.37\.\|bastion' . \
  | grep -v '.git/' \
  | grep -v 'node_modules/' \
  | tee "$REPORT_DIR/internal-refs-$(date +%Y%m%d).txt" || true

echo ""
echo "=== API 키/패스워드 패턴 grep ==="
grep -rn \
  --include='*.py' --include='*.yaml' --include='*.yml' \
  --include='*.toml' --include='*.json' \
  'password\s*=\s*["\x27][^$]\|api_key\s*=\s*["\x27][^$]\|secret\s*=\s*["\x27][^$]' . \
  | grep -v '.git/' \
  | grep -v 'node_modules/' \
  | grep -v '.env.example' \
  | grep -v 'test' \
  | tee "$REPORT_DIR/hardcoded-secrets-$(date +%Y%m%d).txt" || true

echo ""
echo "결과: $REPORT_DIR/"
ls -la "$REPORT_DIR/"
