#!/usr/bin/env bash
# 12개 서비스를 각각 다른 포트에 background로 기동한다.
# 사전 조건: FerretDB가 localhost:27017에서 실행 중이어야 한다.
# 사용법: ./scripts/e2e/start_services.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

export ONEERP_FERRETDB_URI="${FERRETDB_URI:-mongodb://localhost:27017}"
export ONEERP_DATABASE_NAME="oneerp_e2e_test"
export ONEERP_DEBUG="true"

PIDS_FILE="/tmp/oneerp_e2e_pids"
: > "$PIDS_FILE"

declare -A SERVICES=(
    [gateway]=8001
    [selling]=8002
    [buying]=8003
    [stock]=8004
    [accounting]=8005
    [hr]=8006
    [payroll]=8007
    [expenses]=8008
    [crm]=8009
    [assets]=8010
    [projects]=8011
    [quality]=8012
)

for svc in "${!SERVICES[@]}"; do
    port="${SERVICES[$svc]}"
    echo "서비스 기동: $svc (포트 $port)"
    uv run --package "oneerp-${svc}" --directory "services/${svc}" \
        uvicorn app.main:app --host 127.0.0.1 --port "$port" > /dev/null 2>&1 &
    echo $! >> "$PIDS_FILE"
done

echo "모든 서비스 기동 완료. PID 파일: $PIDS_FILE"
echo "서비스가 준비될 때까지 대기 중..."

for svc in "${!SERVICES[@]}"; do
    port="${SERVICES[$svc]}"
    for i in $(seq 1 30); do
        if curl -sf "http://127.0.0.1:${port}/health" > /dev/null 2>&1; then
            echo "  ✓ $svc 준비 완료"
            break
        fi
        if [ "$i" -eq 30 ]; then
            echo "  ✗ $svc 기동 실패 (포트 $port)"
            exit 1
        fi
        sleep 1
    done
done

echo "전체 서비스 준비 완료."
