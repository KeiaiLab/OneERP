#!/usr/bin/env bash
# ADR-0014 — 단일 compose 기반 6 Plane 스모크 테스트.
#
# 사용:
#   scripts/dev/stack-smoke.sh              # 기본: plane 프로파일
#   PROFILE=full scripts/dev/stack-smoke.sh # full 프로파일 (동일 효과)
#
# 동작:
#   1) compose up -d --profile <p>
#   2) healthcheck healthy 대기 (최대 TIMEOUT 초)
#   3) 각 plane 의 /health 를 컨테이너 내부에서 curl (외부 port 비노출 모델)
#   4) NOCLEAN=1 이 아니면 compose down
#
# 환경변수:
#   PROFILE   기본 profile (기본: plane)
#   TIMEOUT   healthcheck 대기 초 (기본 120)
#   NOCLEAN   down 스킵
set -euo pipefail

PROFILE="${1:-${PROFILE:-plane}}"
TIMEOUT="${TIMEOUT:-120}"
COMPOSE_ARGS=(--profile "${PROFILE}")

BLUE="\033[1;34m"
GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
RESET="\033[0m"

log()  { printf "${BLUE}[smoke]${RESET} %s\n" "$*" >&2; }
ok()   { printf "${GREEN}[ ✓ ]${RESET} %s\n" "$*" >&2; }
err()  { printf "${RED}[ ✗ ]${RESET} %s\n" "$*" >&2; }
warn() { printf "${YELLOW}[ ! ]${RESET} %s\n" "$*" >&2; }

cleanup() {
  if [[ -z "${NOCLEAN:-}" ]]; then
    log "compose down 실행"
    docker compose "${COMPOSE_ARGS[@]}" down 2>/dev/null || true
  else
    warn "NOCLEAN=1 — 컨테이너를 남겨둔다 (수동 정리 필요)"
  fi
}

trap cleanup EXIT

log "profile=${PROFILE} timeout=${TIMEOUT}s"
log "docker compose up -d"
docker compose "${COMPOSE_ARGS[@]}" up -d

log "healthcheck 대기 (최대 ${TIMEOUT}s)"
deadline=$(( $(date +%s) + TIMEOUT ))
healthy=0
while [[ $(date +%s) -lt $deadline ]]; do
  total=$(docker compose "${COMPOSE_ARGS[@]}" ps --format json 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$total" == "0" ]]; then
    sleep 2
    continue
  fi
  pending=$(docker compose "${COMPOSE_ARGS[@]}" ps --format json 2>/dev/null \
    | grep -cE '"Health":"(starting|unhealthy)"' || true)
  if [[ "$pending" == "0" ]]; then
    healthy=1
    break
  fi
  sleep 3
done

if [[ "$healthy" != "1" ]]; then
  err "healthcheck timeout"
  docker compose "${COMPOSE_ARGS[@]}" ps
  exit 1
fi
ok "모든 컨테이너 healthy"

# NATS JetStream stream 초기화 — plane 의 subscribe 가 stream name 해석에
# 성공하려면 stream 이 선행 존재해야 함. 재기동 시나리오에서 recovery 경로를
# 실제로 트리거하기 위한 사전 조건.
log "NATS JetStream stream 초기화"
if ! ./scripts/dev/init-nats-streams.sh >/dev/null 2>&1; then
  err "NATS stream 초기화 실패 — 이후 테스트는 의미 없음"
  docker compose "${COMPOSE_ARGS[@]}" logs --tail=30 nats
  exit 1
fi
ok "NATS stream 초기화 완료"

# stream 이 생성되었으므로 plane 들이 최초 구독을 제대로 등록하도록 worker-plane 재기동.
# (최초 기동 때는 stream 이 없어 부분 구독 상태였을 수 있음.)
log "worker-plane 재기동 — stream 생성 후 최초 구독 반영"
docker compose "${COMPOSE_ARGS[@]}" restart worker-plane >/dev/null 2>&1
sleep 5

# Plane 서비스만 추출 (인프라 제외).
planes=$(docker compose "${COMPOSE_ARGS[@]}" ps --format '{{.Service}}' 2>/dev/null \
  | grep -- '-plane$' | sort -u)

pass=0
fail=0
log "plane /health curl 시작 (컨테이너 내부 — 외부 port 미노출 모델)"
for plane in $planes; do
  if docker compose "${COMPOSE_ARGS[@]}" exec -T "$plane" \
       python -c 'import urllib.request,sys; sys.exit(0 if urllib.request.urlopen("http://localhost:8000/health",timeout=2).status==200 else 1)' \
       >/dev/null 2>&1; then
    ok "${plane} /health → 200"
    pass=$((pass + 1))
  else
    err "${plane} /health 실패"
    fail=$((fail + 1))
  fi
done

# ── 재기동 시나리오: durable consumer 재바인딩 검증 ──
log "재기동 시나리오: worker-plane 재기동 후 구독 recovery 확인"
docker compose "${COMPOSE_ARGS[@]}" restart worker-plane >/dev/null 2>&1

deadline=$(( $(date +%s) + 30 ))
worker_healthy=0
while [[ $(date +%s) -lt $deadline ]]; do
  status=$(docker compose "${COMPOSE_ARGS[@]}" ps --format '{{.Service}}:{{.Status}}' worker-plane 2>/dev/null | grep -o 'healthy' || true)
  if [[ "$status" == "healthy" ]]; then
    worker_healthy=1
    break
  fi
  sleep 2
done

if [[ "$worker_healthy" != "1" ]]; then
  err "재기동 후 worker-plane 이 healthy 가 되지 않음"
  docker compose "${COMPOSE_ARGS[@]}" logs --tail=50 worker-plane
  fail=$((fail + 1))
else
  # subject dedup 구현 후 '부분 구독 상태' 도 실제 회귀 시신호이므로 fail 로 판정.
  bad=$(docker compose "${COMPOSE_ARGS[@]}" logs --since=30s worker-plane 2>/dev/null \
    | grep -cE '이벤트 구독 없이 시작|부분 구독 상태' || true)
  if [[ "$bad" -gt 0 ]]; then
    err "재기동 후 금칙어 발견 (count=${bad}) — recovery 또는 subject dedup 회귀"
    docker compose "${COMPOSE_ARGS[@]}" logs --since=30s worker-plane | tail -30
    fail=$((fail + 1))
  else
    ok "worker-plane 재기동 recovery + subject dedup 정상 — 금칙어 없음"
  fi
fi

echo >&2
log "결과: ${pass} pass / ${fail} fail"
[[ "$fail" -gt 0 ]] && exit 1
exit 0
