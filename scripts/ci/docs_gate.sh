#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  if command -v python &>/dev/null; then
    PYTHON_BIN="python"
  elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
  else
    echo "ERROR: python 또는 python3 필요"
    exit 1
  fi
fi

echo "=== 문서 품질 게이트 ==="

# [1/3] Markdown 린트 (기존 문서 정리 전까지 경고 모드)
echo "[1/4] markdownlint-cli2 (경고 모드)"
if command -v npx &>/dev/null; then
  npx markdownlint-cli2 "docs/**/*.md" "*.md" || echo "WARN: markdownlint 오류 발견 — 경고 모드이므로 계속 진행"
else
  echo "WARN: npx 미설치 — markdownlint 스킵"
fi

# [2/4] 로컬 문서 무결성 검증
echo "[2/4] 로컬 문서 무결성 검증"
"$PYTHON_BIN" scripts/docs/check_integrity.py

# [3/4] 링크 검증
echo "[3/4] lychee 링크 검증"
if command -v lychee &>/dev/null; then
  lychee --no-progress "docs/**/*.md" "*.md" || echo "WARN: 일부 링크 검증 실패"
else
  echo "WARN: lychee 미설치 — 링크 검증 스킵"
fi

# [4/4] ADR 구조 검증 — 필수 섹션 존재 여부
echo "[4/4] ADR 구조 검증"
adr_errors=0
for adr in docs/governance/adr/[0-9]*.md; do
  [ -f "$adr" ] || continue
  # 템플릿(0000)은 스킵
  basename_adr="$(basename "$adr")"
  if [[ "$basename_adr" == "0000-"* ]]; then
    continue
  fi
  for section in "## 맥락" "## 결정" "## 대안" "## 근거" "## 영향" "## 실행 항목"; do
    if ! grep -q "$section" "$adr"; then
      echo "ERROR: $adr 에 '$section' 섹션 누락"
      adr_errors=$((adr_errors + 1))
    fi
  done
done
if [ "$adr_errors" -gt 0 ]; then
  echo "ADR 구조 검증 실패: ${adr_errors}건 오류"
  exit 1
fi

echo ""
echo "=== 문서 품질 게이트 통과 ==="
