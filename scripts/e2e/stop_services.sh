#!/usr/bin/env bash
# E2E 테스트용 서비스 프로세스를 종료한다.
set -euo pipefail

PIDS_FILE="/tmp/oneerp_e2e_pids"

if [ ! -f "$PIDS_FILE" ]; then
    echo "PID 파일이 없습니다: $PIDS_FILE"
    exit 0
fi

while IFS= read -r pid; do
    if kill -0 "$pid" 2>/dev/null; then
        echo "프로세스 종료: $pid"
        kill "$pid" 2>/dev/null || true
    fi
done < "$PIDS_FILE"

rm -f "$PIDS_FILE"
echo "모든 서비스 종료 완료."
