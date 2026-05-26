#!/usr/bin/env bash
# NATS JetStream 스트림 초기화
set -euo pipefail

NATS_URL="${NATS_URL:-nats://localhost:4222}"

echo "=== ONEERP 메인 스트림 생성 ==="
nats -s "$NATS_URL" stream add ONEERP \
  --subjects "oneerp.>" \
  --retention limits \
  --max-bytes 1073741824 \
  --max-age 168h \
  --storage file \
  --replicas 3 \
  --discard old \
  --dupe-window 2m \
  --no-allow-rollup \
  --deny-delete \
  --deny-purge || echo "ONEERP 스트림 이미 존재"

echo "=== ONEERP DLQ 스트림 생성 ==="
nats -s "$NATS_URL" stream add ONEERP_DLQ \
  --subjects "oneerp.dlq.>" \
  --retention limits \
  --max-bytes 536870912 \
  --max-age 720h \
  --storage file \
  --replicas 3 || echo "ONEERP_DLQ 스트림 이미 존재"

echo "=== 스트림 목록 확인 ==="
nats -s "$NATS_URL" stream ls
