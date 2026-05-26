#!/usr/bin/env bash
# 회계 balance drift 시뮬레이션 — G4-5 accounting 드릴 전용.
# staging 테넌트에 인위적인 차대 불일치를 주입해 P2 drift 검출·격리·복구 체인을 검증한다.
#
# 사용:
#   scripts/chaos/balance-drift.sh \
#       --tenant staging-tenant-1 \
#       --period 2026-04 \
#       --amount 123.45 \
#       --account-code 1100
#
# 안전장치:
#   - tenant 이름에 "staging" 또는 "dev" 포함 필수.
#   - 종료 시 trap 으로 주입 분개를 역전 분개로 취소.
#
# 전제:
#   - FerretDB 접근 가능한 mongosh.
#   - scripts/audit/gl_rebuild.py 로 drift 검출 → 자동 롤백 체인 검증.

set -euo pipefail

TENANT="" PERIOD="" AMOUNT="" ACCOUNT_CODE="" DRY_RUN=0
MONGO_URI="${FERRETDB_URI:-mongodb://ferretdb.services-staging.svc:27017/oneerp}"

usage() { grep -E '^#( |$)' "$0" | sed 's/^# \{0,1\}//' ; exit "${1:-0}" ; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tenant)       TENANT="$2"; shift 2 ;;
    --period)       PERIOD="$2"; shift 2 ;;
    --amount)       AMOUNT="$2"; shift 2 ;;
    --account-code) ACCOUNT_CODE="$2"; shift 2 ;;
    --uri)          MONGO_URI="$2"; shift 2 ;;
    --dry-run)      DRY_RUN=1; shift ;;
    -h|--help)      usage 0 ;;
    *)              echo "unknown: $1" >&2; usage 2 ;;
  esac
done

for f in TENANT PERIOD AMOUNT ACCOUNT_CODE; do
  [[ -z "${!f}" ]] && { echo "ERROR: --${f,,} 필수" >&2; exit 2; }
done
[[ "$TENANT" != *staging* && "$TENANT" != *dev* ]] && {
  echo "ERROR: tenant 이름에 staging/dev 필요 (got: $TENANT)" >&2
  exit 3
}

run() { if [[ "$DRY_RUN" = "1" ]]; then echo "[dry-run] $*"; else mongosh --quiet "$MONGO_URI" --eval "$*"; fi ; }

DRIFT_ID="drift-$(date +%s)"
INJECT="db.journal_entries.insertOne({
  _id: '$DRIFT_ID',
  tenant_id: '$TENANT',
  period: '$PERIOD',
  account_code: '$ACCOUNT_CODE',
  debit: $AMOUNT,
  credit: 0,
  memo: 'CHAOS: intentional drift for G4-5 drill',
  created_at: new Date()
})"
REVERSE="db.journal_entries.insertOne({
  _id: '$DRIFT_ID-reversal',
  tenant_id: '$TENANT',
  period: '$PERIOD',
  account_code: '$ACCOUNT_CODE',
  debit: 0,
  credit: $AMOUNT,
  memo: 'CHAOS: reversal of $DRIFT_ID',
  reverses: '$DRIFT_ID',
  created_at: new Date()
})"

cleanup() {
  echo "==> 역전 분개 삽입"
  run "$REVERSE"
  echo "==> drift 정리 완료: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
trap cleanup EXIT INT TERM

echo "==> drift 주입: tenant=$TENANT period=$PERIOD account=$ACCOUNT_CODE amount=$AMOUNT"
run "$INJECT"
echo "==> drift id=$DRIFT_ID 기록"

# Alertmanager 가 자동 분류·에스컬레이션 체인을 태우는 동안 대기.
# 드릴에서는 MTTR 측정을 위해 실측 필요 → 60초 관찰 윈도 유지.
echo "==> 60s 관찰 윈도 (MTTR 측정)"
for i in 1 2 3 4 5 6; do
  sleep 10
  echo "  [$((i*10))s] 관찰 중"
done
