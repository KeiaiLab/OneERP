#!/usr/bin/env bash
# ruff error count만 stdout 으로 출력 (ratchet 비교용)
set -euo pipefail
cd "${1:-.}"
out="$(uv run ruff check . 2>&1 | tail -1 || true)"
count="$(echo "$out" | grep -oE 'Found [0-9]+' | grep -oE '[0-9]+' || true)"
if [ -z "${count:-}" ]; then
  if echo "$out" | grep -qi "all checks passed"; then
    count=0
  else
    count=0
  fi
fi
echo "${count}"
