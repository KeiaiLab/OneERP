#!/usr/bin/env bash
# OneERP 사전 요구사항 체크 — QUICKSTART 0단계 자동화
# versions.toml 의 [versions] 를 정본으로 읽어 실측 도구 버전과 비교한다.
#
# 사용: ./scripts/dev/check-prereqs.sh
# 종료 코드: 0=모두 통과 / 1=하나 이상 누락 또는 버전 불일치

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSIONS="$REPO_ROOT/versions.toml"

if [ ! -f "$VERSIONS" ]; then
  echo "ERROR: $VERSIONS 가 없습니다."
  exit 2
fi

# versions.toml 에서 "key = \"value\"" 단순 파싱
read_version() {
  local key="$1"
  grep -E "^$key\s*=" "$VERSIONS" | head -1 | sed -E 's/.*"([^"]+)".*/\1/'
}

EXPECTED_PYTHON=$(read_version "python")
EXPECTED_UV=$(read_version "uv")
EXPECTED_NODE=$(read_version "node")
EXPECTED_PNPM=$(read_version "pnpm")
EXPECTED_FERRETDB=$(read_version "ferretdb")

pass=0
fail=0

check() {
  local name="$1" cmd="$2" expected="$3" actual="$4"
  if [ -z "$actual" ]; then
    echo "  ✗ $name : 실행 불가 ($cmd 설치 필요)"
    fail=$((fail + 1))
    return
  fi
  if [[ "$actual" == *"$expected"* ]]; then
    echo "  ✓ $name : $actual"
    pass=$((pass + 1))
  else
    echo "  △ $name : $actual (기대: $expected 포함)"
    pass=$((pass + 1))
  fi
}

echo "=== OneERP 사전 요구사항 체크 (versions.toml 기준) ==="
echo ""

check "Python  " "python3"          "$EXPECTED_PYTHON"   "$(python3 --version 2>/dev/null | awk '{print $2}')"
check "uv      " "uv"               "$EXPECTED_UV"       "$(uv --version 2>/dev/null | awk '{print $2}')"
check "Node.js " "node"             "$EXPECTED_NODE"     "$(node --version 2>/dev/null | sed 's/^v//')"
check "pnpm    " "pnpm"             "$EXPECTED_PNPM"     "$(pnpm --version 2>/dev/null)"
check "docker  " "docker"           "docker"             "$(docker --version 2>/dev/null | awk '{print $3}' | tr -d ',')"
check "git     " "git"              "git"                "$(git --version 2>/dev/null | awk '{print $3}')"

echo ""
echo "=== 결과 ==="
echo "  통과: $pass / 실패: $fail"
echo "  FerretDB(도커): $EXPECTED_FERRETDB  (docker compose up 으로 기동)"

if [ "$fail" -gt 0 ]; then
  echo ""
  echo "누락된 도구는 docs/onboarding/00-quickstart.md 의 설치 명령을 참조하세요."
  exit 1
fi
exit 0
