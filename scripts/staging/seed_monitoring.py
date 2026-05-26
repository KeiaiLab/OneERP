"""Prometheus 30d 시뮬레이션 샘플 — G2-1 SLO partial 증거."""

from __future__ import annotations

from typing import Any


def build_slo_series(days: int = 30) -> list[dict[str, Any]]:
    """주기적 패턴을 가진 SLO 시계열(p95/error_rate/availability) 생성."""
    return [
        {
            "day": d + 1,
            "p95_ms": 95 + (d % 7) * 2,
            "error_rate": 0.0004 + (d % 3) * 0.0001,
            "availability": 0.9995 - (d % 5) * 0.0001,
        }
        for d in range(days)
    ]


def main() -> None:
    """CLI 엔트리 — 30일 SLO 시계열 JSON 출력."""
    import json
    import sys

    json.dump(build_slo_series(), sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
