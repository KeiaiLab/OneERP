#!/usr/bin/env bash
# ADR-0014 — 단일 docker-compose.yml 스택 종료.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

docker compose --profile plane down "$@"
