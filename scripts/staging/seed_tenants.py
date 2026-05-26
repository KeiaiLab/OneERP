"""staging DB에 3 테넌트 + 기본 GL 계정 시드."""

from __future__ import annotations

from typing import Any

_GL_DEFAULTS: list[dict[str, str]] = [
    {"code": "1000", "name": "현금"},
    {"code": "1100", "name": "보통예금"},
    {"code": "2000", "name": "매입채무"},
    {"code": "4000", "name": "매출"},
    {"code": "5000", "name": "매입원가"},
    {"code": "6000", "name": "판관비"},
]


def build_tenants() -> list[dict[str, Any]]:
    """staging 용 3 테넌트 + 기본 GL 계정 목록 반환."""
    return [
        {
            "id": f"stg-{i}",
            "name": f"Staging Tenant {i}",
            "gl_accounts": list(_GL_DEFAULTS),
        }
        for i in (1, 2, 3)
    ]


def main() -> None:
    """CLI 엔트리 — JSON 으로 테넌트 시드 목록 출력."""
    import json
    import sys

    json.dump(build_tenants(), sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
