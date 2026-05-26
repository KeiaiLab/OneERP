#!/usr/bin/env bash
# NATS JetStream 이벤트 재적용 도구 — G4-3 회계 복구 드릴에서
# 스냅샷 이후 장애 시점까지의 누락 이벤트를 consumer replay 로 재처리한다.
#
# 사용:
#   scripts/ops/replay-events.sh \
#       --stream accounting-events \
#       --from   2026-04-20T23:27:00Z \
#       --to     2026-04-20T23:59:00Z \
#       --consumer accounting-replay-$(date +%s)
#
# 옵션:
#   --stream   NAME   JetStream 스트림 이름 (필수).
#   --from     ISO8601 재적용 시작 시각 (필수).
#   --to       ISO8601 재적용 종료 시각 (선택, 기본=now).
#   --consumer NAME   일회용 consumer 이름 (기본: <stream>-replay-<epoch>).
#   --subject  FILTER 필터 subject (선택, 기본=stream 전체).
#   --dry-run          nats 호출 없이 계획만 출력.

set -euo pipefail

STREAM="" FROM="" TO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
CONSUMER="" SUBJECT=""
DRY_RUN=0

usage() { grep -E '^#( |$)' "$0" | sed 's/^# \{0,1\}//' ; exit "${1:-0}" ; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stream)   STREAM="$2"; shift 2 ;;
    --from)     FROM="$2"; shift 2 ;;
    --to)       TO="$2"; shift 2 ;;
    --consumer) CONSUMER="$2"; shift 2 ;;
    --subject)  SUBJECT="$2"; shift 2 ;;
    --dry-run)  DRY_RUN=1; shift ;;
    -h|--help)  usage 0 ;;
    *)          echo "unknown: $1" >&2; usage 2 ;;
  esac
done

[[ -z "$STREAM" || -z "$FROM" ]] && { echo "ERROR: --stream --from 필수" >&2; exit 2; }
: "${CONSUMER:=${STREAM}-replay-$(date +%s)}"

run() { if [[ "$DRY_RUN" = "1" ]]; then echo "[dry-run] $*"; else eval "$@"; fi ; }

command -v nats >/dev/null || { echo "nats CLI 미설치" >&2; exit 3; }

echo "==> 1/3 임시 consumer 생성: $CONSUMER (stream=$STREAM, from=$FROM, subject=${SUBJECT:-ALL})"
CREATE_ARGS=(consumer add "$STREAM" "$CONSUMER"
  --pull --deliver=by_start_time --opt-start-time="$FROM"
  --ack=explicit --replay=instant --wait=60s)
[[ -n "$SUBJECT" ]] && CREATE_ARGS+=(--filter "$SUBJECT")
run "nats ${CREATE_ARGS[*]}"

echo "==> 2/3 consumer 재처리 (until=$TO)"
# --count 0 = unlimited, --timeout 으로 전체 범위 처리 후 종료.
run "nats consumer next --count=0 --raw --timeout=10s $STREAM $CONSUMER | \
     python3 -c 'import json,sys,datetime as d; t=d.datetime.fromisoformat(\"$TO\".replace(\"Z\",\"+00:00\")); [print(l) for l in sys.stdin if (m:=json.loads(l).get(\"ts\")) and d.datetime.fromisoformat(m.replace(\"Z\",\"+00:00\")) <= t]'"

echo "==> 3/3 임시 consumer 삭제: $CONSUMER"
run "nats consumer rm -f $STREAM $CONSUMER"

echo
echo "재적용 기록:"
echo "  - stream:   $STREAM"
echo "  - subject:  ${SUBJECT:-(all)}"
echo "  - from→to:  $FROM → $TO"
echo "  - consumer: $CONSUMER"
echo "  - 완료:     $(date -u +%Y-%m-%dT%H:%M:%SZ)"
