"""연결결산 커스텀 라우터 — 기간 관리, 투자 관계, 소거, 환산 API.

비즈니스 서비스를 호출하는 엔드포인트를 제공한다.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from oneerp_core.deps import CurrentUserDep

from ..services.elimination_service import EliminationService
from ..services.investment_service import InvestmentService
from ..services.period_service import PeriodService

router = APIRouter(prefix="/api/v1/consolidation", tags=["연결결산"])


# ──────────────────────────────────────────────
# 지분 구조
# ──────────────────────────────────────────────


@router.get("/ownership-tree")
def get_ownership_tree(user: CurrentUserDep) -> dict[str, Any]:
    """지분 구조 트리를 조회한다."""
    svc = InvestmentService(user.tenant_id)
    tree = svc.get_ownership_tree()
    return {"tree": tree}


# ──────────────────────────────────────────────
# 기간 관리
# ──────────────────────────────────────────────


@router.post("/periods/{period_id}/open")
def open_period(period_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """연결 기간을 개시한다 (not_started → open)."""
    svc = PeriodService(user.tenant_id)
    return svc.open_period(period_id, user_id=user.sub)


@router.post("/periods/{period_id}/close")
def close_period(period_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """연결 기간을 마감한다 (review → closed)."""
    svc = PeriodService(user.tenant_id)
    return svc.close_period(period_id, user_id=user.sub)


@router.post("/periods/{period_id}/reopen")
def reopen_period(period_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """연결 기간을 재개한다 (closed → reopened)."""
    svc = PeriodService(user.tenant_id)
    return svc.reopen_period(period_id, user_id=user.sub)


# ──────────────────────────────────────────────
# 소거
# ──────────────────────────────────────────────


@router.post("/periods/{period_id}/eliminate")
def execute_elimination(period_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """소거를 실행한다."""
    svc = EliminationService(user.tenant_id)
    return svc.execute_elimination(period_id)
