#!/usr/bin/env bash
#
# plane 컨테이너 이미지 빌드 SoT (ADR-0010 §2.1, CLAUDE.md 전역 규칙).
#
# 규약:
# - `docker buildx` + `masblue-builder` 빌더 사용 (CLAUDE.md).
# - `--platform linux/amd64` 단일 아키텍처 고정. 멀티아키 금지.
# - 6개 plane (api/edge/extension/realtime/scheduler/worker) 전수 빌드.
#
# 사용:
#   ./scripts/build/build-planes.sh                # 전체 plane 빌드
#   ./scripts/build/build-planes.sh api_plane      # 단일 plane
#   TAG=v1.0.0 ./scripts/build/build-planes.sh     # 커스텀 태그
#   PUSH=1 ./scripts/build/build-planes.sh         # 빌드 후 registry push
#
# 검증: scripts/ci/check_buildx_compliance.py (정적 검사).

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PLANES=(api_plane edge_plane extension_plane realtime_plane scheduler_plane worker_plane)
REGISTRY="${REGISTRY:-ghcr.io/oneerp}"
TAG="${TAG:-dev}"
BUILDER="${BUILDER:-masblue-builder}"
PLATFORM="linux/amd64"

# 단일 plane 지정 시 해당 plane만 빌드
if [[ $# -gt 0 ]]; then
  PLANES=("$@")
fi

# masblue-builder 활성화 (없으면 기본 빌더 사용)
if docker buildx inspect "$BUILDER" >/dev/null 2>&1; then
  docker buildx use "$BUILDER"
fi

for plane in "${PLANES[@]}"; do
  dockerfile="planes/${plane}/Dockerfile"
  if [[ ! -f "$dockerfile" ]]; then
    echo "ERROR: $dockerfile 없음" >&2
    exit 1
  fi
  image="${REGISTRY}/${plane}:${TAG}"
  push_flag=""
  if [[ "${PUSH:-0}" == "1" ]]; then
    push_flag="--push"
  else
    push_flag="--load"
  fi
  echo "=== build $image ==="
  docker buildx build \
    --platform "$PLATFORM" \
    -f "$dockerfile" \
    -t "$image" \
    $push_flag \
    .
done

echo "=== 완료: ${#PLANES[@]} plane 이미지 빌드 ==="
