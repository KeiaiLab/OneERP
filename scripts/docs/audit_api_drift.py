#!/usr/bin/env python3
"""docs/api/**/*.md 와 plane OpenAPI schema 차이 검출 체커 (S3).

spec: docs/superpowers/specs/2026-04-13-docs-health-audit-design.md §3.3

알고리즘:
1. 대상 plane 을 in-process import 하여 OpenAPI schema 수집 (extract_code_endpoints).
   import 실패 시 WARNING + skip.
2. docs/api/**/*.md 를 정규식으로 파싱하여 endpoint 추출 (parse_doc_endpoints).
3. compare_endpoints(code_endpoints, doc_paths) 로 diff 계산:
   - [doc-orphan] docs 에만 존재하는 endpoint.
   - [doc-missing] 코드에만 존재하는 endpoint.
   - [doc-skew] 경로+메서드 일치하나 필드 집합 차이.
4. --report 옵션으로 docs/generated/api-drift-report.md 저장.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

# 로거 설정
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("audit_api_drift")

# docs/api 마크다운 파싱 정규식
HTTP_LINE_RE = re.compile(r"^(GET|POST|PUT|DELETE|PATCH)\s+(\S+)", re.MULTILINE)
FIELD_RE = re.compile(r"^-\s+`(\w+)`", re.MULTILINE)

# in-process import 시 필요한 dummy 환경변수
_DUMMY_ENV: dict[str, str] = {
    "ONEERP_JWT_SECRET": "x" * 32,
    "ONEERP_DEBUG": "true",
    "ONEERP_FERRETDB_URI": "mongodb://localhost:27017",
    "ONEERP_NATS_URL": "nats://localhost:4222",
    "ONEERP_VALKEY_URL": "redis://localhost:6379/0",
}

# 수집 대상 plane 모듈 경로 (모듈명, import 경로)
_PLANES: list[tuple[str, str]] = [
    ("api_plane", "plane_api.main"),
    ("edge_plane", "plane_edge.main"),
    ("realtime_plane", "plane_realtime.main"),
    ("scheduler_plane", "plane_scheduler.main"),
    ("extension_plane", "plane_extension.main"),
    ("worker_plane", "plane_worker.main"),
]


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------


def _inject_dummy_env() -> None:
    """dummy 환경변수 주입 — CoreSettings 초기화 실패 방지."""
    for key, val in _DUMMY_ENV.items():
        os.environ.setdefault(key, val)


def _add_plane_to_path(plane_name: str) -> None:
    """plane 패키지 경로를 sys.path 에 추가한다."""
    plane_dir = ROOT / "planes" / plane_name
    src_dir = str(plane_dir)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)


def _extract_openapi_endpoints(app: Any) -> dict[tuple[str, str], dict[str, set[str]]]:
    """FastAPI app 의 openapi() schema 에서 endpoint → 필드 집합 추출."""
    try:
        schema = app.openapi()
    except Exception as exc:
        logger.warning("openapi() 호출 실패: %s", exc)
        return {}

    endpoints: dict[tuple[str, str], dict[str, set[str]]] = {}
    paths = schema.get("paths", {})
    for path, methods in paths.items():
        for method, operation in methods.items():
            if method.upper() not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                continue
            key = (method.upper(), path)
            req_fields: set[str] = set()
            resp_fields: set[str] = set()

            # 요청 body 필드 추출
            req_body = operation.get("requestBody", {})
            content = req_body.get("content", {})
            for media in content.values():
                schema_ref = media.get("schema", {})
                props = schema_ref.get("properties", {})
                req_fields.update(props.keys())

            # 응답 필드 추출 (200 응답)
            responses = operation.get("responses", {})
            resp_200 = responses.get("200", {})
            resp_content = resp_200.get("content", {})
            for media in resp_content.values():
                schema_ref = media.get("schema", {})
                props = schema_ref.get("properties", {})
                resp_fields.update(props.keys())

            endpoints[key] = {"request_fields": req_fields, "response_fields": resp_fields}

    return endpoints


# ---------------------------------------------------------------------------
# 공개 함수 (단위 테스트에서 직접 호출)
# ---------------------------------------------------------------------------


def parse_doc_endpoints(doc_paths: list[Path]) -> dict[tuple[str, str], set[str]]:
    """docs/api/**/*.md 에서 endpoint → 필드 집합 파싱.

    반환: {(METHOD, path): fields_set}
    """
    result: dict[tuple[str, str], set[str]] = {}

    for doc_path in doc_paths:
        try:
            text = doc_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("파일 읽기 실패 %s: %s", doc_path, exc)
            continue

        # HTTP 라인 위치를 순서대로 수집
        http_matches = list(HTTP_LINE_RE.finditer(text))
        for i, m in enumerate(http_matches):
            method = m.group(1)
            path = m.group(2)
            key = (method, path)

            # 다음 HTTP 라인 전까지의 텍스트에서 필드 추출
            start = m.end()
            end = http_matches[i + 1].start() if i + 1 < len(http_matches) else len(text)
            section = text[start:end]
            fields = set(FIELD_RE.findall(section))
            result[key] = fields

    return result


def compare_endpoints(
    code_endpoints: dict[tuple[str, str], dict[str, set[str]]],
    doc_paths: list[Path],
) -> dict[str, list[tuple[str, str]]]:
    """code_endpoints 와 doc_paths 파싱 결과를 비교하여 diff 반환.

    반환:
        {
            "orphans": [(method, path), ...],   # docs 에만 존재
            "missing": [(method, path), ...],   # 코드에만 존재
            "skew": [(method, path), ...],      # 양측 모두 존재하나 필드 차이
        }
    """
    doc_endpoints = parse_doc_endpoints(doc_paths)

    code_keys = set(code_endpoints.keys())
    doc_keys = set(doc_endpoints.keys())

    orphans = sorted(doc_keys - code_keys)
    missing = sorted(code_keys - doc_keys)

    # 양측 교집합에서 필드 차이 검사
    skew: list[tuple[str, str]] = []
    for key in sorted(code_keys & doc_keys):
        code_all_fields = code_endpoints[key].get("request_fields", set()) | code_endpoints[
            key
        ].get("response_fields", set())
        doc_fields = doc_endpoints[key]
        if code_all_fields != doc_fields:
            skew.append(key)

    return {"orphans": list(orphans), "missing": list(missing), "skew": skew}


def extract_code_endpoints(root: Path | None = None) -> dict[tuple[str, str], dict[str, set[str]]]:
    """plane in-process import 로 전체 code endpoint 수집.

    import 실패 plane 은 WARNING + skip.
    단위 테스트에서는 이 함수를 호출하지 않는다(통합용).
    """
    _inject_dummy_env()
    all_endpoints: dict[tuple[str, str], dict[str, set[str]]] = {}
    _ = root  # 통합 테스트 확장 시 사용 예정

    for plane_name, module_path in _PLANES:
        _add_plane_to_path(plane_name)
        try:
            import importlib

            mod = importlib.import_module(module_path)
            app = getattr(mod, "app", None)
            if app is None:
                logger.warning("[%s] app 객체 없음 — skip", plane_name)
                continue
            endpoints = _extract_openapi_endpoints(app)
            all_endpoints.update(endpoints)
            logger.info("[%s] %d 엔드포인트 수집", plane_name, len(endpoints))
        except Exception as exc:
            logger.warning("[%s] import 실패 — skip: %s", plane_name, exc)

    return all_endpoints


# ---------------------------------------------------------------------------
# 보고서 생성
# ---------------------------------------------------------------------------


def _format_report(
    result: dict[str, list[tuple[str, str]]],
    code_count: int,
    doc_count: int,
) -> str:
    """diff 결과를 마크다운 보고서 문자열로 포맷."""
    lines: list[str] = [
        "# API Drift Report",
        "",
        f"- 코드 endpoint 수: {code_count}",
        f"- docs endpoint 수: {doc_count}",
        "",
        "> **수동 검토 필요**: 마크다운 파싱이 heuristic 이므로 false positive 가 있을 수 있습니다.",
        "",
    ]

    orphans = result["orphans"]
    missing = result["missing"]
    skew = result["skew"]

    lines += [
        f"## [doc-orphan] docs 에만 존재 ({len(orphans)}건)",
        "",
    ]
    for method, path in orphans:
        lines.append(f"- `{method} {path}`")
    lines.append("")

    lines += [
        f"## [doc-missing] 코드에만 존재 ({len(missing)}건)",
        "",
    ]
    for method, path in missing:
        lines.append(f"- `{method} {path}`")
    lines.append("")

    lines += [
        f"## [doc-skew] 필드 차이 ({len(skew)}건)",
        "",
    ]
    for method, path in skew:
        lines.append(f"- `{method} {path}`")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 메인 엔트리포인트
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """메인 엔트리포인트.

    --report 옵션: docs/generated/api-drift-report.md 저장.
    """
    parser = argparse.ArgumentParser(description="API drift 체커 (S3)")
    parser.add_argument(
        "--report", action="store_true", help="docs/generated/api-drift-report.md 저장"
    )
    parser.add_argument("--json", action="store_true", help="구조화 JSON 출력 (후속 CI 용)")
    args = parser.parse_args(argv)

    # 코드 endpoint 수집 (plane in-process import)
    logger.info("plane in-process import 시작...")
    code_endpoints = extract_code_endpoints()
    logger.info("총 code endpoint 수: %d", len(code_endpoints))

    # docs/api/**/*.md 수집
    doc_paths = sorted((ROOT / "docs" / "api").glob("**/*.md"))
    logger.info("docs/api 문서 수: %d", len(doc_paths))

    # 비교
    result = compare_endpoints(code_endpoints, doc_paths)

    orphans = result["orphans"]
    missing = result["missing"]
    skew = result["skew"]

    # stdout 요약
    total = len(orphans) + len(missing) + len(skew)
    print(f"[doc-orphan] {len(orphans)}건")
    for method, path in orphans:
        print(f"  {method} {path}")
    print(f"[doc-missing] {len(missing)}건")
    for method, path in missing:
        print(f"  {method} {path}")
    print(f"[doc-skew] {len(skew)}건")
    for method, path in skew:
        print(f"  {method} {path}")
    print(
        f"\n총 drift {total}건 감지 (orphan {len(orphans)}, missing {len(missing)}, skew {len(skew)})"
    )

    if args.report:
        report_dir = ROOT / "docs" / "generated"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "api-drift-report.md"
        report_text = _format_report(result, len(code_endpoints), len(doc_paths))
        report_path.write_text(report_text, encoding="utf-8")
        logger.info("보고서 저장: %s", report_path)

    if args.json:
        import json as _json

        output = {
            "orphans": [{"method": m, "path": p} for m, p in orphans],
            "missing": [{"method": m, "path": p} for m, p in missing],
            "skew": [{"method": m, "path": p} for m, p in skew],
        }
        print(_json.dumps(output, ensure_ascii=False, indent=2))

    return 1 if total > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
