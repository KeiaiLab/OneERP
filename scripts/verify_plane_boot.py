"""Plane 부팅 스모크 — ADR-0014 M1 검증.

선택한 plane이 로드되고 서브앱 마운트와 헬스체크가 응답하는지 확인한다.

사용:
    uv run --package oneerp-plane-api --directory planes/api_plane \\
        python ../../scripts/verify_plane_boot.py --plane api
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for path in [
    ROOT,
    ROOT / "core",
    ROOT / "planes" / "_shared",
    ROOT / "planes" / "api_plane",
    ROOT / "planes" / "realtime_plane",
    ROOT / "planes" / "worker_plane",
    ROOT / "planes" / "scheduler_plane",
    ROOT / "planes" / "edge_plane",
    ROOT / "planes" / "extension_plane",
]:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from scripts.deploy.catalog import load_plane_catalog  # noqa: E402

_PLANE_MODULES: dict[str, str] = {
    "api": "plane_api.main",
    "realtime": "plane_realtime.main",
    "worker": "plane_worker.main",
    "scheduler": "plane_scheduler.main",
    "edge": "plane_edge.main",
    "extension": "plane_extension.main",
}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plane 부팅 스모크 검증")
    parser.add_argument("--plane", choices=sorted(_PLANE_MODULES), default="api")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    plane_catalog = load_plane_catalog(ROOT)
    if args.plane not in plane_catalog:
        print(f"FAIL: plane 카탈로그에 없음: {args.plane}", file=sys.stderr)
        return 1

    from fastapi.testclient import TestClient

    module = importlib.import_module(_PLANE_MODULES[args.plane])
    app = module.app
    mounts = getattr(module, "_MOUNTS", [])
    mount_names = [m.name for m in mounts]
    routes = [r.path for r in app.routes]
    missing = [m for m in mount_names if not any(r.startswith(f"/{m}") for r in routes)]
    if missing:
        print(f"FAIL: 마운트 미발견: {missing}", file=sys.stderr)
        return 1

    client = TestClient(app)
    health_path = plane_catalog[args.plane].health_path
    resp = client.get(health_path)
    if resp.status_code != 200:
        print(f"FAIL: plane {health_path} = {resp.status_code}", file=sys.stderr)
        return 1

    fail_health = []
    for m in mount_names:
        resp = client.get(f"/{m}/health")
        if resp.status_code != 200:
            fail_health.append((m, resp.status_code))

    if fail_health:
        print(f"FAIL: health 실패 도메인: {fail_health}", file=sys.stderr)
        return 1

    print(f"OK plane={args.plane} mounts={len(mount_names)}개 모두 health=pass")
    print(f"  domains: {mount_names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
