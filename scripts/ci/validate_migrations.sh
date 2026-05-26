#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f "migrations/README.md" ]]; then
  echo "ERROR: migrations/README.md is missing" >&2
  exit 1
fi

# Validate naming convention for migration files (excluding README.md).
bad=0
while IFS= read -r -d '' file; do
  base="$(basename "$file")"
  if [[ "$base" == "README.md" ]]; then
    continue
  fi
  if [[ ! "$base" =~ ^[0-9]{8}_[0-9]{4}__[a-z0-9][a-z0-9_-]*\.(py|md)$ ]]; then
    echo "ERROR: invalid migration filename: $file" >&2
    bad=1
  fi
done < <(find migrations -maxdepth 1 -type f -print0)

if [[ "$bad" -ne 0 ]]; then
  exit 1
fi

echo "migrations: OK"

