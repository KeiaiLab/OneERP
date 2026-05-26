"""예약(Reservation) CRUD + 체크인/체크아웃 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.reservation import ReservationCreate, ReservationUpdate
from ..services.reservation_service import ReservationService

router = APIRouter(prefix="/api/v1/reservations", tags=["예약"])
_COLLECTION = "reservations"
_PREFIX = "RSV"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "/",
    status_code=201,
    dependencies=[Depends(require_permission("reservation:create"))],
)
async def create_reservation(body: ReservationCreate) -> dict:
    """예약을 생성한다.

    BR-RSV-003 ~ BR-RSV-009 규칙 적용.
    """
    svc = ReservationService(tenant_id="default")
    return svc.create_reservation(body)


@router.get(
    "/",
    dependencies=[Depends(require_permission("reservation:read"))],
)
async def list_reservations(page: int = 1, page_size: int = 20) -> dict:
    """예약 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get(
    "/{doc_id}",
    dependencies=[Depends(require_permission("reservation:read"))],
)
async def get_reservation(doc_id: str) -> dict:
    """예약 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404,
            error="ERR-RSV-005",
            detail="예약을 찾을 수 없습니다",
        )
    return doc


@router.put(
    "/{doc_id}",
    dependencies=[Depends(require_permission("reservation:write"))],
)
async def update_reservation(doc_id: str, body: ReservationUpdate) -> dict:
    """예약을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404,
            error="ERR-RSV-005",
            detail="예약을 찾을 수 없습니다",
        )
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "예약이 수정되었습니다"}


@router.post(
    "/{doc_id}/cancel",
    dependencies=[Depends(require_permission("reservation:cancel"))],
)
async def cancel_reservation(doc_id: str) -> dict:
    """예약을 취소한다.

    BR-RSV-005, BR-RSV-010 규칙 적용.
    """
    svc = ReservationService(tenant_id="default")
    return svc.cancel_reservation(doc_id)


@router.post(
    "/{doc_id}/check-in",
    dependencies=[Depends(require_permission("reservation:write"))],
)
async def check_in(doc_id: str) -> dict:
    """예약 체크인을 처리한다."""
    svc = ReservationService(tenant_id="default")
    return svc.check_in(doc_id)


@router.post(
    "/{doc_id}/check-out",
    dependencies=[Depends(require_permission("reservation:write"))],
)
async def check_out(doc_id: str) -> dict:
    """예약 체크아웃(완료)을 처리한다."""
    svc = ReservationService(tenant_id="default")
    return svc.check_out(doc_id)


@router.get(
    "/resource/{resource_id}/availability",
    dependencies=[Depends(require_permission("reservation:read"))],
)
async def get_availability(resource_id: str, date: str) -> dict:
    """특정 자원의 특정 날짜 가용성을 조회한다."""
    svc = ReservationService(tenant_id="default")
    return svc.get_resource_availability(resource_id, date)


@router.post(
    "/release-no-shows",
    dependencies=[Depends(require_permission("reservation:write"))],
)
async def release_no_shows() -> dict:
    """미체크인 예약을 자동 해제한다."""
    svc = ReservationService(tenant_id="default")
    return svc.release_no_shows()
