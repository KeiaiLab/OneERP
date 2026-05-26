#!/usr/bin/env bash
# E2E 테스트 실행 스크립트.
# compose 또는 로컬 개발 스택이 이미 FerretDB/NATS/Valkey 를 제공한다고 가정한다.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

export ONEERP_FERRETDB_URI="${ONEERP_FERRETDB_URI:-mongodb://localhost:27017}"
export FERRETDB_URI="${FERRETDB_URI:-${ONEERP_FERRETDB_URI}}"
export ONEERP_DATABASE_NAME="${ONEERP_DATABASE_NAME:-oneerp_e2e_test}"
export ONEERP_DEBUG="${ONEERP_DEBUG:-true}"
export NATS_URL="${NATS_URL:-nats://localhost:4222}"
export VALKEY_URL="${VALKEY_URL:-redis://localhost:6379}"

drop_e2e_database() {
    uv run --no-project --with pymongo python3 -c "
import os
from pymongo import MongoClient

client = MongoClient(os.environ['FERRETDB_URI'], serverSelectionTimeoutMS=2000)
client.drop_database(os.environ['ONEERP_DATABASE_NAME'])
client.close()
"
}

cleanup() {
    echo "=== 정리 ==="
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    echo "=== E2E 테스트 DB 삭제 ==="
    drop_e2e_database >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "=== 인프라 확인 ==="
for _ in $(seq 1 20); do
    uv run --no-project --with pymongo python3 -c "
import os
from pymongo import MongoClient
c = MongoClient(os.environ['FERRETDB_URI'], serverSelectionTimeoutMS=2000)
c.admin.command('ping')
" 2>/dev/null && break
    sleep 2
done

if ! uv run --no-project --with pymongo python3 -c "
import os
from pymongo import MongoClient
c = MongoClient(os.environ['FERRETDB_URI'], serverSelectionTimeoutMS=2000)
c.admin.command('ping')
" >/dev/null 2>&1; then
    echo "ERROR: FerretDB가 ${FERRETDB_URI} 에서 응답하지 않습니다. docker compose up -d postgres ferretdb valkey nats 후 재시도하세요." >&2
    exit 1
fi

echo "=== E2E 테스트 DB 초기화 ==="
drop_e2e_database

./scripts/dev/init-nats-streams.sh >/dev/null 2>&1 || true

echo "=== 서비스 기동 ==="
for svc_port in "gateway:8001" "selling:8002" "buying:8003" "stock:8004" "accounting:8005" \
                "hr:8006" "payroll:8007" "expenses:8008" "crm:8009" "assets:8010" \
                "projects:8011" "quality:8012"; do
    svc="${svc_port%%:*}"
    port="${svc_port##*:}"
    uv run --package "oneerp-${svc}" --directory "services/${svc}" \
        uvicorn app.main:app --host 127.0.0.1 --port "$port" > /dev/null 2>&1 &
done

sleep 4

echo "=== E2E 테스트 실행 ==="
uv run --directory core --with fastapi --with uvicorn python -m pytest ../tests/e2e/ -m e2e -v --tb=short

echo "=== E2E 테스트 완료 ==="
