#!/usr/bin/env python3
"""OpenAPI 스펙 수집기 (ADR-0001 G1-2, ADR-0007 호환).

각 plane 앱에서 도메인별 `/<domain>/openapi.json`을 수집해
`docs/api/<domain>/openapi.json` + `docs/api/<domain>/openapi.yaml`로
발행한다. G1-2 게이트의 증거 파일을 자동 생성.

수집 대상: HTTP 라우트를 노출하는 plane — api, realtime, extension.
(worker/scheduler는 HTTP 라우트 없음, edge는 forwarding-only라 제외)

사용:
    uv run --package oneerp-plane-api python scripts/audit/collect_openapi.py
    uv run --package oneerp-plane-api python scripts/audit/collect_openapi.py --plane api
    uv run --package oneerp-plane-api python scripts/audit/collect_openapi.py --no-yaml
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "docs/api"

# HTTP plane만 대상
HTTP_PLANES = {
    "api": "plane_api.main",
    "realtime": "plane_realtime.main",
    "extension": "plane_extension.main",
    "edge": "plane_edge.main",
}


def ensure_dev_env() -> None:
    """dev JWT 시크릿 자동 주입 (미설정 시)."""
    if not os.environ.get("ONEERP_JWT_SECRET"):
        # 개발 전용 고정 시크릿 — OpenAPI 추출 한정
        os.environ["ONEERP_JWT_SECRET"] = "x" * 32
    os.environ.setdefault("ONEERP_DEBUG", "true")


def load_plane_mounts(plane: str) -> tuple[Any, list[Any]]:
    module_path = HTTP_PLANES[plane]
    mod = importlib.import_module(module_path)
    mounts = getattr(mod, "_MOUNTS", [])
    app = getattr(mod, "app", None)
    if app is None:
        raise SystemExit(f"plane {plane}: app not found")
    return app, mounts


def collect_from_plane(plane: str, *, write_yaml: bool = True) -> list[dict]:
    """plane에서 모든 도메인의 openapi.json 수집."""
    from fastapi.testclient import TestClient

    app, mounts = load_plane_mounts(plane)
    client = TestClient(app)
    results: list[dict[str, Any]] = []
    for m in mounts:
        domain = m.name
        try:
            r = client.get(f"/{domain}/openapi.json")
        except Exception as e:
            results.append(
                {
                    "plane": plane,
                    "domain": domain,
                    "status": "fail",
                    "code": type(e).__name__,
                    "error": str(e)[:120],
                }
            )
            continue
        if r.status_code != 200:
            results.append(
                {"plane": plane, "domain": domain, "status": "fail", "code": r.status_code}
            )
            continue
        spec = r.json()
        dom_dir = OUT_DIR / domain
        dom_dir.mkdir(parents=True, exist_ok=True)
        # JSON 발행
        (dom_dir / "openapi.json").write_text(
            json.dumps(spec, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        # YAML도 발행 (옵션)
        if write_yaml:
            try:
                import yaml

                (dom_dir / "openapi.yaml").write_text(
                    yaml.safe_dump(spec, sort_keys=True, allow_unicode=True),
                    encoding="utf-8",
                )
            except ImportError:
                pass
        paths = len(spec.get("paths", {}))
        results.append(
            {
                "plane": plane,
                "domain": domain,
                "status": "ok",
                "paths": paths,
                "file": str((dom_dir / "openapi.json").relative_to(REPO)),
            }
        )
    return results


def render_index(all_results: list[dict]) -> str:
    ok = [r for r in all_results if r["status"] == "ok"]
    failed = [r for r in all_results if r["status"] != "ok"]
    lines = [
        "# API 스펙 인덱스 (자동 생성)",
        "",
        "> 근거: ADR-0001 G1-2 + ADR-0007.",
        "> 생성: `scripts/audit/collect_openapi.py`.",
        f"> 총 {len(ok)} 도메인 발행, {len(failed)} 실패.",
        "",
        "## 도메인별 스펙",
        "",
        "| Plane | Domain | Paths | 파일 |",
        "|-------|--------|-------|------|",
    ]
    lines.extend(
        f"| {r['plane']} | {r['domain']} | {r['paths']} | [{r['file']}](../../{r['file']}) |"
        for r in sorted(ok, key=lambda x: (x["plane"], x["domain"]))
    )
    if failed:
        lines.extend(["", "## 실패", ""])
        lines.extend(f"- {r['plane']}/{r['domain']}: HTTP {r.get('code', '?')}" for r in failed)
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description="OpenAPI 수집기 (ADR-0001 G1-2)")
    p.add_argument("--plane", choices=list(HTTP_PLANES), help="단일 plane만")
    p.add_argument("--no-yaml", action="store_true", help="YAML 산출물 생략")
    p.add_argument("--no-index", action="store_true", help="인덱스 파일 생성 생략")
    args = p.parse_args()

    ensure_dev_env()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    planes = [args.plane] if args.plane else list(HTTP_PLANES)
    all_results: list[dict] = []
    for plane in planes:
        try:
            all_results.extend(collect_from_plane(plane, write_yaml=not args.no_yaml))
            print(
                f"[ok] {plane}: {sum(1 for r in all_results if r['plane'] == plane and r['status'] == 'ok')} domains"
            )
        except Exception as e:
            print(f"[FAIL] {plane}: {e}", file=sys.stderr)
            return 2

    ok_count = sum(1 for r in all_results if r["status"] == "ok")
    fail_count = len(all_results) - ok_count

    if not args.no_index:
        index_path = OUT_DIR / "INDEX.md"
        index_path.write_text(render_index(all_results), encoding="utf-8")
        print(f"[index] wrote {index_path.relative_to(REPO)}")

    print()
    print(f"Total: {ok_count} OK, {fail_count} failed")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
