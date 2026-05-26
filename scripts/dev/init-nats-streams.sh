#!/usr/bin/env bash
# scripts/dev/init-nats-streams.sh
# NATS JetStream 스트림 초기화 — docker compose 기동 후 실행.
#
# ADR-0014 compose 통합 이후 NATS 는 host port 를 노출하지 않으므로, 초기화
# 스크립트는 compose 네트워크 내부 plane 컨테이너(api-plane)를 경유해 실행한다.
# (api-plane 이미지에 nats-py 가 이미 설치되어 있음.)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

NATS_URL="${NATS_URL:-nats://nats:4222}"
EXEC_SERVICE="${EXEC_SERVICE:-worker-plane}"

echo "NATS 스트림 초기화 중... (via ${EXEC_SERVICE} → ${NATS_URL})"

docker compose exec -T -e "NATS_URL=${NATS_URL}" "${EXEC_SERVICE}" python - <<'PY'
from __future__ import annotations

import asyncio
import os

import nats
from nats.js.api import StorageType, StreamConfig


async def ensure_stream(js, config: StreamConfig) -> None:
    try:
        await js.add_stream(config)
        print(f"  생성: {config.name}")
    except Exception:
        await js.stream_info(config.name)
        print(f"  재사용: {config.name}")


async def main() -> None:
    nc = await nats.connect(os.environ["NATS_URL"])
    js = nc.jetstream()
    await ensure_stream(
        js,
        StreamConfig(
            name="ONEERP",
            subjects=["oneerp.>"],
            storage=StorageType.FILE,
        ),
    )
    await nc.close()


asyncio.run(main())
PY

echo "NATS 스트림 초기화 완료"
