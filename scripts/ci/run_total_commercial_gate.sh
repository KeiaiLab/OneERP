#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

printf '\n=== SaaS release catalog 불변성 확인 ===\n'
python3 scripts/ci/check_saas_release_catalog.py

printf '\n=== 기본 릴리즈 게이트 ===\n'
./scripts/ci/run_release_gate.sh

printf '\n=== 성능/복구/운영 필수 근거 파일 확인 ===\n'
python3 scripts/ci/check_release_rehearsal_evidence.py

printf '\n=== 47모듈 x 23게이트 strict 상용 준비도 확인 ===\n'
python3 scripts/audit/commercial_readiness.py --verify --strict --format text >/dev/null

printf '\n=== total commercial gate 통과 ===\n'
