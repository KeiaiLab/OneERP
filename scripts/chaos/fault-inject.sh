#!/usr/bin/env bash
# 카오스 장애 주입 도구 — G4-5 On-call 응답 드릴에서 사용.
# staging Deployment 에 일시적 결함(5xx / latency / crash) 을 주입해
# Alertmanager → PagerDuty 체인의 MTTA/MTTR 을 측정한다.
#
# 사용:
#   scripts/chaos/fault-inject.sh gateway --kind 5xx --duration 5m
#   scripts/chaos/fault-inject.sh accounting --kind crash --duration 2m
#
# 옵션:
#   POSITIONAL       주입 대상 모듈(= Deployment 이름).
#   --kind KIND      5xx | latency | crash | oom (기본 5xx).
#   --duration DUR   주입 지속시간 (기본 5m). `sleep` 포맷.
#   --namespace NS   기본 services-staging (운영 주입 금지).
#   --dry-run         patch 없이 계획만 출력.
#
# 안전장치:
#   - namespace 에 "staging" 또는 "dev" 가 포함돼야 실행. 운영 주입 방지.
#   - 종료 시 trap 으로 반드시 원상복구.

set -euo pipefail

MODULE="" KIND="5xx" DURATION="5m" NS="services-staging" DRY_RUN=0

usage() { grep -E '^#( |$)' "$0" | sed 's/^# \{0,1\}//' ; exit "${1:-0}" ; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --kind)      KIND="$2"; shift 2 ;;
    --duration)  DURATION="$2"; shift 2 ;;
    --namespace) NS="$2"; shift 2 ;;
    --dry-run)   DRY_RUN=1; shift ;;
    -h|--help)   usage 0 ;;
    --*)         echo "unknown: $1" >&2; usage 2 ;;
    *)           MODULE="$1"; shift ;;
  esac
done

[[ -z "$MODULE" ]] && { echo "ERROR: 모듈 이름 필수" >&2; usage 2; }
[[ "$NS" != *staging* && "$NS" != *dev* ]] && {
  echo "ERROR: 안전장치 — namespace 에 staging/dev 포함 필요 (got: $NS)" >&2
  exit 3
}

run() { if [[ "$DRY_RUN" = "1" ]]; then echo "[dry-run] $*"; else eval "$@"; fi ; }

# 결함별 patch 전략 (envvar 주입으로 런타임에 인식되는 것을 가정).
case "$KIND" in
  5xx)     PATCH='{"spec":{"template":{"spec":{"containers":[{"name":"app","env":[{"name":"CHAOS_FORCE_5XX","value":"1"}]}]}}}}' ;;
  latency) PATCH='{"spec":{"template":{"spec":{"containers":[{"name":"app","env":[{"name":"CHAOS_LATENCY_MS","value":"2000"}]}]}}}}' ;;
  crash)   PATCH='{"spec":{"template":{"spec":{"containers":[{"name":"app","env":[{"name":"CHAOS_CRASH_ON_STARTUP","value":"1"}]}]}}}}' ;;
  oom)     PATCH='{"spec":{"template":{"spec":{"containers":[{"name":"app","resources":{"limits":{"memory":"16Mi"}}}]}}}}' ;;
  *)       echo "ERROR: unknown --kind: $KIND" >&2; exit 2 ;;
esac

# 원상복구 patch (주입 env 제거).
CLEANUP='{"spec":{"template":{"spec":{"containers":[{"name":"app","env":null}]}}}}'

cleanup() {
  echo "==> 복구 시작"
  run "kubectl -n $NS patch deployment $MODULE --type=strategic --patch '$CLEANUP'"
  echo "==> 복구 완료: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
trap cleanup EXIT INT TERM

echo "==> chaos 주입: module=$MODULE kind=$KIND duration=$DURATION namespace=$NS"
echo "시각: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
run "kubectl -n $NS patch deployment $MODULE --type=strategic --patch '$PATCH'"

echo "==> 대기: $DURATION"
run "sleep $DURATION"

# cleanup trap 이 복구 수행.
