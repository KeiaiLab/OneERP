"""예약 정책(ReservationPolicy) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.reservation_policy import (
    ReservationPolicy,
    ReservationPolicyCreate,
    ReservationPolicyUpdate,
)

router = APIRouter(prefix="/api/v1/reservation-policies", tags=["예약정책"])
_COLLECTION = "reservation_policies"
_PREFIX = "RPL"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "/",
    status_code=201,
    dependencies=[Depends(require_permission("reservation_policy:create"))],
)
async def create_policy(body: ReservationPolicyCreate) -> dict:
    """예약 정책을 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = ReservationPolicy(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"id": doc_id, "message": "예약 정책이 생성되었습니다"}


@router.get(
    "/",
    dependencies=[Depends(require_permission("reservation_policy:read"))],
)
async def list_policies(page: int = 1, page_size: int = 20) -> dict:
    """예약 정책 목록을 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get(
    "/{doc_id}",
    dependencies=[Depends(require_permission("reservation_policy:read"))],
)
async def get_policy(doc_id: str) -> dict:
    """예약 정책 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404,
            error="not_found",
            detail="예약 정책을 찾을 수 없습니다",
        )
    return doc


@router.put(
    "/{doc_id}",
    dependencies=[Depends(require_permission("reservation_policy:write"))],
)
async def update_policy(doc_id: str, body: ReservationPolicyUpdate) -> dict:
    """예약 정책을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404,
            error="not_found",
            detail="예약 정책을 찾을 수 없습니다",
        )
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "예약 정책이 수정되었습니다"}
