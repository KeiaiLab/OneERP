"""API Plane 진입점 (P1, ADR-0014).

실행:
    uv run --package oneerp-plane-api --directory planes/api_plane \\
        uvicorn plane_api.main:app --port 8100

ERP 동기 CRUD 도메인을 단일 uvicorn 프로세스에 다중 마운트한다.
M3 완료 후 전 도메인 리네임 완료 상태. 도메인 추가/제거는 _MOUNTS 편집만.
"""

from __future__ import annotations

from pathlib import Path

from plane_shared import DomainMount, build_plane_app

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _mount(name: str, *parts: str) -> DomainMount:
    return DomainMount(name=name, service_root=_REPO_ROOT.joinpath("services", *parts))


# ERP 트랜잭션 도메인 (25개) — DocStatus + Outbox 패턴의 sync CRUD.
# Realtime / Scheduler / Adapter 는 별도 plane 에서 담당.
_MOUNTS: list[DomainMount] = [
    # Sales
    _mount("selling", "sales", "selling"),
    _mount("crm", "sales", "crm"),
    _mount("pos", "sales", "pos"),
    _mount("commerce", "sales", "commerce"),
    _mount("reservation", "sales", "reservation"),
    # SCM
    _mount("buying", "scm", "buying"),
    _mount("stock", "scm", "stock"),
    _mount("manufacturing", "scm", "manufacturing"),
    _mount("qm", "scm", "qm"),
    # Finance
    _mount("accounting", "finance", "accounting"),
    _mount("expenses", "finance", "expenses"),
    _mount("payroll", "finance", "payroll"),
    _mount("finance-extra", "finance", "finance_extra"),
    # HR
    _mount("hr", "hr", "hr"),
    _mount("learning", "hr", "learning"),
    # Assets
    _mount("plm", "assets", "plm"),
    _mount("assets", "assets", "assets"),
    # Compliance / EHS
    _mount("compliance", "compliance", "compliance"),
    _mount("ehs", "ehs", "ehs"),
    # Logistics
    _mount("logistics", "logistics", "logistics"),
    _mount("advanced-planning", "logistics", "advanced-planning"),
    # Platform (ADR-0014: 동기 HTTP 특성이 api plane에 부합)
    _mount("analytics", "platform", "analytics"),
    _mount("rpa", "platform", "rpa"),
]

app = build_plane_app(plane_name="api", mounts=_MOUNTS)
