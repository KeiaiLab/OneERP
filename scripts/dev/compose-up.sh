#!/usr/bin/env bash
# ADR-0014 — 단일 docker-compose.yml 로 6 Plane + 인프라 기동 + 헬스 검증.
#
# 플레인 간 통신은 compose 네트워크 hostname 기반이며, 외부 진입은 edge-plane(8080) 만 노출한다.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_ARGS=(--profile full)

PLANES=(
  api-plane
  realtime-plane
  worker-plane
  scheduler-plane
  edge-plane
  extension-plane
)

echo "[1/5] compose 설정 검증"
docker compose "${COMPOSE_ARGS[@]}" config --services >/dev/null

echo "[2/5] 6 Plane + web + edge-router + 인프라 기동"
docker compose "${COMPOSE_ARGS[@]}" up -d --build

echo "[3/5] infra healthy 대기 (NATS 8222 기준)"
for _ in $(seq 1 30); do
  if docker compose exec -T nats wget -q --spider http://localhost:8222/healthz >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "[4/5] NATS 스트림 초기화 + 시드"
./scripts/dev/init-nats-streams.sh
./scripts/dev/seed-data.sh

echo "[5/5] Plane /health 전수 확인 (컨테이너 내부)"
for plane in "${PLANES[@]}"; do
  ok="false"
  for _ in $(seq 1 60); do
    code=$(docker compose exec -T "$plane" \
      python -c 'import urllib.request,sys; sys.exit(0 if urllib.request.urlopen("http://localhost:8000/health",timeout=2).status==200 else 1)' 2>/dev/null \
      && echo 200 || echo 000)
    if [[ "$code" == "200" ]]; then
      echo "  ✓ ${plane}"
      ok="true"
      break
    fi
    sleep 2
  done
  if [[ "$ok" != "true" ]]; then
    echo "  ✗ ${plane}"
    docker compose logs --tail=100 "$plane"
    exit 1
  fi
done

echo ""
echo "외부 진입: http://127.0.0.1:8080/  (edge-router → edge-plane/web)"
echo "기본 계정: demo / ${ONEERP_DEV_ADMIN_PASSWORD:-demo1234}"
