#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

export FERRETDB_URI="${FERRETDB_URI:-mongodb://localhost:27017}"

cleanup() {
  if docker compose version >/dev/null 2>&1; then
    docker compose down -v --remove-orphans >/dev/null 2>&1 || true
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose down -v --remove-orphans >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

if docker compose version >/dev/null 2>&1; then
  docker compose up -d --wait
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose up -d
else
  echo "ERROR: docker compose is not available in this environment" >&2
  exit 1
fi

uv run pytest -m integration
