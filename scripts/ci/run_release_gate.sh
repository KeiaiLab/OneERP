#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

log_stage() {
  printf '\n=== %s ===\n' "$1"
}

log_step() {
  printf '[release-gate] %s\n' "$1"
}

pick_port() {
  python3 - "$1" <<'PY'
from __future__ import annotations

import socket
import sys

preferred = int(sys.argv[1])


def available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("0.0.0.0", port))
        except OSError:
            return False
    return True


if available(preferred):
    print(preferred)
else:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        print(sock.getsockname()[1])
PY
}

export ONEERP_FERRETDB_HOST_PORT="${ONEERP_FERRETDB_HOST_PORT:-$(pick_port 27017)}"
export ONEERP_NATS_HOST_PORT="${ONEERP_NATS_HOST_PORT:-$(pick_port 4222)}"
export ONEERP_NATS_MONITOR_HOST_PORT="${ONEERP_NATS_MONITOR_HOST_PORT:-$(pick_port 8222)}"
export ONEERP_VALKEY_HOST_PORT="${ONEERP_VALKEY_HOST_PORT:-$(pick_port 6379)}"
export ONEERP_FERRETDB_URI="${ONEERP_FERRETDB_URI:-mongodb://localhost:${ONEERP_FERRETDB_HOST_PORT}}"
export FERRETDB_URI="${FERRETDB_URI:-${ONEERP_FERRETDB_URI}}"
export NATS_URL="${NATS_URL:-nats://localhost:${ONEERP_NATS_HOST_PORT}}"
export VALKEY_URL="${VALKEY_URL:-redis://localhost:${ONEERP_VALKEY_HOST_PORT}}"

log_stage "정적"
log_step "scripts/ci/run.sh"
./scripts/ci/run.sh

log_stage "조립"
log_step "compose host ports ferretdb=${ONEERP_FERRETDB_HOST_PORT} nats=${ONEERP_NATS_HOST_PORT} valkey=${ONEERP_VALKEY_HOST_PORT}"
log_step "scripts/dev/stack-smoke.sh"
NATS_URL=nats://nats:4222 NOCLEAN=1 ./scripts/dev/stack-smoke.sh

log_stage "데이터"
log_step "scripts/dev/seed-data.sh"
./scripts/dev/seed-data.sh

log_stage "사용자 시나리오"
log_step "scripts/ci/run_e2e.sh"
./scripts/ci/run_e2e.sh
log_step "web/tests/e2e/smoke.spec.ts"
(
  cd web
  pnpm exec playwright test tests/e2e/smoke.spec.ts
)

printf '\n=== release gate 통과 ===\n'
